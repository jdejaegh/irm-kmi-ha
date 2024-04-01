"""Sensor for pollen from the IRM KMI"""
import logging

from homeassistant.components import sensor

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.irm_kmi import DOMAIN, IrmKmiCoordinator
from custom_components.irm_kmi.const import POLLEN_NAMES
from custom_components.irm_kmi.pollen import PollenParser

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiPollen(coordinator, entry, pollen.lower()) for pollen in POLLEN_NAMES])


class IrmKmiPollen(CoordinatorEntity, SensorEntity):
    """Representation of a pollen sensor"""
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry,
                 pollen: str
                 ) -> None:
        super().__init__(coordinator)
        SensorEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}-pollen-{pollen}"
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_{pollen}_level")
        self._attr_options = PollenParser.get_option_values()
        self._attr_name = f"Pollen {pollen}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="IRM KMI",
            name=f"Pollen {pollen}"
        )
        self._pollen = pollen
        # TODO add translation for name
        # self._attr_translation_key = f"pollen_{pollen}"
        # _LOGGER.debug(f"translation key: {self._attr_translation_key}")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get('pollen', {}).get(self._pollen, None)
