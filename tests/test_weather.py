import os
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock

from freezegun import freeze_time
from homeassistant.components.weather import Forecast
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator, IrmKmiWeather


@freeze_time(datetime.fromisoformat("2023-12-28T15:30:00+01:00"))
async def test_weather_nl(
        hass: HomeAssistant,
        mock_image_and_nl_forecast_irm_kmi_api: AsyncMock,
        mock_config_entry: MockConfigEntry
) -> None:
    hass.states.async_set(
        "zone.home",
        0,
        {"latitude": 50.738681639, "longitude": 4.054077148},
    )
    hass.config.config_dir = os.getcwd()

    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    await coordinator.async_config_entry_first_refresh()

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
        mock_image_and_high_temp_irm_kmi_api: AsyncMock,
        mock_config_entry: MockConfigEntry
) -> None:
    # Test case for https://github.com/jdejaegh/irm-kmi-ha/issues/8
    hass.states.async_set(
        "zone.home",
        0,
        {"latitude": 50.738681639, "longitude": 4.054077148},
    )
    hass.config.config_dir = os.getcwd()

    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    await coordinator.async_config_entry_first_refresh()

    weather = IrmKmiWeather(coordinator, mock_config_entry)
    result: List[Forecast] = await weather.async_forecast_daily()

    for f in result:
        if f['native_temperature'] is not None and f['native_templow'] is not None:
            assert f['native_temperature'] >= f['native_templow']

    result: List[Forecast] = await weather.async_forecast_twice_daily()

    for f in result:
        if f['native_temperature'] is not None and f['native_templow'] is not None:
            assert f['native_temperature'] >= f['native_templow']
