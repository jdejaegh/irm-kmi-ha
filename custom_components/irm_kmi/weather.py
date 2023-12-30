"""Support for IRM KMI weather."""
import asyncio
import logging
from typing import List

from homeassistant.components.weather import (Forecast, WeatherEntity,
                                              WeatherEntityFeature)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (UnitOfPrecipitationDepth, UnitOfPressure,
                                 UnitOfSpeed, UnitOfTemperature)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, CONF_USE_DEPRECATED_FORECAST
from .const import OPTION_DEPRECATED_FORECAST_HOURLY, OPTION_DEPRECATED_FORECAST_NOT_USED, \
    OPTION_DEPRECATED_FORECAST_DAILY
from .coordinator import IrmKmiCoordinator
from .utils import get_config_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the weather entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiWeather(coordinator, entry)])


class IrmKmiWeather(CoordinatorEntity, WeatherEntity):

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry
                 ) -> None:
        super().__init__(coordinator)
        WeatherEntity.__init__(self)
        self._name = entry.title
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="IRM KMI",
            name=entry.title
        )
        self._deprecated_forecast_as = get_config_value(entry, CONF_USE_DEPRECATED_FORECAST)

    @property
    def supported_features(self) -> WeatherEntityFeature:
        features = WeatherEntityFeature(0)
        features |= WeatherEntityFeature.FORECAST_DAILY
        features |= WeatherEntityFeature.FORECAST_TWICE_DAILY
        features |= WeatherEntityFeature.FORECAST_HOURLY
        return features

    @property
    def name(self) -> str:
        return self._name

    @property
    def condition(self) -> str | None:
        return self.coordinator.data.get('current_weather', {}).get('condition')

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('temperature')

    @property
    def native_temperature_unit(self) -> str | None:
        return UnitOfTemperature.CELSIUS

    @property
    def native_wind_speed_unit(self) -> str | None:
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('wind_speed')

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('wind_gust_speed')

    @property
    def wind_bearing(self) -> float | str | None:
        return self.coordinator.data.get('current_weather', {}).get('wind_bearing')

    @property
    def native_precipitation_unit(self) -> str | None:
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('pressure')

    @property
    def native_pressure_unit(self) -> str | None:
        return UnitOfPressure.HPA

    @property
    def uv_index(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('uv_index')

    @property
    def forecast(self) -> list[Forecast] | None:
        """This attribute is deprecated by Home Assistant by still implemented for compatibility
        with older components.  Newer components should use the service weather.get_forecasts instead."""
        if self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_NOT_USED:
            return None
        elif self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_HOURLY:
            return self.coordinator.data.get('hourly_forecast')
        elif self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_DAILY:
            return self.daily_forecast()

    async def async_forecast_twice_daily(self) -> List[Forecast] | None:
        return self.coordinator.data.get('daily_forecast')

    async def async_forecast_daily(self) -> list[Forecast] | None:
        return self.daily_forecast()

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        return self.coordinator.data.get('hourly_forecast')

    def daily_forecast(self) -> list[Forecast] | None:
        data: list[Forecast] = self.coordinator.data.get('daily_forecast')
        if not isinstance(data, list):
            return None
        if len(data) > 1 and not data[0].get('is_daytime') and data[1].get('native_templow') is None:
            data[1]['native_templow'] = data[0].get('native_templow')
        if len(data) > 0 and not data[0].get('is_daytime'):
            return data
        if len(data) > 1 and data[0].get('native_templow') is None and not data[1].get('is_daytime'):
            data[0]['native_templow'] = data[1].get('native_templow')
        return [f for f in data if f.get('is_daytime')]
