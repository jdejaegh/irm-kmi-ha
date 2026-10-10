"""Data classes for IRM KMI integration"""
from datetime import datetime
from enum import Enum
from typing import List, Required, TypedDict


class Forecast(TypedDict, total=False):
    """Typed weather forecast dict.

    All attributes are in native units and old attributes kept
    for backwards compatibility.

    Data from Home Assistant to avoid to depend on Home Assistant for this
    """

    condition: str | None
    datetime: Required[str]
    humidity: float | None
    precipitation_probability: int | None
    cloud_coverage: int | None
    native_precipitation: float | None
    precipitation: None
    native_pressure: float | None
    pressure: None
    native_temperature: float | None
    temperature: None
    native_templow: float | None
    templow: None
    native_apparent_temperature: float | None
    wind_bearing: float | str | None
    native_wind_gust_speed: float | None
    native_wind_speed: float | None
    wind_speed: None
    native_dew_point: float | None
    uv_index: float | None
    is_daytime: bool | None  # Mandatory to use with forecast_twice_daily


class IrmKmiConditionEvol(Enum):
    ONE_WAY = 'one_way'
    TWO_WAYS = 'two_ways'
    STABLE = 'stable'

class IrmKmiForecast(Forecast, total=False):
    """Forecast class with additional attributes for IRM KMI"""

    condition_2: str | None
    condition_evol: IrmKmiConditionEvol | None
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


class IrmKmiRadarForecast(Forecast):
    """Forecast class to handle rain forecast from the IRM KMI rain radar"""
    rain_forecast_max: float
    rain_forecast_min: float
    might_rain: bool
    unit: str | None


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
