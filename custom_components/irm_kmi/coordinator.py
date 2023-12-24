"""Example integration using DataUpdateCoordinator."""

from datetime import timedelta, datetime
import logging

import async_timeout

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .api import IrmKmiApiClient, IrmKmiApiError

_LOGGER = logging.getLogger(__name__)


class IrmKmiCoordinator(DataUpdateCoordinator):
    """Coordinator to update data from IRM KMI"""

    def __init__(self, hass, coord: dict):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="IRM KMI weather",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self._api_client = IrmKmiApiClient(session=async_get_clientsession(hass))
        self._coord = coord

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                api_data = await self._api_client.get_forecasts_coord(self._coord)
                _LOGGER.debug(f"Observation for {api_data.get('cityName', '')}: {api_data.get('obs', '{}')}")

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
                        'wind_bearing': now_hourly.get('windDirection', None) if now_hourly is not None else None,
                        'pressure': now_hourly.get('pressure', None) if now_hourly is not None else None,
                        'uv_index': uv_index
                    },

                    'hourly_forecast': {

                    }
                }

                return processed_data
        except IrmKmiApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
