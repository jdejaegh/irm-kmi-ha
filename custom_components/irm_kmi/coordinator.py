"""Example integration using DataUpdateCoordinator."""

import logging
from datetime import datetime, timedelta
from typing import List

import async_timeout
from homeassistant.components.weather import Forecast
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .api import IrmKmiApiClient, IrmKmiApiError
from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .const import OUT_OF_BENELUX
from .data import IrmKmiForecast

_LOGGER = logging.getLogger(__name__)


class IrmKmiCoordinator(DataUpdateCoordinator):
    """Coordinator to update data from IRM KMI"""

    def __init__(self, hass, zone):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="IRM KMI weather",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=7),
        )
        self._api_client = IrmKmiApiClient(session=async_get_clientsession(hass))
        self._zone = zone

    async def _async_update_data(self):
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
            raise UpdateFailed(f"Zone '{self._zone}' is out of Benelux and forecast is only available in the Benelux")

        return self.process_api_data(api_data)

    @staticmethod
    def process_api_data(api_data):
        # Process data to get current hour forecast
        now_hourly = None
        hourly_forecast_data = api_data.get('for', {}).get('hourly')
        if not (hourly_forecast_data is None
                or not isinstance(hourly_forecast_data, list)
                or len(hourly_forecast_data) == 0):

            for current in hourly_forecast_data[:2]:
                if datetime.now().strftime('%H') == current['hour']:
                    now_hourly = current
        # Get UV index
        module_data = api_data.get('module', None)
        uv_index = None
        if not (module_data is None or not isinstance(module_data, list)):
            for module in module_data:
                if module.get('type', None) == 'uv':
                    uv_index = module.get('data', {}).get('levelValue')
        # Put everything together
        processed_data = {
            'current_weather': {
                'condition': CDT_MAP.get(
                    (api_data.get('obs', {}).get('ww'), api_data.get('obs', {}).get('dayNight')), None),
                'temperature': api_data.get('obs', {}).get('temp'),
                'wind_speed': now_hourly.get('windSpeedKm', None) if now_hourly is not None else None,
                'wind_gust_speed': now_hourly.get('windPeakSpeedKm', None) if now_hourly is not None else None,
                'wind_bearing': now_hourly.get('windDirectionText', {}).get('en') if now_hourly is not None else None,
                'pressure': now_hourly.get('pressure', None) if now_hourly is not None else None,
                'uv_index': uv_index
            },
            'daily_forecast': IrmKmiCoordinator.daily_list_to_forecast(api_data.get('for', {}).get('daily')),
            'hourly_forecast': IrmKmiCoordinator.hourly_list_to_forecast(api_data.get('for', {}).get('hourly'))
        }
        return processed_data

    @staticmethod
    def hourly_list_to_forecast(data: List[dict] | None) -> List[Forecast] | None:
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
        if data is None or not isinstance(data, list) or len(data) == 0:
            return None

        forecasts = list()
        n_days = 0

        for f in data:
            precipitation = None
            if f.get('precipQuantity', None) is not None:
                precipitation = float(f.get('precipQuantity'))

            is_daytime = f.get('dayNight', None) == 'd'

            forecast = IrmKmiForecast(
                datetime=(datetime.now() + timedelta(days=n_days)).strftime('%Y-%m-%d')
                if is_daytime else datetime.now().strftime('%Y-%m-%d'),
                condition=CDT_MAP.get((f.get('ww1', None), f.get('dayNight', None)), None),
                native_precipitation=precipitation,
                native_temperature=f.get('tempMax', None),
                native_templow=f.get('tempMin', None),
                native_wind_gust_speed=f.get('wind', {}).get('peakSpeed'),
                native_wind_speed=f.get('wind', {}).get('speed'),
                precipitation_probability=f.get('precipChance', None),
                wind_bearing=f.get('wind', {}).get('dirText', {}).get('en'),
                is_daytime=is_daytime,
                text_fr=f.get('text', {}).get('fr'),
                text_nl=f.get('text', {}).get('nl')
            )
            forecasts.append(forecast)
            if is_daytime:
                n_days += 1

        return forecasts
