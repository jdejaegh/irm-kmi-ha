import logging

from homeassistant.components.weather import WeatherEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .coordinator import IrmKmiCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug(f"IRM KMI setup.  Config: {config}")
    coordinator = IrmKmiCoordinator(hass, city_id=config.get("city_id"))
    await coordinator.async_request_refresh()

    async_add_entities([IrmKmiWeather(
        coordinator,
        config.get("name", "IRM KMI Weather")
    )])


class IrmKmiWeather(CoordinatorEntity, WeatherEntity):

    def __init__(self, coordinator: IrmKmiCoordinator, name: str) -> None:
        super().__init__(coordinator)
        self._name = name

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
    def native_temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS
