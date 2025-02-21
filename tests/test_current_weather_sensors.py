import inspect

from custom_components.irm_kmi.const import CURRENT_WEATHER_SENSORS, CURRENT_WEATHER_SENSOR_UNITS, \
    CURRENT_WEATHER_SENSOR_CLASS
from custom_components.irm_kmi.data import CurrentWeatherData

def test_sensors_in_current_weather_data():
    weather_data_keys = inspect.get_annotations(CurrentWeatherData).keys()

    for sensor in CURRENT_WEATHER_SENSORS:
        assert sensor in weather_data_keys

def test_sensors_have_unit():
    weather_sensor_units_keys = CURRENT_WEATHER_SENSOR_UNITS.keys()

    for sensor in CURRENT_WEATHER_SENSORS:
        assert sensor in weather_sensor_units_keys

def test_sensors_have_class():
    weather_sensor_class_keys = CURRENT_WEATHER_SENSOR_CLASS.keys()

    for sensor in CURRENT_WEATHER_SENSORS:
        assert sensor in weather_sensor_class_keys

