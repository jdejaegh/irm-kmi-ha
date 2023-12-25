import logging
from typing import List

from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature, Forecast
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, UnitOfPrecipitationDepth, UnitOfPressure
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .coordinator import IrmKmiCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug(f"IRM KMI setup.  Config: {config}")
    coordinator = IrmKmiCoordinator(hass, coord={'lat': config.get("lat"), 'long': config.get("lon")})

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([IrmKmiWeather(
        coordinator,
        config.get("name", "IRM KMI Weather")
    )])


class IrmKmiWeather(CoordinatorEntity, WeatherEntity):

    def __init__(self, coordinator: IrmKmiCoordinator, name: str) -> None:
        super().__init__(coordinator)
        self._name = name

    @property
    def supported_features(self) -> WeatherEntityFeature:
        features = WeatherEntityFeature(0)
        features |= WeatherEntityFeature.FORECAST_TWICE_DAILY
        features |= WeatherEntityFeature.FORECAST_HOURLY
        return features

    @property
    def name(self) -> str:
        return self._name

    @property
    def condition(self) -> str | None:
        return self.coordinator.data.get('current_weather').get('condition')

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get('current_weather').get('temperature')

    @property
    def native_temperature_unit(self) -> str | None:
        return UnitOfTemperature.CELSIUS

    @property
    def native_wind_speed_unit(self) -> str | None:
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get('current_weather').get('wind_speed')

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self.coordinator.data.get('current_weather').get('wind_gust_speed')

    @property
    def wind_bearing(self) -> float | str | None:
        return self.coordinator.data.get('current_weather').get('wind_bearing')

    @property
    def native_precipitation_unit(self) -> str | None:
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get('current_weather').get('pressure')

    @property
    def native_pressure_unit(self) -> str | None:
        return UnitOfPressure.HPA

    @property
    def uv_index(self) -> float | None:
        return self.coordinator.data.get('current_weather').get('uv_index')

    @property
    def forecast(self) -> list[Forecast] | None:
        result = list()
        if self.coordinator.data.get('daily_forecast') is not None:
            result += self.coordinator.data.get('daily_forecast')
        if self.coordinator.data.get('hourly_forecast') is not None:
            result += self.coordinator.data.get('hourly_forecast')
        return result

    async def async_forecast_twice_daily(self) -> List[Forecast] | None:
        return self.coordinator.data.get('daily_forecast')

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        return self.coordinator.data.get('hourly_forecast')
