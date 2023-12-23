"""API Client for IRM KMI weather"""
from __future__ import annotations

import asyncio
import socket

import aiohttp
import async_timeout
import hashlib
from datetime import datetime


class IrmKmiApiError(Exception):
    """Exception to indicate a general API error."""


class IrmKmiApiCommunicationError(
    IrmKmiApiError
):
    """Exception to indicate a communication error."""


class IrmKmiApiParametersError(
    IrmKmiApiError
):
    """Exception to indicate a parameter error."""


class IrmKmiApiAuthenticationError(
    IrmKmiApiError
):
    """Exception to indicate an authentication error."""


def _api_key(method_name: str):
    """Get API key."""
    return hashlib.md5(f"r9EnW374jkJ9acc;{method_name};{datetime.now().strftime('%d/%m/%Y')}".encode()).hexdigest()


class IrmKmiApiClient:
    """Sample API Client."""

    def __init__(
            self,
            session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._session = session
        self._base_url = "https://app.meteo.be/services/appv4/"

    async def get_forecasts_city(self, city_id: int) -> any:
        """Get forecasts for given city."""
        return await self._api_wrapper(
            params={"ins": city_id,
                    "s": "getForecasts"}
        )

    async def _api_wrapper(
            self,
            params: dict,
            path: str = "",
            method: str = "get",
            data: dict | None = None,
            headers: dict | None = None
    ) -> any:
        """Get information from the API."""

        if 's' not in params:
            raise IrmKmiApiParametersError("No query provided as 's' argument for API")
        else:
            params['k'] = _api_key(params['s'])

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=f"{self._base_url}{path}",
                    headers=headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError as exception:
            raise IrmKmiApiCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise IrmKmiApiCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise IrmKmiApiError(
                "Something really wrong happened!"
            ) from exception
