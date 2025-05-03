import inspect
from zoneinfo import ZoneInfo

import pytest
from homeassistant.core import HomeAssistant
from irm_kmi_api.data import CurrentWeatherData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator
from custom_components.irm_kmi.const import (CURRENT_WEATHER_SENSOR_CLASS,
                                             CURRENT_WEATHER_SENSOR_UNITS,
                                             CURRENT_WEATHER_SENSORS)
from custom_components.irm_kmi.data import ProcessedCoordinatorData
from custom_components.irm_kmi.sensor import IrmKmiCurrentRainfall
from tests.conftest import get_api_with_data


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



@pytest.mark.parametrize("expected,filename",
                         [
                             ('mm/h', 'forecast_ams_no_ww.json'),
                             ('mm/10min', 'forecast_out_of_benelux.json'),
                             ('mm/10min', 'forecast_with_rain_on_radar.json'),
                         ])
async def test_current_rainfall_unit(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        expected,
        filename
) -> None:
    hass.config.time_zone = 'Europe/Brussels'
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    api = get_api_with_data(filename)
    tz = ZoneInfo("Europe/Brussels")

    coordinator.data = ProcessedCoordinatorData(
        current_weather=api.get_current_weather(tz),
        hourly_forecast=api.get_hourly_forecast(tz),
        radar_forecast=api.get_radar_forecast(),
        country=api.get_country()
    )

    s = IrmKmiCurrentRainfall(coordinator, mock_config_entry)

    assert s.native_unit_of_measurement == expected
