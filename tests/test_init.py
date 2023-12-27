"""Tests for the IRM KMI integration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ZONE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi.const import DOMAIN


async def test_load_unload_config_entry(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        mock_irm_kmi_api: AsyncMock,
        mock_coordinator: AsyncMock
) -> None:
    """Test the IRM KMI configuration entry loading/unloading."""
    hass.states.async_set(
        "zone.home",
        0,
        {"latitude": 50.738681639, "longitude": 4.054077148},
    )

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.data.get(DOMAIN)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_config_entry_not_ready(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        mock_exception_irm_kmi_api: AsyncMock
) -> None:
    """Test the IRM KMI configuration entry not ready."""
    hass.states.async_set(
        "zone.home",
        0,
        {"latitude": 50.738681639, "longitude": 4.054077148},
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_exception_irm_kmi_api.get_forecasts_coord.call_count == 1
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_config_entry_zone_removed(
        hass: HomeAssistant,
        caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the IRM KMI configuration entry not ready."""
    mock_config_entry = MockConfigEntry(
        title="My Castle",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.castle"},
        unique_id="zone.castle",
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    assert "Zone 'zone.castle' not found" in caplog.text


async def test_zone_out_of_benelux(
        hass: HomeAssistant,
        caplog: pytest.LogCaptureFixture,
        mock_irm_kmi_api_out_benelux: AsyncMock
) -> None:
    """Test the IRM KMI when configuration zone is out of Benelux"""
    mock_config_entry = MockConfigEntry(
        title="London",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.london"},
        unique_id="zone.london",
    )
    hass.states.async_set(
        "zone.london",
        0,
        {"latitude": 51.5072, "longitude": 0.1276},
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    assert "Zone 'zone.london' is out of Benelux" in caplog.text
