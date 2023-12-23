"""Example integration using DataUpdateCoordinator."""

from datetime import timedelta
import logging

import async_timeout

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

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
                data = await self._api_client.get_forecasts_coord(self._coord)
                return data
        except IrmKmiApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
