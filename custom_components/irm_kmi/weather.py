import logging
from homeassistant.components.weather import WeatherEntity
from homeassistant.components.weather import ATTR_CONDITION_PARTLYCLOUDY
from homeassistant.const import UnitOfTemperature

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([IrmKmiWeather()])
    _LOGGER.warning("Irm KMI setup")


class IrmKmiWeather(WeatherEntity):

    @property
    def name(self) -> str:
        return "IRM KMI Weather"

    @property
    def condition(self) -> str | None:
        return ATTR_CONDITION_PARTLYCLOUDY

    @property
    def native_temperature(self) -> float | None:
        return 20.2

    @property
    def native_temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS
