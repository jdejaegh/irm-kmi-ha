from typing import TypedDict

from homeassistant.components.weather import Forecast

from .irm_kmi_api.data import CurrentWeatherData, IrmKmiForecast, WarningData
from .irm_kmi_api.rain_graph import RainGraph


class ProcessedCoordinatorData(TypedDict, total=False):
    """Data class that will be exposed to the entities consuming data from an IrmKmiCoordinator"""

    current_weather: CurrentWeatherData
    hourly_forecast: list[Forecast] | None
    daily_forecast: list[IrmKmiForecast] | None
    radar_forecast: list[Forecast] | None
    animation: RainGraph | None
    warnings: list[WarningData]
    pollen: dict
    country: str
