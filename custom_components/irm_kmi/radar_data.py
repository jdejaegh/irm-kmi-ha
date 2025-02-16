"""Data classes related to radar forecast for IRM KMI integration"""
# This file was needed to avoid circular import with rain_graph.py and data.py
from datetime import datetime
from typing import TypedDict, List

from homeassistant.components.weather import Forecast


class IrmKmiRadarForecast(Forecast):
    """Forecast class to handle rain forecast from the IRM KMI rain radar"""
    rain_forecast_max: float
    rain_forecast_min: float
    might_rain: bool


class AnimationFrameData(TypedDict, total=False):
    """Holds one single frame of the radar camera, along with the timestamp of the frame"""
    time: datetime | None
    image: bytes | str | None
    value: float | None
    position: float | None
    position_higher: float | None
    position_lower: float | None


class RadarAnimationData(TypedDict, total=False):
    """Holds frames and additional data for the animation to be rendered"""
    sequence: List[AnimationFrameData] | None
    most_recent_image_idx: int | None
    hint: str | None
    unit: str | None
    location: bytes | str | None
    svg_still: bytes | None
    svg_animated: bytes | None
