from datetime import datetime, timedelta

from freezegun import freeze_time
from homeassistant.components.weather import (ATTR_CONDITION_CLOUDY,
                                              ATTR_CONDITION_PARTLYCLOUDY,
                                              ATTR_CONDITION_RAINY, Forecast)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi.coordinator import IrmKmiCoordinator
from custom_components.irm_kmi.data import CurrentWeatherData, IrmKmiForecast
from tests.conftest import get_api_data


async def test_jules_forgot_to_revert_update_interval_before_pushing(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    assert timedelta(minutes=5) <= coordinator.update_interval


@freeze_time(datetime.fromisoformat('2024-01-12T07:10:00'))
async def test_warning_data(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("be_forecast_warning.json")
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = coordinator.warnings_from_data(api_data.get('for', {}).get('warning'))

    assert isinstance(result, list)
    assert len(result) == 2

    first = result[0]

    assert first.get('starts_at').replace(tzinfo=None) < datetime.now()
    assert first.get('ends_at').replace(tzinfo=None) > datetime.now()

    assert first.get('slug') == 'fog'
    assert first.get('friendly_name') == 'Fog'
    assert first.get('id') == 7
    assert first.get('level') == 1


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00'))
def test_current_weather_be() -> None:
    api_data = get_api_data("forecast.json")
    result = IrmKmiCoordinator.current_weather_from_data(api_data)

    expected = CurrentWeatherData(
        condition=ATTR_CONDITION_CLOUDY,
        temperature=7,
        wind_speed=5,
        wind_gust_speed=None,
        wind_bearing='WSW',
        pressure=1020,
        uv_index=.7
    )

    assert result == expected


@freeze_time(datetime.fromisoformat("2023-12-28T15:30:00"))
def test_current_weather_nl() -> None:
    api_data = get_api_data("forecast_nl.json")
    result = IrmKmiCoordinator.current_weather_from_data(api_data)

    expected = CurrentWeatherData(
        condition=ATTR_CONDITION_CLOUDY,
        temperature=11,
        wind_speed=40,
        wind_gust_speed=None,
        wind_bearing='SW',
        pressure=1008,
        uv_index=1
    )

    assert expected == result


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00.028724'))
async def test_daily_forecast(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("forecast.json").get('for', {}).get('daily')

    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    result = coordinator.daily_list_to_forecast(api_data)

    assert isinstance(result, list)
    assert len(result) == 8

    expected = IrmKmiForecast(
        datetime='2023-12-27',
        condition=ATTR_CONDITION_PARTLYCLOUDY,
        native_precipitation=0,
        native_temperature=9,
        native_templow=4,
        native_wind_gust_speed=50,
        native_wind_speed=20,
        precipitation_probability=0,
        wind_bearing='S',
        is_daytime=True,
        text='Hey!',
    )

    assert result[1] == expected


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00.028724'))
def test_hourly_forecast() -> None:
    api_data = get_api_data("forecast.json").get('for', {}).get('hourly')
    result = IrmKmiCoordinator.hourly_list_to_forecast(api_data)

    assert isinstance(result, list)
    assert len(result) == 49

    expected = Forecast(
        datetime='2023-12-27T02:00:00',
        condition=ATTR_CONDITION_RAINY,
        native_precipitation=.98,
        native_temperature=8,
        native_templow=None,
        native_wind_gust_speed=None,
        native_wind_speed=15,
        precipitation_probability=70,
        wind_bearing='S',
        native_pressure=1020,
        is_daytime=False
    )

    assert result[8] == expected
