"""Constants for the IRM KMI integration."""
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.weather import (
      ATTR_CONDITION_CLEAR_NIGHT,
      ATTR_CONDITION_CLOUDY,
      ATTR_CONDITION_FOG,
      ATTR_CONDITION_LIGHTNING_RAINY,
      ATTR_CONDITION_PARTLYCLOUDY,
      ATTR_CONDITION_POURING,
      ATTR_CONDITION_RAINY,
      ATTR_CONDITION_SNOWY,
      ATTR_CONDITION_SNOWY_RAINY,
      ATTR_CONDITION_SUNNY,
)
from homeassistant.const import (
      DEGREE,
      Platform,
      UnitOfPressure,
      UnitOfSpeed,
      UnitOfTemperature,
)
from irm_kmi_api import PollenName

DOMAIN: Final = 'irm_kmi'
PLATFORMS: Final = [Platform.WEATHER, Platform.CAMERA, Platform.BINARY_SENSOR, Platform.SENSOR]
CONFIG_FLOW_VERSION = 6

OUT_OF_BENELUX: Final = ["außerhalb der Benelux (Brussels)",
                         "Hors de Belgique (Bxl)",
                         "Outside the Benelux (Brussels)",
                         "Buiten de Benelux (Brussel)"]
LANGS: Final = ['en', 'fr', 'nl', 'de']

CONF_STYLE: Final = "style"

CONF_DARK_MODE: Final = "dark_mode"

# TODO delete those two constants when integrating with Home Assistant Core
CONF_USE_DEPRECATED_FORECAST: Final = 'use_deprecated_forecast_attribute'
OPTION_DEPRECATED_FORECAST_NOT_USED: Final = 'do_not_use_deprecated_forecast'

CONF_LANGUAGE_OVERRIDE: Final = 'language_override'

CONF_LANGUAGE_OVERRIDE_OPTIONS: Final = [
    'none', "fr", "nl", "de", "en"
]

REPAIR_SOLUTION: Final = "repair_solution"
REPAIR_OPT_MOVE: Final = "repair_option_move"
REPAIR_OPT_DELETE: Final = "repair_option_delete"
REPAIR_OPTIONS: Final = [REPAIR_OPT_MOVE, REPAIR_OPT_DELETE]

# map ('ww', 'dayNight') tuple from IRM KMI to HA conditions
IRM_KMI_TO_HA_CONDITION_MAP: Final = {
    (0, 'd'): ATTR_CONDITION_SUNNY,
    (0, 'n'): ATTR_CONDITION_CLEAR_NIGHT,
    (1, 'd'): ATTR_CONDITION_SUNNY,
    (1, 'n'): ATTR_CONDITION_CLEAR_NIGHT,
    (2, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (2, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (3, 'd'): ATTR_CONDITION_PARTLYCLOUDY,
    (3, 'n'): ATTR_CONDITION_PARTLYCLOUDY,
    (4, 'd'): ATTR_CONDITION_POURING,
    (4, 'n'): ATTR_CONDITION_POURING,
    (5, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (5, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (6, 'd'): ATTR_CONDITION_POURING,
    (6, 'n'): ATTR_CONDITION_POURING,
    (7, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (7, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (8, 'd'): ATTR_CONDITION_SNOWY_RAINY,
    (8, 'n'): ATTR_CONDITION_SNOWY_RAINY,
    (9, 'd'): ATTR_CONDITION_SNOWY_RAINY,
    (9, 'n'): ATTR_CONDITION_SNOWY_RAINY,
    (10, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (10, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (11, 'd'): ATTR_CONDITION_SNOWY,
    (11, 'n'): ATTR_CONDITION_SNOWY,
    (12, 'd'): ATTR_CONDITION_SNOWY,
    (12, 'n'): ATTR_CONDITION_SNOWY,
    (13, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (13, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (14, 'd'): ATTR_CONDITION_CLOUDY,
    (14, 'n'): ATTR_CONDITION_CLOUDY,
    (15, 'd'): ATTR_CONDITION_CLOUDY,
    (15, 'n'): ATTR_CONDITION_CLOUDY,
    (16, 'd'): ATTR_CONDITION_POURING,
    (16, 'n'): ATTR_CONDITION_POURING,
    (17, 'd'): ATTR_CONDITION_LIGHTNING_RAINY,
    (17, 'n'): ATTR_CONDITION_LIGHTNING_RAINY,
    (18, 'd'): ATTR_CONDITION_RAINY,
    (18, 'n'): ATTR_CONDITION_RAINY,
    (19, 'd'): ATTR_CONDITION_POURING,
    (19, 'n'): ATTR_CONDITION_POURING,
    (20, 'd'): ATTR_CONDITION_SNOWY_RAINY,
    (20, 'n'): ATTR_CONDITION_SNOWY_RAINY,
    (21, 'd'): ATTR_CONDITION_RAINY,
    (21, 'n'): ATTR_CONDITION_RAINY,
    (22, 'd'): ATTR_CONDITION_SNOWY,
    (22, 'n'): ATTR_CONDITION_SNOWY,
    (23, 'd'): ATTR_CONDITION_SNOWY,
    (23, 'n'): ATTR_CONDITION_SNOWY,
    (24, 'd'): ATTR_CONDITION_FOG,
    (24, 'n'): ATTR_CONDITION_FOG,
    (25, 'd'): ATTR_CONDITION_FOG,
    (25, 'n'): ATTR_CONDITION_FOG,
    (26, 'd'): ATTR_CONDITION_FOG,
    (26, 'n'): ATTR_CONDITION_FOG,
    (27, 'd'): ATTR_CONDITION_FOG,
    (27, 'n'): ATTR_CONDITION_FOG
}

POLLEN_TO_ICON_MAP: Final = {
    PollenName.ALDER: 'mdi:tree',
    PollenName.ASH: 'mdi:tree',
    PollenName.BIRCH: 'mdi:tree',
    PollenName.GRASSES: 'mdi:grass',
    PollenName.HAZEL: 'mdi:tree',
    PollenName.MUGWORT: 'mdi:sprout',
    PollenName.OAK: 'mdi:tree'
}

IRM_KMI_NAME: Final = {
    'fr': 'Institut Royal Météorologique de Belgique',
    'nl': 'Koninklijk Meteorologisch Instituut van België',
    'de': 'Königliche Meteorologische Institut von Belgien',
    'en': 'Royal Meteorological Institute of Belgium'
}

USER_AGENT: Final = 'github.com/jdejaegh/irm-kmi-ha 0.3.0'

CURRENT_WEATHER_SENSORS: Final = {'temperature', 'wind_speed', 'wind_gust_speed', 'wind_bearing', 'uv_index',
                                  'pressure'}

CURRENT_WEATHER_SENSOR_UNITS: Final = {'temperature': UnitOfTemperature.CELSIUS,
                                       'wind_speed': UnitOfSpeed.KILOMETERS_PER_HOUR,
                                       'wind_gust_speed': UnitOfSpeed.KILOMETERS_PER_HOUR,
                                       'wind_bearing': DEGREE,
                                       # Need to put '', else the history shows a bar graph instead of a chart
                                       'uv_index': '',
                                       'pressure': UnitOfPressure.HPA}

CURRENT_WEATHER_SENSOR_CLASS: Final = {'temperature': SensorDeviceClass.TEMPERATURE,
                                       'wind_speed': SensorDeviceClass.WIND_SPEED,
                                       'wind_gust_speed': SensorDeviceClass.WIND_SPEED,
                                       'wind_bearing': None,
                                       'uv_index': None,
                                       'pressure': SensorDeviceClass.ATMOSPHERIC_PRESSURE}

# Leave None when we want the default icon to be shown
CURRENT_WEATHER_SENSOR_ICON: Final = {'temperature': None,
                                       'wind_speed': None,
                                       'wind_gust_speed': None,
                                       'wind_bearing': 'mdi:compass',
                                       'uv_index': 'mdi:sun-wireless',
                                       'pressure': None}
