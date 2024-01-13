"""Sensor to signal weather warning from the IRM KMI"""
import datetime
import logging

import pytz
from homeassistant.components import binary_sensor
from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                    BinarySensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.irm_kmi import DOMAIN, IrmKmiCoordinator

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
        if self.coordinator.data.get('warnings') is None:
            return False

        now = datetime.datetime.now(tz=pytz.timezone(self.hass.config.time_zone))
        for item in self.coordinator.data.get('warnings'):
            if item.get('starts_at') < now < item.get('ends_at'):
                return True

        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return the camera state attributes."""
        attrs = {"warnings": self.coordinator.data.get('warnings', [])}
        return attrs
