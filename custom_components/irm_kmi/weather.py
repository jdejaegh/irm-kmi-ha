import logging

from datetime import datetime

from homeassistant.components.weather import WeatherEntity
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, UnitOfPrecipitationDepth, UnitOfPressure
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .coordinator import IrmKmiCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug(f"IRM KMI setup.  Config: {config}")
    coordinator = IrmKmiCoordinator(hass, coord={'lat': config.get("lat"), 'long': config.get("lon")})

    await coordinator.async_request_refresh()

    async_add_entities([IrmKmiWeather(
        coordinator,
        config.get("name", "IRM KMI Weather")
    )])


class IrmKmiWeather(CoordinatorEntity, WeatherEntity):

    def __init__(self, coordinator: IrmKmiCoordinator, name: str) -> None:
        super().__init__(coordinator)
        self._name = name

    def _current_hour_data(self) -> dict | None:
        data = self.coordinator.data.get('for', {}).get('hourly')
        if data is None or not isinstance(data, list) or len(data) == 0:
            return None
        data = data[0]
        if datetime.now().strftime('%H') != data['hour']:
            return None
        return data

    @property
    def name(self) -> str:
        return self._name

    @property
    def condition(self) -> str | None:
        irm_condition = (self.coordinator.data.get('obs', {}).get('ww'),
                         self.coordinator.data.get('obs', {}).get('dayNight'))
        return CDT_MAP.get(irm_condition, None)

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get('obs', {}).get('temp')

    @property
    def native_temperature_unit(self) -> str | None:
        return UnitOfTemperature.CELSIUS

    @property
    def native_wind_speed_unit(self) -> str | None:
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def native_wind_speed(self) -> float | None:
        data = self._current_hour_data()
        return data.get('windSpeedKm', None)

    @property
    def native_wind_gust_speed(self) -> float | None:
        data = self._current_hour_data()
        return data.get('windPeakSpeedKm', None)

    @property
    def wind_bearing(self) -> float | str | None:
        data = self._current_hour_data()
        return data.get('windDirection', None)

    @property
    def native_precipitation_unit(self) -> str | None:
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def native_pressure(self) -> float | None:
        data = self._current_hour_data()
        return data.get('pressure', None)

    @property
    def native_pressure_unit(self) -> str | None:
        return UnitOfPressure.HPA

    @property
    def uv_index(self) -> float | None:
        data = self.coordinator.data.get('module', None)
        if data is None or not isinstance(data, list):
            return None

        for module in data:
            if module.get('type', None) == 'uv':
                return module.get('data', {}).get('levelValue')

        return None
