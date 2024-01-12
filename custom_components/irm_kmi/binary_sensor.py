"""Sensor to signal weather warning from the IRM KMI"""

import logging

from homeassistant.components import binary_sensor
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.irm_kmi import IrmKmiCoordinator, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the binary platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiWarning(coordinator, entry)])


class IrmKmiWarning(CoordinatorEntity, BinarySensorEntity):
    """Representation of a weather warning binary sensor"""

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry
                 ) -> None:
        _LOGGER.info(f"{entry.entry_id}, {entry.title}")
        super().__init__(coordinator)
        BinarySensorEntity.__init__(self)
        self._attr_device_class = BinarySensorDeviceClass.SAFETY
        self._attr_unique_id = entry.entry_id
        self.entity_id = binary_sensor.ENTITY_ID_FORMAT.format(f"weather_warning_{str(entry.title).lower()}")
        self._attr_name = f"Warning {entry.title}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="IRM KMI",
            name=f"Warning {entry.title}"
        )

    @property
    def is_on(self) -> bool | None:
        # TODO return a real value but first, change implementation of coordinator to expose the data
        return True
