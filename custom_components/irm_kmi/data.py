"""Data classes for IRM KMI integration"""
from datetime import datetime
from typing import List, TypedDict

from homeassistant.components.weather import Forecast

from .rain_graph import RainGraph


class IrmKmiForecast(Forecast):
    """Forecast class with additional attributes for IRM KMI"""

    # TODO: add condition_2 as well and evolution to match data from the API?
    text: str | None
    sunrise: str | None
    sunset: str | None


class CurrentWeatherData(TypedDict, total=False):
    """Class to hold the currently observable weather at a given location"""
    condition: str | None
    temperature: float | None
    wind_speed: float | None
    wind_gust_speed: float | None
    wind_bearing: float | str | None
    uv_index: float | None
    pressure: float | None


class WarningData(TypedDict, total=False):
    """Holds data about a specific warning"""
    slug: str
    id: int
    level: int
    friendly_name: str
    text: str
    starts_at: datetime
    ends_at: datetime


class ProcessedCoordinatorData(TypedDict, total=False):
    """Data class that will be exposed to the entities consuming data from an IrmKmiCoordinator"""
    current_weather: CurrentWeatherData
    hourly_forecast: List[Forecast] | None
    daily_forecast: List[IrmKmiForecast] | None
    radar_forecast: List[Forecast] | None
    animation: RainGraph | None
    warnings: List[WarningData]
    pollen: dict
    country: str
