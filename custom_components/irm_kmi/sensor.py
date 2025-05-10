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
from irm_kmi_api import ExtendedForecast, PollenParser, PollenName, RadarForecast

from .coordinator import IrmKmiCoordinator
from .const import (CURRENT_WEATHER_SENSOR_CLASS, CURRENT_WEATHER_SENSOR_ICON,
                    CURRENT_WEATHER_SENSOR_UNITS, CURRENT_WEATHER_SENSORS,
                    POLLEN_TO_ICON_MAP, DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the sensor platform"""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiPollen(coordinator, entry, pollen) for pollen in PollenName])
    async_add_entities([IrmKmiCurrentWeather(coordinator, entry, name) for name in CURRENT_WEATHER_SENSORS])
    async_add_entities([IrmKmiNextWarning(coordinator, entry),
                        IrmKmiCurrentRainfall(coordinator, entry)])

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
                 pollen: PollenName
                 ) -> None:
        super().__init__(coordinator)
        SensorEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}-pollen-{pollen.value}"
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_{pollen.value}_level")
        self._attr_options = [p.value for p in PollenParser.get_option_values()]
        self._attr_device_info = coordinator.shared_device_info
        self._pollen = pollen
        self._attr_translation_key = f"pollen_{pollen.value}"
        self._attr_icon = POLLEN_TO_ICON_MAP[pollen]

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        r = self.coordinator.data.get('pollen', {}).get(self._pollen, None)
        return r.value if r is not None else None


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
        data: list[ExtendedForecast] = self.coordinator.data.get('daily_forecast')

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
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_current_{sensor_name}")
        self._attr_device_info = coordinator.shared_device_info
        self._attr_translation_key = f"current_{sensor_name}"
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

    @property
    def icon(self) -> str | None:
        return CURRENT_WEATHER_SENSOR_ICON[self._sensor_name]


class IrmKmiCurrentRainfall(CoordinatorEntity, SensorEntity):
    """Representation of a current rainfall sensor"""

    _attr_has_entity_name = True
    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        SensorEntity.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}-current-rainfall"
        self.entity_id = sensor.ENTITY_ID_FORMAT.format(f"{str(entry.title).lower()}_current_rainfall")
        self._attr_device_info = coordinator.shared_device_info
        self._attr_translation_key = "current_rainfall"
        self._attr_icon = 'mdi:weather-pouring'

    def _current_forecast(self) -> RadarForecast | None:
        now = dt.now()
        forecasts = self.coordinator.data.get('radar_forecast', None)

        if forecasts is None:
            return None

        prev = forecasts[0]
        for f in forecasts:
            if datetime.fromisoformat(f.get('datetime')) > now:
                return prev
            prev = f

        return forecasts[-1]

    @property
    def native_value(self) -> float | None:
        """Return the current value of the sensor"""
        current = self._current_forecast()

        if current is None:
            return None

        return current.get('native_precipitation', None)

    @property
    def native_unit_of_measurement(self) -> str | None:
        current = self._current_forecast()

        if current is None:
            return None

        return current.get('unit', None)