"""Data classes for IRM KMI integration"""
from datetime import datetime
from typing import List, TypedDict

from homeassistant.components.weather import Forecast


class IrmKmiForecast(Forecast):
    """Forecast class with additional attributes for IRM KMI"""

    # TODO: add condition_2 as well and evolution to match data from the API?
    text_fr: str | None
    text_nl: str | None


class CurrentWeatherData(TypedDict, total=False):
    condition: str | None
    temperature: float | None
    wind_speed: float | None
    wind_gust_speed: float | None
    wind_bearing: float | str | None
    uv_index: float | None
    pressure: float | None


class AnimationFrameData(TypedDict, total=False):
    time: datetime | None
    image: bytes | None


class RadarAnimationData(TypedDict, total=False):
    sequence: List[AnimationFrameData] | None
    most_recent_image: bytes | None
    hint: str | None


class ProcessedCoordinatorData(TypedDict, total=False):
    current_weather: CurrentWeatherData
    hourly_forecast: List[Forecast] | None
    daily_forecast: List[IrmKmiForecast] | None
    animation: RadarAnimationData
