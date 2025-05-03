from datetime import timedelta

from homeassistant.components.weather import ATTR_CONDITION_CLOUDY
from homeassistant.core import HomeAssistant
from irm_kmi_api.data import CurrentWeatherData, IrmKmiRadarForecast
from irm_kmi_api.pollen import PollenParser
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi.coordinator import IrmKmiCoordinator
from custom_components.irm_kmi.data import ProcessedCoordinatorData
from tests.conftest import get_api_data, get_api_with_data


async def test_jules_forgot_to_revert_update_interval_before_pushing(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    assert timedelta(minutes=5) <= coordinator.update_interval


async def test_refresh_succeed_even_when_pollen_and_radar_fail(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
):
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    coordinator._api._api_data = get_api_data("forecast.json")

    result = await coordinator.process_api_data()

    assert result.get('current_weather').get('condition') == ATTR_CONDITION_CLOUDY

    assert result.get('animation').get_hint() == "No rain forecasted shortly"

    assert result.get('pollen') == PollenParser.get_unavailable_data()

    existing_data = ProcessedCoordinatorData(
        current_weather=CurrentWeatherData(),
        daily_forecast=[],
        hourly_forecast=[],
        animation=None,
        warnings=[],
        pollen={'foo': 'bar'}
    )
    coordinator.data = existing_data
    result = await coordinator.process_api_data()

    assert result.get('current_weather').get('condition') == ATTR_CONDITION_CLOUDY

    assert result.get('animation').get_hint() == "No rain forecasted shortly"

    assert result.get('pollen') == {'foo': 'bar'}


def test_radar_forecast() -> None:
    api = get_api_with_data("forecast.json")
    result = api.get_radar_forecast()

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

    assert expected == result


def test_radar_forecast_rain_interval() -> None:
    api = get_api_with_data('forecast_with_rain_on_radar.json')
    result = api.get_radar_forecast()

    _12 = IrmKmiRadarForecast(
        datetime='2024-05-30T18:00:00+02:00',
        native_precipitation=0.89,
        might_rain=True,
        rain_forecast_max=1.12,
        rain_forecast_min=0.50,
        unit='mm/10min'
    )

    _13 = IrmKmiRadarForecast(
        datetime="2024-05-30T18:10:00+02:00",
        native_precipitation=0.83,
        might_rain=True,
        rain_forecast_max=1.09,
        rain_forecast_min=0.64,
        unit='mm/10min'
    )

    assert result[12] == _12
    assert result[13] == _13
