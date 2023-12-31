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
    """Class to hold the currently observable weather at a given location"""
    condition: str | None
    temperature: float | None
    wind_speed: float | None
    wind_gust_speed: float | None
    wind_bearing: float | str | None
    uv_index: float | None
    pressure: float | None


class AnimationFrameData(TypedDict, total=False):
    """Holds one single frame of the radar camera, along with the timestamp of the frame"""
    time: datetime | None
    image: bytes | None
    value: float | None
    position: float | None
    position_higher: float | None
    position_lower: float | None
    rain_graph: bytes | None


class RadarAnimationData(TypedDict, total=False):
    """Holds frames and additional data for the animation to be rendered"""
    sequence: List[AnimationFrameData] | None
    most_recent_image_idx: int | None
    hint: str | None
    unit: str | None


class ProcessedCoordinatorData(TypedDict, total=False):
    """Data class that will be exposed to the entities consuming data from an IrmKmiCoordinator"""
    current_weather: CurrentWeatherData
    hourly_forecast: List[Forecast] | None
    daily_forecast: List[IrmKmiForecast] | None
    animation: RadarAnimationData
