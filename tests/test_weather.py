import json
from datetime import datetime
from typing import List

from freezegun import freeze_time
from homeassistant.components.weather import Forecast
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture

from custom_components.irm_kmi import IrmKmiCoordinator, IrmKmiWeather
from custom_components.irm_kmi.data import ProcessedCoordinatorData
from custom_components.irm_kmi.irm_kmi_api.data import IrmKmiRadarForecast
from tests.conftest import get_api_with_data


@freeze_time(datetime.fromisoformat("2023-12-28T15:30:00+01:00"))
async def test_weather_nl(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    forecast = json.loads(load_fixture("forecast_nl.json"))
    coordinator._api._api_data = forecast

    coordinator.data = await coordinator.process_api_data()
    weather = IrmKmiWeather(coordinator, mock_config_entry)
    result = await weather.async_forecast_daily()

    assert isinstance(result, list)
    assert len(result) == 7

    # When getting daily forecast, the min temperature of the current day
    # should be the min temperature of the coming night
    assert result[0]['native_templow'] == 9


@freeze_time(datetime.fromisoformat("2024-01-21T14:15:00+01:00"))
async def test_weather_higher_temp_at_night(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    # Test case for https://github.com/jdejaegh/irm-kmi-ha/issues/8
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    forecast = json.loads(load_fixture("high_low_temp.json"))
    coordinator._api._api_data = forecast

    coordinator.data = await coordinator.process_api_data()

    weather = IrmKmiWeather(coordinator, mock_config_entry)
    result: List[Forecast] = await weather.async_forecast_daily()

    for f in result:
        if f['native_temperature'] is not None and f['native_templow'] is not None:
            assert f['native_temperature'] >= f['native_templow']

    result: List[Forecast] = await weather.async_forecast_twice_daily()

    for f in result:
        if f['native_temperature'] is not None and f['native_templow'] is not None:
            assert f['native_temperature'] >= f['native_templow']


@freeze_time(datetime.fromisoformat("2023-12-26T18:30:00+01:00"))
async def test_forecast_attribute_same_as_service_call(
        hass: HomeAssistant,
        mock_config_entry_with_deprecated: MockConfigEntry
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry_with_deprecated)
    forecast = json.loads(load_fixture("forecast.json"))
    coordinator._api._api_data = forecast

    coordinator.data = await coordinator.process_api_data()

    weather = IrmKmiWeather(coordinator, mock_config_entry_with_deprecated)

    result_service: List[Forecast] = await weather.async_forecast_twice_daily()
    result_forecast: List[Forecast] = weather.extra_state_attributes['forecast']

    assert result_service == result_forecast


@freeze_time(datetime.fromisoformat("2023-12-26T17:58:03+01:00"))
async def test_radar_forecast_service(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
):
    hass.config.time_zone = 'Europe/Brussels'
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    coordinator._api = get_api_with_data("forecast.json")

    coordinator.data = ProcessedCoordinatorData(
        radar_forecast=coordinator._api.get_radar_forecast()
    )

    weather = IrmKmiWeather(coordinator, mock_config_entry)

    result_service: List[Forecast] = weather.get_forecasts_radar_service(False)

    expected = [
        IrmKmiRadarForecast(datetime="2023-12-26T17:00:00+01:00", native_precipitation=0, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T17:10:00+01:00", native_precipitation=0, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T17:20:00+01:00", native_precipitation=0, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T17:30:00+01:00", native_precipitation=0, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T17:40:00+01:00", native_precipitation=0.1, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T17:50:00+01:00", native_precipitation=0.01, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T18:00:00+01:00", native_precipitation=0.12, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T18:10:00+01:00", native_precipitation=1.2, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T18:20:00+01:00", native_precipitation=2, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T18:30:00+01:00", native_precipitation=0, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min'),
        IrmKmiRadarForecast(datetime="2023-12-26T18:40:00+01:00", native_precipitation=0, might_rain=False,
                            rain_forecast_max=0, rain_forecast_min=0, unit='mm/10min')
    ]

    assert result_service == expected[5:]

    result_service: List[Forecast] = weather.get_forecasts_radar_service(True)

    assert result_service == expected
