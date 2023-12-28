"""Fixtures for the IRM KMI integration tests."""
from __future__ import annotations

import json
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_ZONE
from pytest_homeassistant_custom_component.common import (MockConfigEntry,
                                                          load_fixture)

from custom_components.irm_kmi.api import IrmKmiApiParametersError
from custom_components.irm_kmi.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Home",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.home"},
        unique_id="zone.home",
    )


@pytest.fixture
def mock_setup_entry() -> Generator[None, None, None]:
    """Mock setting up a config entry."""
    with patch(
            "custom_components.irm_kmi.async_setup_entry", return_value=True
    ):
        yield


@pytest.fixture()
def mock_irm_kmi_api(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    fixture: str = "forecast.json"

    forecast = json.loads(load_fixture(fixture))
    with patch(
            "custom_components.irm_kmi.coordinator.IrmKmiApiClient", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_forecasts_coord.return_value = forecast
        yield irm_kmi


@pytest.fixture()
def mock_irm_kmi_api_out_benelux(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    fixture: str = "forecast_out_of_benelux.json"

    forecast = json.loads(load_fixture(fixture))
    print(type(forecast))
    with patch(
            "custom_components.irm_kmi.coordinator.IrmKmiApiClient", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_forecasts_coord.return_value = forecast
        yield irm_kmi


@pytest.fixture()
def mock_exception_irm_kmi_api(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""
    with patch(
            "custom_components.irm_kmi.coordinator.IrmKmiApiClient", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_forecasts_coord.side_effect = IrmKmiApiParametersError
        yield irm_kmi


@pytest.fixture()
def mock_image_irm_kmi_api(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked IrmKmi api client."""

    async def patched(url: str, params: dict | None = None) -> bytes:
        if "cdn.knmi.nl" in url:
            file_name = "tests/fixtures/clouds_nl.png"
        elif "app.meteo.be/services/appv4/?s=getIncaImage" in url:
            file_name = "tests/fixtures/clouds_be.png"
        elif "getLocalizationLayerBE" in url:
            file_name = "tests/fixtures/loc_layer_be_n.png"
        elif "getLocalizationLayerNL" in url:
            file_name = "tests/fixtures/loc_layer_nl_d.png"
        else:
            raise ValueError("Not a valid parameter for the mock")

        with open(file_name, "rb") as file:
            return file.read()

    with patch(
            "custom_components.irm_kmi.coordinator.IrmKmiApiClient", autospec=True
    ) as irm_kmi_api_mock:
        irm_kmi = irm_kmi_api_mock.return_value
        irm_kmi.get_image.side_effect = patched
        yield irm_kmi


@pytest.fixture()
def mock_coordinator(request: pytest.FixtureRequest) -> Generator[None, MagicMock, None]:
    """Return a mocked coordinator."""
    with patch(
            "custom_components.irm_kmi.IrmKmiCoordinator", autospec=True
    ) as coordinator_mock:
        coord = coordinator_mock.return_value
        coord._async_animation_data.return_value = {'animation': None}
        yield coord
