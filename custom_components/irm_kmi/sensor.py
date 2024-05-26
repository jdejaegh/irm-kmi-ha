"""Sensor for pollen from the IRM KMI"""
import datetime
import logging

import pytz
from homeassistant.components import sensor
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.irm_kmi import DOMAIN, IrmKmiCoordinator
from custom_components.irm_kmi.const import POLLEN_NAMES, POLLEN_TO_ICON_MAP
from custom_components.irm_kmi.pollen import PollenParser

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiPollen(coordinator, entry, pollen.lower()) for pollen in POLLEN_NAMES])
    async_add_entities([IrmKmiNextWarning(coordinator, entry),])


class IrmKmiPollen(CoordinatorEntity, SensorEntity):
    """Representation of a pollen sensor"""
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

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
        self._attr_device_info = coordinator.shared_device_info
        self._pollen = pollen
        self._attr_translation_key = f"pollen_{pollen}"
        self._attr_icon = POLLEN_TO_ICON_MAP[pollen]

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get('pollen', {}).get(self._pollen, None)


class IrmKmiNextWarning(CoordinatorEntity, SensorEntity):
    """Representation of the next weather warning"""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry,
                 ) -> None:
        super().__init__(coordinator)
        SensorEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}-next-warning"
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_next_warning")
        self._attr_device_info = coordinator.shared_device_info
        self._attr_translation_key = f"next_warning"

    @property
    def native_value(self) -> datetime.datetime | None:
        """Return the timestamp for the start of the next warning.  Is None when no future warning are available"""
        if self.coordinator.data.get('warnings') is None:
            return None

        now = datetime.datetime.now(tz=pytz.timezone(self.hass.config.time_zone))
        earliest_next = None
        for item in self.coordinator.data.get('warnings'):
            if now < item.get('starts_at'):
                if earliest_next is None:
                    earliest_next = item.get('starts_at')
                else:
                    earliest_next = min(earliest_next, item.get('starts_at'))

        return earliest_next

    @property
    def extra_state_attributes(self) -> dict:
        """Return the attributes related to all the future warnings."""
        now = datetime.datetime.now(tz=pytz.timezone(self.hass.config.time_zone))
        attrs = {"next_warnings": [w for w in self.coordinator.data.get('warnings', []) if now < w.get('starts_at')]}

        attrs["next_warnings_friendly_names"] = ", ".join(
            [warning['friendly_name'] for warning in attrs['next_warnings'] if warning['friendly_name'] != ''])

        return attrs
