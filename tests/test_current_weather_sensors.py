import inspect
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator
from custom_components.irm_kmi.const import CURRENT_WEATHER_SENSORS, CURRENT_WEATHER_SENSOR_UNITS, \
    CURRENT_WEATHER_SENSOR_CLASS
from custom_components.irm_kmi.data import CurrentWeatherData, ProcessedCoordinatorData
from custom_components.irm_kmi.sensor import IrmKmiCurrentWeather, IrmKmiCurrentRainfall
from tests.conftest import get_api_data


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


@pytest.mark.parametrize("sensor,expected,filename",
                         [
                             ('temperature', -2, 'be_forecast_warning.json'),
                             ('temperature', 7, 'forecast.json'),
                             ('temperature', 15, 'forecast_ams_no_ww.json'),
                             ('temperature', 9, 'forecast_out_of_benelux.json'),
                             ('temperature', 13, 'forecast_with_rain_on_radar.json'),
                             ('temperature', 4, 'high_low_temp.json'),
                             ('temperature', 14, 'midnight-bug-31-05-2024T00-13.json'),
                             ('temperature', 13, 'no-midnight-bug-31-05-2024T01-55.json'),

                             ('wind_speed', 10, 'be_forecast_warning.json'),
                             ('wind_speed', 5, 'forecast.json'),
                             ('wind_speed', 26, 'forecast_ams_no_ww.json'),
                             ('wind_speed', 25, 'forecast_out_of_benelux.json'),
                             ('wind_speed', 15, 'forecast_with_rain_on_radar.json'),
                             ('wind_speed', 30, 'high_low_temp.json'),
                             ('wind_speed', 10, 'midnight-bug-31-05-2024T00-13.json'),
                             ('wind_speed', 15, 'no-midnight-bug-31-05-2024T01-55.json'),

                             ('wind_gust_speed', None, 'be_forecast_warning.json'),
                             ('wind_gust_speed', None, 'forecast.json'),
                             ('wind_gust_speed', None, 'forecast_ams_no_ww.json'),
                             ('wind_gust_speed', None, 'forecast_out_of_benelux.json'),
                             ('wind_gust_speed', None, 'forecast_with_rain_on_radar.json'),
                             ('wind_gust_speed', 50, 'high_low_temp.json'),
                             ('wind_gust_speed', None, 'midnight-bug-31-05-2024T00-13.json'),
                             ('wind_gust_speed', None, 'no-midnight-bug-31-05-2024T01-55.json'),

                             ('wind_bearing', 23, 'be_forecast_warning.json'),
                             ('wind_bearing', 248, 'forecast.json'),
                             ('wind_bearing', 270, 'forecast_ams_no_ww.json'),
                             ('wind_bearing', 180, 'forecast_out_of_benelux.json'),
                             ('wind_bearing', 293, 'forecast_with_rain_on_radar.json'),
                             ('wind_bearing', 180, 'high_low_temp.json'),
                             ('wind_bearing', 293, 'midnight-bug-31-05-2024T00-13.json'),
                             ('wind_bearing', 270, 'no-midnight-bug-31-05-2024T01-55.json'),

                             ('uv_index', 0.7, 'be_forecast_warning.json'),
                             ('uv_index', 0.7, 'forecast.json'),
                             ('uv_index', 6, 'forecast_ams_no_ww.json'),
                             ('uv_index', 0.6, 'forecast_out_of_benelux.json'),
                             ('uv_index', None, 'forecast_with_rain_on_radar.json'),
                             ('uv_index', 0.7, 'high_low_temp.json'),
                             ('uv_index', 5.6, 'midnight-bug-31-05-2024T00-13.json'),
                             ('uv_index', 5.6, 'no-midnight-bug-31-05-2024T01-55.json'),

                             ('pressure', 1034, 'be_forecast_warning.json'),
                             ('pressure', 1020, 'forecast.json'),
                             ('pressure', 1010, 'forecast_ams_no_ww.json'),
                             ('pressure', 1013, 'forecast_out_of_benelux.json'),
                             ('pressure', 1006, 'forecast_with_rain_on_radar.json'),
                             ('pressure', 1022, 'high_low_temp.json'),
                             ('pressure', 1010, 'midnight-bug-31-05-2024T00-13.json'),
                             ('pressure', 1010, 'no-midnight-bug-31-05-2024T01-55.json'),

                             ('rainfall', 0.42, 'be_forecast_warning.json'),
                             ('rainfall', 0.15, 'forecast_nl.json'),
                             ('rainfall', 0, 'forecast.json'),
                             ('rainfall', 0.1341, 'forecast_ams_no_ww.json'),
                             ('rainfall', 0, 'forecast_out_of_benelux.json'),
                             ('rainfall', 0.33, 'forecast_with_rain_on_radar.json'),
                             ('rainfall', 0, 'high_low_temp.json'),
                             ('rainfall', 0, 'midnight-bug-31-05-2024T00-13.json'),
                             ('rainfall', 0, 'no-midnight-bug-31-05-2024T01-55.json'),
                         ])
async def test_current_weather_sensors(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        sensor,
        expected,
        filename
) -> None:
    hass.config.time_zone = 'Europe/Brussels'

    api_data = get_api_data(filename)
    time = api_data.get('obs').get('timestamp')

    @freeze_time(datetime.fromisoformat(time) + timedelta(seconds=45, minutes=1))
    async def run(mock_config_entry_, sensor_, expected_):
        coordinator = IrmKmiCoordinator(hass, mock_config_entry_)
        coordinator.data = ProcessedCoordinatorData(
            current_weather=await IrmKmiCoordinator.current_weather_from_data(api_data),
            hourly_forecast=await IrmKmiCoordinator.hourly_list_to_forecast(api_data.get('for', {}).get('hourly')),
            radar_forecast=IrmKmiCoordinator.radar_list_to_forecast(api_data.get('animation', {})),
            country=api_data.get('country')
        )

        if sensor_ == 'rainfall':
            s = IrmKmiCurrentRainfall(coordinator, mock_config_entry_)
        else:
            s = IrmKmiCurrentWeather(coordinator, mock_config_entry_, sensor_)

        assert s.native_value == expected_

    await run(mock_config_entry, sensor, expected)


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
    api_data = get_api_data(filename)

    coordinator.data = ProcessedCoordinatorData(
        current_weather=await IrmKmiCoordinator.current_weather_from_data(api_data),
        hourly_forecast=await IrmKmiCoordinator.hourly_list_to_forecast(api_data.get('for', {}).get('hourly')),
        radar_forecast=IrmKmiCoordinator.radar_list_to_forecast(api_data.get('animation', {})),
        country=api_data.get('country')
    )

    s = IrmKmiCurrentRainfall(coordinator, mock_config_entry)

    assert s.native_unit_of_measurement == expected
