"""Fixtures for the IRM KMI integration tests."""
from __future__ import annotations

import json
from typing import Generator
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from homeassistant.const import CONF_ZONE
from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture

from custom_components.irm_kmi import OPTION_STYLE_STD
from custom_components.irm_kmi.const import (CONF_DARK_MODE, CONF_LANGUAGE_OVERRIDE, CONF_STYLE,
                                             CONF_USE_DEPRECATED_FORECAST, DOMAIN, OPTION_DEPRECATED_FORECAST_NOT_USED,
                                             OPTION_DEPRECATED_FORECAST_TWICE_DAILY, IRM_KMI_TO_HA_CONDITION_MAP)
from custom_components.irm_kmi.data import ProcessedCoordinatorData
from custom_components.irm_kmi.irm_kmi_api.api import IrmKmiApiError, IrmKmiApiParametersError, IrmKmiApiClientHa


def get_api_data(fixture: str) -> dict:
    return json.loads(load_fixture(fixture))


def get_api_with_data(fixture: str) -> IrmKmiApiClientHa:
    api = IrmKmiApiClientHa(session=MagicMock(), user_agent='', cdt_map=IRM_KMI_TO_HA_CONDITION_MAP)
    api._api_data = get_api_data(fixture)
    return api


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Home",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.home",
              CONF_STYLE: OPTION_STYLE_STD,
              CONF_DARK_MODE: True,
              CONF_USE_DEPRECATED_FORECAST: OPTION_DEPRECATED_FORECAST_NOT_USED,
              CONF_LANGUAGE_OVERRIDE: 'none'},
        unique_id="zone.home",
    )


@pytest.fixture
def mock_config_entry_with_deprecated() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Home",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.home",
              CONF_STYLE: OPTION_STYLE_STD,
              CONF_DARK_MODE: True,
              CONF_USE_DEPRECATED_FORECAST: OPTION_DEPRECATED_FORECAST_TWICE_DAILY,
              CONF_LANGUAGE_OVERRIDE: 'none'},
        unique_id="zone.home",
    )


@pytest.fixture
def mock_setup_entry() -> Generator[None, None, None]:
    """Mock setting up a config entry."""
    with patch(
            "custom_components.irm_kmi.async_setup_entry", return_value=True
    ):
        yield


@pytest.fixture
def mock_get_forecast_in_benelux():
    """Mock a call to IrmKmiApiClient.get_forecasts_coord() so that it returns something valid and in the Benelux"""
    with patch("custom_components.irm_kmi.config_flow.IrmKmiApiClient.get_forecasts_coord",
               return_value={'cityName': 'Brussels'}):
        yield


@pytest.fixture
def mock_get_forecast_out_benelux():
    """Mock a call to IrmKmiApiClient.get_forecasts_coord() so that it returns something outside Benelux"""
    with patch("custom_components.irm_kmi.config_flow.IrmKmiApiClient.get_forecasts_coord",
               return_value={'cityName': "Outside the Benelux (Brussels)"}):
        yield


@pytest.fixture
def mock_get_forecast_api_error():
    """Mock a call to IrmKmiApiClient.get_forecasts_coord() so that it raises an error"""
    with patch("custom_components.irm_kmi.config_flow.IrmKmiApiClient.get_forecasts_coord",
               side_effet=IrmKmiApiError):
        return


@pytest.fixture
def mock_get_forecast_api_error_repair():
    """Mock a call to IrmKmiApiClient.get_forecasts_coord() so that it raises an error"""
    with patch("custom_components.irm_kmi.repairs.IrmKmiApiClient.get_forecasts_coord",
               side_effet=IrmKmiApiError):
        return


@pytest.fixture()
def mock_irm_kmi_api(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    fixture: str = "forecast.json"

    forecast = json.loads(load_fixture(fixture))
    with patch(
            "custom_components.irm_kmi.coordinator.IrmKmiApiClientHa", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_forecasts_coord.return_value = forecast
        yield irm_kmi


@pytest.fixture()
def mock_irm_kmi_api_repair_in_benelux(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    fixture: str = "forecast.json"

    forecast = json.loads(load_fixture(fixture))
    with patch(
            "custom_components.irm_kmi.repairs.IrmKmiApiClient", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_forecasts_coord.return_value = forecast
        yield irm_kmi


@pytest.fixture()
def mock_irm_kmi_api_repair_out_of_benelux(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    fixture: str = "forecast_out_of_benelux.json"

    forecast = json.loads(load_fixture(fixture))
    with patch(
            "custom_components.irm_kmi.repairs.IrmKmiApiClient", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_forecasts_coord.return_value = forecast
        yield irm_kmi


@pytest.fixture()
def mock_exception_irm_kmi_api(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    with patch(
            "custom_components.irm_kmi.coordinator.IrmKmiApiClientHa", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.refresh_forecasts_coord.side_effect = IrmKmiApiParametersError
        yield irm_kmi

