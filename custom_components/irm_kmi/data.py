from typing import TypedDict, List

from homeassistant.components.weather import Forecast

from .irm_kmi_api.data import CurrentWeatherData, IrmKmiForecast, WarningData
from .irm_kmi_api.rain_graph import RainGraph


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
