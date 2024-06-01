"""Sensor to signal weather warning from the IRM KMI"""
import logging

from homeassistant.components import binary_sensor
from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                    BinarySensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt

from custom_components.irm_kmi import DOMAIN, IrmKmiCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the binary platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiWarning(coordinator, entry)])


class IrmKmiWarning(CoordinatorEntity, BinarySensorEntity):
    """Representation of a weather warning binary sensor"""

    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry
                 ) -> None:
        super().__init__(coordinator)
        BinarySensorEntity.__init__(self)
        self._attr_device_class = BinarySensorDeviceClass.SAFETY
        self._attr_unique_id = entry.entry_id
        self.entity_id = binary_sensor.ENTITY_ID_FORMAT.format(f"weather_warning_{str(entry.title).lower()}")
        self._attr_name = f"Warning {entry.title}"
        self._attr_device_info = coordinator.shared_device_info

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data.get('warnings') is None:
            return False

        now = dt.now()
        for item in self.coordinator.data.get('warnings'):
            if item.get('starts_at') < now < item.get('ends_at'):
                return True

        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return the warning sensor attributes."""
        attrs = {"warnings": self.coordinator.data.get('warnings', [])}

        now = dt.now()
        for warning in attrs['warnings']:
            warning['is_active'] = warning.get('starts_at') < now < warning.get('ends_at')

        attrs["active_warnings_friendly_names"] = ", ".join([warning['friendly_name'] for warning in attrs['warnings']
                                                             if warning['is_active'] and warning['friendly_name'] != ''])

        return attrs
