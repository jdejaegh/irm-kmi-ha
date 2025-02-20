"""API Client for IRM KMI weather"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import socket
import time
from datetime import datetime

import aiohttp
import async_timeout
from .const import USER_AGENT

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
    cache_max_age = 60 * 60 * 2  # Remove items from the cache if they have not been hit since 2 hours
    cache = {}

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._base_url = "https://app.meteo.be/services/appv4/"

    async def get_forecasts_coord(self, coord: dict) -> dict:
        """Get forecasts for given city."""
        assert 'lat' in coord
        assert 'long' in coord
        coord['lat'] = round(coord['lat'], self.COORD_DECIMALS)
        coord['long'] = round(coord['long'], self.COORD_DECIMALS)

        response: bytes = await self._api_wrapper(params={"s": "getForecasts", "k": _api_key("getForecasts")} | coord)
        return json.loads(response)

    async def get_image(self, url, params: dict | None = None) -> bytes:
        """Get the image at the specified url with the parameters"""
        r: bytes = await self._api_wrapper(base_url=url, params={} if params is None else params)
        return r

    async def get_svg(self, url, params: dict | None = None) -> str:
        """Get SVG as str at the specified url with the parameters"""
        r: bytes = await self._api_wrapper(base_url=url, params={} if params is None else params)
        return r.decode()

    async def _api_wrapper(
            self,
            params: dict,
            base_url: str | None = None,
            path: str = "",
            method: str = "get",
            data: dict | None = None,
            headers: dict | None = None,
    ) -> bytes:
        """Get information from the API."""
        url = f"{self._base_url if base_url is None else base_url}{path}"

        if headers is None:
            headers = {'User-Agent': USER_AGENT}
        else:
            headers['User-Agent'] = USER_AGENT

        if url in self.cache:
            headers['If-None-Match'] = self.cache[url]['etag']

        try:
            async with async_timeout.timeout(60):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()

                if response.status == 304:
                    _LOGGER.debug(f"Cache hit for {url}")
                    self.cache[url]['timestamp'] = time.time()
                    return self.cache[url]['response']

                if 'ETag' in response.headers:
                    _LOGGER.debug(f"Saving in cache {url}")
                    r = await response.read()
                    self.cache[url] = {'etag': response.headers['ETag'], 'response': r, 'timestamp': time.time()}
                    return r

                return await response.read()

        except asyncio.TimeoutError as exception:
            raise IrmKmiApiCommunicationError("Timeout error fetching information") from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise IrmKmiApiCommunicationError("Error fetching information") from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise IrmKmiApiError(f"Something really wrong happened! {exception}") from exception

    def expire_cache(self):
        now = time.time()
        keys_to_delete = set()
        for key, value in self.cache.items():
            if now - value['timestamp'] > self.cache_max_age:
                keys_to_delete.add(key)
        for key in keys_to_delete:
            del self.cache[key]
        _LOGGER.info(f"Expired {len(keys_to_delete)} elements from API cache")
