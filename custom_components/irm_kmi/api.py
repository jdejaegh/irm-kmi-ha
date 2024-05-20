"""API Client for IRM KMI weather"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import socket
from datetime import datetime

import aiohttp
import async_timeout
from aiohttp import ClientResponse

_LOGGER = logging.getLogger(__name__)


class IrmKmiApiError(Exception):
    """Exception to indicate a general API error."""


class IrmKmiApiCommunicationError(IrmKmiApiError):
    """Exception to indicate a communication error."""


class IrmKmiApiParametersError(IrmKmiApiError):
    """Exception to indicate a parameter error."""


def _api_key(method_name: str) -> str:
    """Get API key."""
    return hashlib.md5(f"r9EnW374jkJ9acc;{method_name};{datetime.now().strftime('%d/%m/%Y')}".encode()).hexdigest()


class IrmKmiApiClient:
    """API client for IRM KMI weather data"""
    COORD_DECIMALS = 6

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._base_url = "https://app.meteo.be/services/appv4/"

    async def get_forecasts_coord(self, coord: dict) -> dict:
        """Get forecasts for given city."""
        assert 'lat' in coord
        assert 'long' in coord
        coord['lat'] = round(coord['lat'], self.COORD_DECIMALS)
        coord['long'] = round(coord['long'], self.COORD_DECIMALS)

        response = await self._api_wrapper(params={"s": "getForecasts", "k": _api_key("getForecasts")} | coord)
        return await response.json()

    async def get_image(self, url, params: dict | None = None) -> bytes:
        """Get the image at the specified url with the parameters"""
        r: ClientResponse = await self._api_wrapper(base_url=url, params={} if params is None else params)
        return await r.read()

    async def get_svg(self, url, params: dict | None = None) -> str:
        """Get SVG as str at the specified url with the parameters"""
        r: ClientResponse = await self._api_wrapper(base_url=url, params={} if params is None else params)
        return await r.text()

    async def _api_wrapper(
            self,
            params: dict,
            base_url: str | None = None,
            path: str = "",
            method: str = "get",
            data: dict | None = None,
            headers: dict | None = None,
    ) -> any:
        """Get information from the API."""
        if headers is None:
            headers = {'User-Agent': 'github.com/jdejaegh/irm-kmi-ha'}
        else:
            headers['User-Agent'] = 'github.com/jdejaegh/irm-kmi-ha'

        try:
            async with async_timeout.timeout(60):
                response = await self._session.request(
                    method=method,
                    url=f"{self._base_url if base_url is None else base_url}{path}",
                    headers=headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response

        except asyncio.TimeoutError as exception:
            raise IrmKmiApiCommunicationError("Timeout error fetching information") from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise IrmKmiApiCommunicationError("Error fetching information") from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise IrmKmiApiError(f"Something really wrong happened! {exception}") from exception
