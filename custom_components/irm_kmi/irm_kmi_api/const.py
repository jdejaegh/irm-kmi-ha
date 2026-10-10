from typing import Final

from .data import IrmKmiConditionEvol

POLLEN_NAMES: Final = {"Alder", "Ash", "Birch", "Grasses", "Hazel", "Mugwort", "Oak"}
POLLEN_LEVEL_TO_COLOR = {
    "null": "green",
    "low": "yellow",
    "moderate": "orange",
    "high": "red",
    "very high": "purple",
    "active": "active",
}
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# TODO move those to an Enum
OPTION_STYLE_STD: Final = "standard_style"
OPTION_STYLE_CONTRAST: Final = "contrast_style"
OPTION_STYLE_YELLOW_RED: Final = "yellow_red_style"
OPTION_STYLE_SATELLITE: Final = "satellite_style"
STYLE_TO_PARAM_MAP: Final = {
    OPTION_STYLE_STD: 1,
    OPTION_STYLE_CONTRAST: 2,
    OPTION_STYLE_YELLOW_RED: 3,
    OPTION_STYLE_SATELLITE: 4,
}

MAP_WARNING_ID_TO_SLUG: Final = {
    0: "wind",
    1: "rain",
    2: "ice_or_snow",
    3: "thunder",
    7: "fog",
    9: "cold",
    10: "heat",
    12: "thunder_wind_rain",
    13: "thunderstorm_strong_gusts",
    14: "thunderstorm_large_rainfall",
    15: "storm_surge",
    17: "coldspell",
}

WWEVOL_TO_ENUM_MAP: Final = {
    None: IrmKmiConditionEvol.STABLE,
    0: IrmKmiConditionEvol.ONE_WAY,
    1: IrmKmiConditionEvol.TWO_WAYS,
}
