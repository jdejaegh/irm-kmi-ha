"""DataUpdateCoordinator for the IRM KMI integration."""
import asyncio
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, List, Tuple

import async_timeout
import pytz
from homeassistant.components.weather import Forecast
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)
from PIL import Image, ImageDraw, ImageFont

from .api import IrmKmiApiClient, IrmKmiApiError
from .const import CONF_DARK_MODE, CONF_STYLE, CONF_STYLE_SATELLITE
from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .const import LANGS, OUT_OF_BENELUX, STYLE_TO_PARAM_MAP
from .data import (AnimationFrameData, CurrentWeatherData, IrmKmiForecast,
                   ProcessedCoordinatorData, RadarAnimationData)
from .utils import disable_from_config

_LOGGER = logging.getLogger(__name__)


class IrmKmiCoordinator(DataUpdateCoordinator):
    """Coordinator to update data from IRM KMI"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="IRM KMI weather",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=7),
        )
        self._api_client = IrmKmiApiClient(session=async_get_clientsession(hass))
        self._zone = entry.data.get('zone')
        self._config_entry = entry
        self._disabled = False

    async def _async_update_data(self) -> ProcessedCoordinatorData:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        if (zone := self.hass.states.get(self._zone)) is None:
            raise UpdateFailed(f"Zone '{self._zone}' not found")

        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                api_data = await self._api_client.get_forecasts_coord(
                    {'lat': zone.attributes[ATTR_LATITUDE],
                     'long': zone.attributes[ATTR_LONGITUDE]}
                )
                _LOGGER.debug(f"Observation for {api_data.get('cityName', '')}: {api_data.get('obs', '{}')}")

        except IrmKmiApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

        if api_data.get('cityName', None) in OUT_OF_BENELUX:
            if self.data is None:
                error_text = f"Zone '{self._zone}' is out of Benelux and forecast is only available in the Benelux"
                _LOGGER.error(error_text)
                raise ConfigEntryError(error_text)
            else:
                # TODO create a repair when this triggers
                _LOGGER.error(f"The zone {self._zone} is now out of Benelux and forecast is only available in Benelux."
                              f"Associated device is now disabled.  Move the zone back in Benelux and re-enable to fix "
                              f"this")
                disable_from_config(self.hass, self._config_entry)
                return ProcessedCoordinatorData()

        return await self.process_api_data(api_data)

    async def async_refresh(self) -> None:
        """Refresh data and log errors."""
        await self._async_refresh(log_failures=True, raise_on_entry_error=True)

    async def _async_animation_data(self, api_data: dict) -> RadarAnimationData:
        """From the API data passed in, call the API to get all the images and create the radar animation data object.
        Frames from the API are merged with the background map and the location marker to create each frame."""
        animation_data = api_data.get('animation', {}).get('sequence')
        localisation_layer_url = api_data.get('animation', {}).get('localisationLayer')
        country = api_data.get('country', '')

        if animation_data is None or localisation_layer_url is None or not isinstance(animation_data, list):
            return RadarAnimationData()

        try:
            images_from_api = await self.download_images_from_api(animation_data, country, localisation_layer_url)
        except IrmKmiApiError:
            _LOGGER.warning(f"Could not get images for weather radar")
            return RadarAnimationData()

        localisation = Image.open(BytesIO(images_from_api[0])).convert('RGBA')
        images_from_api = images_from_api[1:]

        radar_animation = await self.merge_frames_from_api(animation_data, country, images_from_api, localisation)

        lang = self.hass.config.language if self.hass.config.language in LANGS else 'en'
        radar_animation['hint'] = api_data.get('animation', {}).get('sequenceHint', {}).get(lang)
        return radar_animation

    async def process_api_data(self, api_data: dict) -> ProcessedCoordinatorData:
        """From the API data, create the object that will be used in the entities"""
        return ProcessedCoordinatorData(
            current_weather=IrmKmiCoordinator.current_weather_from_data(api_data),
            daily_forecast=IrmKmiCoordinator.daily_list_to_forecast(api_data.get('for', {}).get('daily')),
            hourly_forecast=IrmKmiCoordinator.hourly_list_to_forecast(api_data.get('for', {}).get('hourly')),
            animation=await self._async_animation_data(api_data=api_data)
        )

    async def download_images_from_api(self,
                                       animation_data: list,
                                       country: str,
                                       localisation_layer_url: str) -> tuple[Any]:
        """Download a batch of images to create the radar frames."""
        coroutines = list()
        dark_mode = self._config_entry.data[CONF_DARK_MODE]
        style = self._config_entry.data[CONF_STYLE]
        coroutines.append(
            self._api_client.get_image(localisation_layer_url,
                                       params={'th': 'd' if country == 'NL' or not dark_mode else 'n'}))

        for frame in animation_data:
            if frame.get('uri', None) is not None:
                coroutines.append(
                    self._api_client.get_image(frame.get('uri'), params={'rs': STYLE_TO_PARAM_MAP[style]}))
        async with async_timeout.timeout(20):
            images_from_api = await asyncio.gather(*coroutines)

        _LOGGER.debug(f"Just downloaded {len(images_from_api)} images")
        return images_from_api

    async def merge_frames_from_api(self,
                                    animation_data: List[dict],
                                    country: str,
                                    images_from_api: Tuple[bytes],
                                    localisation_layer: Image
                                    ) -> RadarAnimationData:
        """Merge three layers to create one frame of the radar: the basemap, the clouds and the location marker.
        Adds text in the top right to specify the timestamp of each image."""
        background: Image
        fill_color: tuple
        dark_mode = self._config_entry.data[CONF_DARK_MODE]
        satellite_mode = self._config_entry.data[CONF_STYLE] == CONF_STYLE_SATELLITE

        if country == 'NL':
            background = Image.open("custom_components/irm_kmi/resources/nl.png").convert('RGBA')
            fill_color = (0, 0, 0)
        else:
            image_path = (f"custom_components/irm_kmi/resources/be_"
                          f"{'satellite' if satellite_mode else 'black' if dark_mode else 'white'}.png")
            background = (Image.open(image_path).convert('RGBA'))
            fill_color = (255, 255, 255) if dark_mode or satellite_mode else (0, 0, 0)

        most_recent_frame = None
        tz = pytz.timezone(self.hass.config.time_zone)
        current_time = datetime.now(tz=tz)
        sequence: List[AnimationFrameData] = list()

        for (idx, sequence_element) in enumerate(animation_data):
            frame = images_from_api[idx]
            layer = Image.open(BytesIO(frame)).convert('RGBA')
            temp = Image.alpha_composite(background, layer)
            temp = Image.alpha_composite(temp, localisation_layer)

            draw = ImageDraw.Draw(temp)
            font = ImageFont.truetype("custom_components/irm_kmi/resources/roboto_medium.ttf", 16)
            time_image = (datetime.fromisoformat(sequence_element.get('time'))
                          .astimezone(tz=tz))

            time_str = time_image.isoformat(sep=' ', timespec='minutes')

            draw.text((4, 4), time_str, fill_color, font=font)

            bytes_img = BytesIO()
            temp.save(bytes_img, 'png', compress_level=8)

            sequence.append(
                AnimationFrameData(
                    time=time_image,
                    image=bytes_img.getvalue()
                )
            )

            if most_recent_frame is None and current_time < time_image:
                recent_idx = idx - 1 if idx > 0 else idx
                most_recent_frame = sequence[recent_idx].get('image', None)

        background.close()
        most_recent_frame = most_recent_frame if most_recent_frame is not None else sequence[-1].get('image')

        return RadarAnimationData(
            sequence=sequence,
            most_recent_image=most_recent_frame
        )

    @staticmethod
    def current_weather_from_data(api_data: dict) -> CurrentWeatherData:
        """Parse the API data to build a CurrentWeatherData."""
        # Process data to get current hour forecast
        now_hourly = None
        hourly_forecast_data = api_data.get('for', {}).get('hourly')
        if not (hourly_forecast_data is None
                or not isinstance(hourly_forecast_data, list)
                or len(hourly_forecast_data) == 0):

            for current in hourly_forecast_data[:2]:
                if datetime.now().strftime('%H') == current['hour']:
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
        except TypeError:
            pressure = None

        try:
            wind_speed = float(now_hourly.get('windSpeedKm', None)) if now_hourly is not None else None
        except TypeError:
            wind_speed = None

        try:
            wind_gust_speed = float(now_hourly.get('windPeakSpeedKm', None)) if now_hourly is not None else None
        except TypeError:
            wind_gust_speed = None

        try:
            temperature = float(api_data.get('obs', {}).get('temp'))
        except TypeError:
            temperature = None

        current_weather = CurrentWeatherData(
            condition=CDT_MAP.get((api_data.get('obs', {}).get('ww'), api_data.get('obs', {}).get('dayNight')), None),
            temperature=temperature,
            wind_speed=wind_speed,
            wind_gust_speed=wind_gust_speed,
            wind_bearing=now_hourly.get('windDirectionText', {}).get('en') if now_hourly is not None else None,
            pressure=pressure,
            uv_index=uv_index
        )

        if api_data.get('country', '') == 'NL':
            current_weather['wind_speed'] = api_data.get('obs', {}).get('windSpeedKm')
            current_weather['wind_bearing'] = api_data.get('obs', {}).get('windDirectionText', {}).get('en')

        return current_weather

    @staticmethod
    def hourly_list_to_forecast(data: List[dict] | None) -> List[Forecast] | None:
        """Parse data from the API to create a list of hourly forecasts"""
        if data is None or not isinstance(data, list) or len(data) == 0:
            return None

        forecasts = list()
        day = datetime.now()

        for f in data:
            if 'dateShow' in f:
                day = day + timedelta(days=1)

            hour = f.get('hour', None)
            if hour is None:
                continue

            precipitation_probability = None
            if f.get('precipChance', None) is not None:
                precipitation_probability = int(f.get('precipChance'))

            ww = None
            if f.get('ww', None) is not None:
                ww = int(f.get('ww'))

            forecast = Forecast(
                datetime=day.strftime(f'%Y-%m-%dT{hour}:00:00'),
                condition=CDT_MAP.get((ww, f.get('dayNight', None)), None),
                native_precipitation=f.get('precipQuantity', None),
                native_temperature=f.get('temp', None),
                native_templow=None,
                native_wind_gust_speed=f.get('windPeakSpeedKm', None),
                native_wind_speed=f.get('windSpeedKm', None),
                precipitation_probability=precipitation_probability,
                wind_bearing=f.get('windDirectionText', {}).get('en'),
                native_pressure=f.get('pressure', None),
                is_daytime=f.get('dayNight', None) == 'd'
            )

            forecasts.append(forecast)

        return forecasts

    @staticmethod
    def daily_list_to_forecast(data: List[dict] | None) -> List[Forecast] | None:
        """Parse data from the API to create a list of daily forecasts"""
        if data is None or not isinstance(data, list) or len(data) == 0:
            return None

        forecasts = list()
        n_days = 0

        for (idx, f) in enumerate(data):
            precipitation = None
            if f.get('precipQuantity', None) is not None:
                try:
                    precipitation = float(f.get('precipQuantity'))
                except TypeError:
                    pass

            native_wind_gust_speed = None
            if f.get('wind', {}).get('peakSpeed') is not None:
                try:
                    native_wind_gust_speed = int(f.get('wind', {}).get('peakSpeed'))
                except TypeError:
                    pass

            is_daytime = f.get('dayNight', None) == 'd'

            forecast = IrmKmiForecast(
                datetime=(datetime.now() + timedelta(days=n_days)).strftime('%Y-%m-%d')
                if is_daytime else datetime.now().strftime('%Y-%m-%d'),
                condition=CDT_MAP.get((f.get('ww1', None), f.get('dayNight', None)), None),
                native_precipitation=precipitation,
                native_temperature=f.get('tempMax', None),
                native_templow=f.get('tempMin', None),
                native_wind_gust_speed=native_wind_gust_speed,
                native_wind_speed=f.get('wind', {}).get('speed'),
                precipitation_probability=f.get('precipChance', None),
                wind_bearing=f.get('wind', {}).get('dirText', {}).get('en'),
                is_daytime=is_daytime,
                text_fr=f.get('text', {}).get('fr'),
                text_nl=f.get('text', {}).get('nl')
            )
            forecasts.append(forecast)
            if is_daytime or idx == 0:
                n_days += 1

        return forecasts
