"""Constants for the IRM KMI integration."""
from typing import Final

from homeassistant.components.weather import (ATTR_CONDITION_CLEAR_NIGHT,
                                              ATTR_CONDITION_CLOUDY,
                                              ATTR_CONDITION_FOG,
                                              ATTR_CONDITION_LIGHTNING_RAINY,
                                              ATTR_CONDITION_PARTLYCLOUDY,
                                              ATTR_CONDITION_POURING,
                                              ATTR_CONDITION_RAINY,
                                              ATTR_CONDITION_SNOWY,
                                              ATTR_CONDITION_SNOWY_RAINY,
                                              ATTR_CONDITION_SUNNY)
from homeassistant.const import Platform

DOMAIN: Final = 'irm_kmi'
PLATFORMS: Final = [Platform.WEATHER, Platform.CAMERA, Platform.BINARY_SENSOR, Platform.SENSOR]
CONFIG_FLOW_VERSION = 5

OUT_OF_BENELUX: Final = ["außerhalb der Benelux (Brussels)",
                         "Hors de Belgique (Bxl)",
                         "Outside the Benelux (Brussels)",
                         "Buiten de Benelux (Brussel)"]
LANGS: Final = ['en', 'fr', 'nl', 'de']

OPTION_STYLE_STD: Final = 'standard_style'
OPTION_STYLE_CONTRAST: Final = 'contrast_style'
OPTION_STYLE_YELLOW_RED: Final = 'yellow_red_style'
OPTION_STYLE_SATELLITE: Final = 'satellite_style'
CONF_STYLE: Final = "style"

CONF_STYLE_OPTIONS: Final = [
    OPTION_STYLE_STD,
    OPTION_STYLE_CONTRAST,
    OPTION_STYLE_YELLOW_RED,
    OPTION_STYLE_SATELLITE
]

CONF_DARK_MODE: Final = "dark_mode"

STYLE_TO_PARAM_MAP: Final = {
    OPTION_STYLE_STD: 1,
    OPTION_STYLE_CONTRAST: 2,
    OPTION_STYLE_YELLOW_RED: 3,
    OPTION_STYLE_SATELLITE: 4
}

CONF_USE_DEPRECATED_FORECAST: Final = 'use_deprecated_forecast_attribute'
OPTION_DEPRECATED_FORECAST_NOT_USED: Final = 'do_not_use_deprecated_forecast'
OPTION_DEPRECATED_FORECAST_DAILY: Final = 'daily_in_deprecated_forecast'
OPTION_DEPRECATED_FORECAST_TWICE_DAILY: Final = 'twice_daily_in_deprecated_forecast'
OPTION_DEPRECATED_FORECAST_HOURLY: Final = 'hourly_in_deprecated_forecast'

CONF_USE_DEPRECATED_FORECAST_OPTIONS: Final = [
    OPTION_DEPRECATED_FORECAST_NOT_USED,
    OPTION_DEPRECATED_FORECAST_DAILY,
    OPTION_DEPRECATED_FORECAST_TWICE_DAILY,
    OPTION_DEPRECATED_FORECAST_HOURLY
]

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

MAP_WARNING_ID_TO_SLUG: Final = {
    0: 'wind',
    1: 'rain',
    2: 'ice_or_snow',
    3: 'thunder',
    7: 'fog',
    9: 'cold',
    12: 'thunder_wind_rain',
    13: 'thunderstorm_strong_gusts',
    14: 'thunderstorm_large_rainfall',
    15: 'storm_surge',
    17: 'coldspell'}

POLLEN_NAMES: Final = {'Alder', 'Ash', 'Birch', 'Grasses', 'Hazel', 'Mugwort', 'Oak'}

POLLEN_TO_ICON_MAP: Final = {
    'alder': 'mdi:tree', 'ash': 'mdi:tree', 'birch': 'mdi:tree', 'grasses': 'mdi:grass', 'hazel': 'mdi:tree',
    'mugwort': 'mdi:sprout', 'oak': 'mdi:tree'
}

IRM_KMI_NAME: Final = {
    'fr': 'Institut Royal Météorologique de Belgique',
    'nl': 'Koninklijk Meteorologisch Instituut van België',
    'de': 'Königliche Meteorologische Institut von Belgien',
    'en': 'Royal Meteorological Institute of Belgium'
}

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
