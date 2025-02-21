"""Sensor for pollen from the IRM KMI"""
import logging
from datetime import datetime

from homeassistant.components import sensor
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt

from custom_components.irm_kmi import DOMAIN, IrmKmiCoordinator
from custom_components.irm_kmi.const import POLLEN_NAMES, POLLEN_TO_ICON_MAP, CURRENT_WEATHER_SENSOR_UNITS, \
    CURRENT_WEATHER_SENSOR_CLASS, CURRENT_WEATHER_SENSORS
from custom_components.irm_kmi.data import IrmKmiForecast
from custom_components.irm_kmi.pollen import PollenParser

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiPollen(coordinator, entry, pollen.lower()) for pollen in POLLEN_NAMES])
    async_add_entities([IrmKmiCurrentWeather(coordinator, entry, name) for name in CURRENT_WEATHER_SENSORS])
    async_add_entities([IrmKmiNextWarning(coordinator, entry),])

    if coordinator.data.get('country') != 'NL':
        async_add_entities([IrmKmiNextSunMove(coordinator, entry, move) for move in ['sunset', 'sunrise']])


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
    def native_value(self) -> datetime | None:
        """Return the timestamp for the start of the next warning.  Is None when no future warning are available"""
        if self.coordinator.data.get('warnings') is None:
            return None

        now = dt.now()
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
        now = dt.now()
        attrs = {"next_warnings": [w for w in self.coordinator.data.get('warnings', []) if now < w.get('starts_at')]}

        attrs["next_warnings_friendly_names"] = ", ".join(
            [warning['friendly_name'] for warning in attrs['next_warnings'] if warning['friendly_name'] != ''])

        return attrs


class IrmKmiNextSunMove(CoordinatorEntity, SensorEntity):
    """Representation of the next sunrise or sunset"""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry,
                 move: str) -> None:
        assert move in ['sunset', 'sunrise']
        super().__init__(coordinator)
        SensorEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}-next-{move}"
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_next_{move}")
        self._attr_device_info = coordinator.shared_device_info
        self._attr_translation_key = f"next_{move}"
        self._move: str = move
        self._attr_icon = 'mdi:weather-sunset-down' if move == 'sunset' else 'mdi:weather-sunset-up'

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp for the next sunrise or sunset"""
        now = dt.now()
        data: list[IrmKmiForecast] = self.coordinator.data.get('daily_forecast')

        upcoming = [datetime.fromisoformat(f.get(self._move)) for f in data
                    if f.get(self._move) is not None and datetime.fromisoformat(f.get(self._move)) >= now]

        if len(upcoming) > 0:
            return upcoming[0]
        return None


class IrmKmiCurrentWeather(CoordinatorEntity, SensorEntity):
    """Representation of a current weather sensor"""

    _attr_has_entity_name = True
    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry,
                 sensor_name: str) -> None:
        super().__init__(coordinator)
        SensorEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}-current-{sensor_name}"
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_next_{sensor_name}")
        self._attr_device_info = coordinator.shared_device_info
        # TODO
        #  self._attr_translation_key = f"next_{move}"
        self._sensor_name: str = sensor_name

    @property
    def native_value(self) -> float | None:
        """Return the current value of the sensor"""
        return self.coordinator.data.get('current_weather', {}).get(self._sensor_name, None)

    @property
    def native_unit_of_measurement(self) -> str | None:
        return CURRENT_WEATHER_SENSOR_UNITS[self._sensor_name]

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return CURRENT_WEATHER_SENSOR_CLASS[self._sensor_name]
