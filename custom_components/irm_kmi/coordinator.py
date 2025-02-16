"""DataUpdateCoordinator for the IRM KMI integration."""
import logging
from datetime import datetime, timedelta
from statistics import mean
from typing import List
import urllib.parse

import async_timeout
from homeassistant.components.weather import Forecast
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator, UpdateFailed)
from homeassistant.util import dt
from homeassistant.util.dt import utcnow

from .api import IrmKmiApiClient, IrmKmiApiError
from .const import CONF_DARK_MODE, CONF_STYLE, DOMAIN, IRM_KMI_NAME
from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .const import MAP_WARNING_ID_TO_SLUG as SLUG_MAP
from .const import (OPTION_STYLE_SATELLITE, OUT_OF_BENELUX, STYLE_TO_PARAM_MAP,
                    WEEKDAYS)
from .data import (CurrentWeatherData, IrmKmiForecast,
                   ProcessedCoordinatorData,
                   WarningData)
from .radar_data import IrmKmiRadarForecast, AnimationFrameData, RadarAnimationData
from .pollen import PollenParser
from .rain_graph import RainGraph
from .utils import (disable_from_config, get_config_value, next_weekday,
                    preferred_language)

_LOGGER = logging.getLogger(__name__)


class IrmKmiCoordinator(TimestampDataUpdateCoordinator):
    """Coordinator to update data from IRM KMI"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            # Name of the data. For logging purposes.
            name="IRM KMI weather",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=7),
        )
        self._api_client = IrmKmiApiClient(session=async_get_clientsession(hass))
        self._zone = get_config_value(entry, CONF_ZONE)
        self._dark_mode = get_config_value(entry, CONF_DARK_MODE)
        self._style = get_config_value(entry, CONF_STYLE)
        self.shared_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=IRM_KMI_NAME.get(preferred_language(self.hass, self.config_entry)),
            name=f"{entry.title}"
        )

    async def _async_update_data(self) -> ProcessedCoordinatorData:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        self._api_client.expire_cache()
        if (zone := self.hass.states.get(self._zone)) is None:
            raise UpdateFailed(f"Zone '{self._zone}' not found")
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(60):
                api_data = await self._api_client.get_forecasts_coord(
                    {'lat': zone.attributes[ATTR_LATITUDE],
                     'long': zone.attributes[ATTR_LONGITUDE]}
                )
                _LOGGER.debug(f"Observation for {api_data.get('cityName', '')}: {api_data.get('obs', '{}')}")
                _LOGGER.debug(f"Full data: {api_data}")

        except IrmKmiApiError as err:
            if self.last_update_success_time is not None \
                    and self.last_update_success_time - utcnow() < 2.5 * self.update_interval:
                _LOGGER.warning(f"Error communicating with API for general forecast: {err}. Keeping the old data.")
                return self.data
            else:
                raise UpdateFailed(f"Error communicating with API for general forecast: {err}. "
                                   f"Last success time is: {self.last_update_success_time}")

        if api_data.get('cityName', None) in OUT_OF_BENELUX:
            _LOGGER.error(f"The zone {self._zone} is now out of Benelux and forecast is only available in Benelux. "
                          f"Associated device is now disabled.  Move the zone back in Benelux and re-enable to fix "
                          f"this")
            disable_from_config(self.hass, self.config_entry)

            issue_registry.async_create_issue(
                self.hass,
                DOMAIN,
                "zone_moved",
                is_fixable=True,
                severity=issue_registry.IssueSeverity.ERROR,
                translation_key='zone_moved',
                data={'config_entry_id': self.config_entry.entry_id, 'zone': self._zone},
                translation_placeholders={'zone': self._zone}
            )
            return ProcessedCoordinatorData()

        return await self.process_api_data(api_data)

    async def async_refresh(self) -> None:
        """Refresh data and log errors."""
        await self._async_refresh(log_failures=True, raise_on_entry_error=True)

    async def _async_animation_data(self, api_data: dict) -> RainGraph | None:
        """From the API data passed in, call the API to get all the images and create the radar animation data object.
        Frames from the API are merged with the background map and the location marker to create each frame."""
        animation_data = api_data.get('animation', {}).get('sequence')
        localisation_layer_url = api_data.get('animation', {}).get('localisationLayer')
        country = api_data.get('country', '')

        if animation_data is None or localisation_layer_url is None or not isinstance(animation_data, list):
            return None

        localisation = self.merge_url_and_params(localisation_layer_url,
                                                 {'th': 'd' if country == 'NL' or not self._dark_mode else 'n'})
        images_from_api = [self.merge_url_and_params(frame.get('uri'), {'rs': STYLE_TO_PARAM_MAP[self._style]})
            for frame in animation_data if frame is not None and frame.get('uri') is not None
        ]

        lang = preferred_language(self.hass, self.config_entry)
        radar_animation = RadarAnimationData(
            hint=api_data.get('animation', {}).get('sequenceHint', {}).get(lang),
            unit=api_data.get('animation', {}).get('unit', {}).get(lang),
            location=localisation
        )
        rain_graph: RainGraph = await self.create_rain_graph(radar_animation, animation_data, country, images_from_api)
        return rain_graph

    @staticmethod
    def merge_url_and_params(url, params):
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        query_params.update(params)
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        new_url = parsed_url._replace(query=new_query)
        return str(urllib.parse.urlunparse(new_url))

    async def _async_pollen_data(self, api_data: dict) -> dict:
        """Get SVG pollen info from the API, return the pollen data dict"""
        _LOGGER.debug("Getting pollen data from API")
        svg_url = None
        for module in api_data.get('module', []):
            _LOGGER.debug(f"module: {module}")
            if module.get('type', None) == 'svg':
                url = module.get('data', {}).get('url', {}).get('en', '')
                if 'pollen' in url:
                    svg_url = url
                    break
        if svg_url is None:
            return PollenParser.get_default_data()

        try:
            _LOGGER.debug(f"Requesting pollen SVG at url {svg_url}")
            pollen_svg: str = await self._api_client.get_svg(svg_url)
        except IrmKmiApiError as err:
            _LOGGER.warning(f"Could not get pollen data from the API: {err}. Keeping the same data.")
            return self.data.get('pollen', PollenParser.get_unavailable_data()) \
                if self.data is not None else PollenParser.get_unavailable_data()

        return PollenParser(pollen_svg).get_pollen_data()

    async def process_api_data(self, api_data: dict) -> ProcessedCoordinatorData:
        """From the API data, create the object that will be used in the entities"""
        return ProcessedCoordinatorData(
            current_weather=await IrmKmiCoordinator.current_weather_from_data(api_data),
            daily_forecast=await self.daily_list_to_forecast(api_data.get('for', {}).get('daily')),
            hourly_forecast=await IrmKmiCoordinator.hourly_list_to_forecast(api_data.get('for', {}).get('hourly')),
            radar_forecast=IrmKmiCoordinator.radar_list_to_forecast(api_data.get('animation', {})),
            animation=await self._async_animation_data(api_data=api_data),
            warnings=self.warnings_from_data(api_data.get('for', {}).get('warning')),
            pollen=await self._async_pollen_data(api_data=api_data),
            country=api_data.get('country')
        )


    @staticmethod
    async def current_weather_from_data(api_data: dict) -> CurrentWeatherData:
        """Parse the API data to build a CurrentWeatherData."""
        # Process data to get current hour forecast
        now_hourly = None
        hourly_forecast_data = api_data.get('for', {}).get('hourly')
        tz = await dt.async_get_time_zone('Europe/Brussels')
        now = dt.now(time_zone=tz)
        if not (hourly_forecast_data is None
                or not isinstance(hourly_forecast_data, list)
                or len(hourly_forecast_data) == 0):

            for current in hourly_forecast_data[:4]:
                if now.strftime('%H') == current['hour']:
                    now_hourly = current
                    break
        # Get UV index
        module_data = api_data.get('module', None)
        uv_index = None
        if not (module_data is None or not isinstance(module_data, list)):
            for module in module_data:
                if module.get('type', None) == 'uv':
                    uv_index = module.get('data', {}).get('levelValue')

        try:
            pressure = float(now_hourly.get('pressure', None)) if now_hourly is not None else None
        except (TypeError, ValueError):
            pressure = None

        try:
            wind_speed = float(now_hourly.get('windSpeedKm', None)) if now_hourly is not None else None
        except (TypeError, ValueError):
            wind_speed = None

        try:
            wind_gust_speed = float(now_hourly.get('windPeakSpeedKm', None)) if now_hourly is not None else None
        except (TypeError, ValueError):
            wind_gust_speed = None

        try:
            temperature = float(api_data.get('obs', {}).get('temp'))
        except (TypeError, ValueError):
            temperature = None

        try:
            dir_cardinal = now_hourly.get('windDirectionText', {}).get('en') if now_hourly is not None else None
            if dir_cardinal == 'VAR' or now_hourly is None:
                wind_bearing = None
            else:
                wind_bearing = (float(now_hourly.get('windDirection')) + 180) % 360
        except (TypeError, ValueError):
            wind_bearing = None

        current_weather = CurrentWeatherData(
            condition=CDT_MAP.get((api_data.get('obs', {}).get('ww'), api_data.get('obs', {}).get('dayNight')), None),
            temperature=temperature,
            wind_speed=wind_speed,
            wind_gust_speed=wind_gust_speed,
            wind_bearing=wind_bearing,
            pressure=pressure,
            uv_index=uv_index
        )

        if api_data.get('country', '') == 'NL':
            current_weather['wind_speed'] = api_data.get('obs', {}).get('windSpeedKm')
            if api_data.get('obs', {}).get('windDirectionText', {}).get('en') == 'VAR':
                current_weather['wind_bearing'] = None
            else:
                try:
                    current_weather['wind_bearing'] = (float(api_data.get('obs', {}).get('windDirection')) + 180) % 360
                except ValueError:
                    current_weather['wind_bearing'] = None

        # Since June 2024, the NL weather does not include the condition in the 'ww' key, so we get it from the current
        # hourly forecast instead if it is missing
        if current_weather['condition'] is None:
            try:
                current_weather['condition'] = CDT_MAP.get((int(now_hourly.get('ww')), now_hourly.get('dayNight')))
            except (TypeError, ValueError, AttributeError):
                current_weather['condition'] = None

        return current_weather

    @staticmethod
    async def hourly_list_to_forecast(data: List[dict] | None) -> List[Forecast] | None:
        """Parse data from the API to create a list of hourly forecasts"""
        if data is None or not isinstance(data, list) or len(data) == 0:
            return None

        forecasts = list()
        tz = await dt.async_get_time_zone('Europe/Brussels')
        day = dt.now(time_zone=tz).replace(hour=0, minute=0, second=0, microsecond=0)

        for idx, f in enumerate(data):
            if 'dateShow' in f and idx > 0:
                day = day + timedelta(days=1)

            hour = f.get('hour', None)
            if hour is None:
                continue
            day = day.replace(hour=int(hour))

            precipitation_probability = None
            if f.get('precipChance', None) is not None:
                precipitation_probability = int(f.get('precipChance'))

            ww = None
            if f.get('ww', None) is not None:
                ww = int(f.get('ww'))

            wind_bearing = None
            if f.get('windDirectionText', {}).get('en') != 'VAR':
                try:
                    wind_bearing = (float(f.get('windDirection')) + 180) % 360
                except (TypeError, ValueError):
                    pass

            forecast = Forecast(
                datetime=day.isoformat(),
                condition=CDT_MAP.get((ww, f.get('dayNight', None)), None),
                native_precipitation=f.get('precipQuantity', None),
                native_temperature=f.get('temp', None),
                native_templow=None,
                native_wind_gust_speed=f.get('windPeakSpeedKm', None),
                native_wind_speed=f.get('windSpeedKm', None),
                precipitation_probability=precipitation_probability,
                wind_bearing=wind_bearing,
                native_pressure=f.get('pressure', None),
                is_daytime=f.get('dayNight', None) == 'd'
            )

            forecasts.append(forecast)

        return forecasts

    @staticmethod
    def radar_list_to_forecast(data: dict | None) -> List[IrmKmiRadarForecast] | None:
        """Create a list of short term forecasts for rain based on the data provided by the rain radar"""
        if data is None:
            return None
        sequence = data.get("sequence", [])
        ratios = [f['value'] / f['position'] for f in sequence if f['position'] > 0]

        if len(ratios) > 0:
            ratio = mean(ratios)
        else:
            ratio = 0

        forecast = list()
        for f in sequence:
            forecast.append(
                IrmKmiRadarForecast(
                    datetime=f.get("time"),
                    native_precipitation=f.get('value'),
                    rain_forecast_max=round(f.get('positionHigher') * ratio, 2),
                    rain_forecast_min=round(f.get('positionLower') * ratio, 2),
                    might_rain=f.get('positionHigher') > 0
                )
            )
        return forecast

    async def daily_list_to_forecast(self, data: List[dict] | None) -> List[IrmKmiForecast] | None:
        """Parse data from the API to create a list of daily forecasts"""
        if data is None or not isinstance(data, list) or len(data) == 0:
            return None

        forecasts = list()
        lang = preferred_language(self.hass, self.config_entry)
        tz = await dt.async_get_time_zone('Europe/Brussels')
        forecast_day = dt.now(tz)

        for (idx, f) in enumerate(data):
            precipitation = None
            if f.get('precipQuantity', None) is not None:
                try:
                    precipitation = float(f.get('precipQuantity'))
                except (TypeError, ValueError):
                    pass

            native_wind_gust_speed = None
            if f.get('wind', {}).get('peakSpeed') is not None:
                try:
                    native_wind_gust_speed = int(f.get('wind', {}).get('peakSpeed'))
                except (TypeError, ValueError):
                    pass

            wind_bearing = None
            if f.get('wind', {}).get('dirText', {}).get('en') != 'VAR':
                try:
                    wind_bearing = (float(f.get('wind', {}).get('dir')) + 180) % 360
                except (TypeError, ValueError):
                    pass

            is_daytime = f.get('dayNight', None) == 'd'

            day_name = f.get('dayName', {}).get('en', None)
            timestamp = f.get('timestamp', None)
            if timestamp is not None:
                forecast_day = datetime.fromisoformat(timestamp)
            elif day_name in WEEKDAYS:
                forecast_day = next_weekday(forecast_day, WEEKDAYS.index(day_name))
            elif day_name in ['Today', 'Tonight']:
                forecast_day = dt.now(tz)
            elif day_name == 'Tomorrow':
                forecast_day = dt.now(tz) + timedelta(days=1)

            sunrise_sec = f.get('dawnRiseSeconds', None)
            if sunrise_sec is None:
                sunrise_sec = f.get('sunRise', None)
            sunrise = None
            if sunrise_sec is not None:
                try:
                    sunrise = (forecast_day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)
                               + timedelta(seconds=float(sunrise_sec)))
                except (TypeError, ValueError):
                    pass

            sunset_sec = f.get('dawnSetSeconds', None)
            if sunset_sec is None:
                sunset_sec = f.get('sunSet', None)
            sunset = None
            if sunset_sec is not None:
                try:
                    sunset = (forecast_day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)
                              + timedelta(seconds=float(sunset_sec)))
                except (TypeError, ValueError):
                    pass

            forecast = IrmKmiForecast(
                datetime=(forecast_day.strftime('%Y-%m-%d')),
                condition=CDT_MAP.get((f.get('ww1', None), f.get('dayNight', None)), None),
                native_precipitation=precipitation,
                native_temperature=f.get('tempMax', None),
                native_templow=f.get('tempMin', None),
                native_wind_gust_speed=native_wind_gust_speed,
                native_wind_speed=f.get('wind', {}).get('speed'),
                precipitation_probability=f.get('precipChance', None),
                wind_bearing=wind_bearing,
                is_daytime=is_daytime,
                text=f.get('text', {}).get(lang, ""),
                sunrise=sunrise.isoformat() if sunrise is not None else None,
                sunset=sunset.isoformat() if sunset is not None else None
            )
            # Swap temperature and templow if needed
            if (forecast['native_templow'] is not None
                    and forecast['native_temperature'] is not None
                    and forecast['native_templow'] > forecast['native_temperature']):
                (forecast['native_templow'], forecast['native_temperature']) = \
                    (forecast['native_temperature'], forecast['native_templow'])

            forecasts.append(forecast)

        return forecasts

    async def create_rain_graph(self,
                                radar_animation: RadarAnimationData,
                                api_animation_data: List[dict],
                                country: str,
                                images_from_api: list[str],
                                ) -> RainGraph:
        """Create a RainGraph object that is ready to output animated and still SVG images"""
        sequence: List[AnimationFrameData] = list()

        tz = await dt.async_get_time_zone(self.hass.config.time_zone)
        current_time = dt.now(time_zone=tz)
        most_recent_frame = None

        for idx, item in enumerate(api_animation_data):
            frame = AnimationFrameData(
                image=images_from_api[idx],
                time=datetime.fromisoformat(item.get('time')) if item.get('time', None) is not None else None,
                value=item.get('value', 0),
                position=item.get('position', 0),
                position_lower=item.get('positionLower', 0),
                position_higher=item.get('positionHigher', 0)
            )
            sequence.append(frame)

            if most_recent_frame is None and current_time < frame['time']:
                most_recent_frame = idx - 1 if idx > 0 else idx

        radar_animation['sequence'] = sequence
        radar_animation['most_recent_image_idx'] = most_recent_frame

        satellite_mode = self._style == OPTION_STYLE_SATELLITE

        if country == 'NL':
            image_path = "custom_components/irm_kmi/resources/nl.png"
            bg_size = (640, 600)
        else:
            image_path = (f"custom_components/irm_kmi/resources/be_"
                          f"{'satellite' if satellite_mode else 'black' if self._dark_mode else 'white'}.png")
            bg_size = (640, 490)

        return await RainGraph(radar_animation, image_path, bg_size, tz=tz, config_dir=self.hass.config.config_dir,
                               dark_mode=self._dark_mode, api_client=self._api_client).build()

    def warnings_from_data(self, warning_data: list | None) -> List[WarningData]:
        """Create a list of warning data instances based on the api data"""
        if warning_data is None or not isinstance(warning_data, list) or len(warning_data) == 0:
            return []

        lang = preferred_language(self.hass, self.config_entry)
        result = list()
        for data in warning_data:
            try:
                warning_id = int(data.get('warningType', {}).get('id'))
                start = datetime.fromisoformat(data.get('fromTimestamp', None))
                end = datetime.fromisoformat(data.get('toTimestamp', None))
            except (TypeError, ValueError):
                # Without this data, the warning is useless
                continue

            try:
                level = int(data.get('warningLevel'))
            except TypeError:
                level = None

            result.append(
                WarningData(
                    slug=SLUG_MAP.get(warning_id, 'unknown'),
                    id=warning_id,
                    level=level,
                    friendly_name=data.get('warningType', {}).get('name', {}).get(lang, ''),
                    text=data.get('text', {}).get(lang, ''),
                    starts_at=start,
                    ends_at=end
                )
            )

        return result if len(result) > 0 else []
