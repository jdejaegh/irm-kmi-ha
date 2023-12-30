"""Tests for the IRM KMI config flow."""

from unittest.mock import MagicMock

from homeassistant.components.zone import ENTITY_ID_HOME
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import async_migrate_entry
from custom_components.irm_kmi.const import (
    CONF_DARK_MODE, CONF_STYLE, CONF_USE_DEPRECATED_FORECAST,
    CONFIG_FLOW_VERSION, DOMAIN, OPTION_DEPRECATED_FORECAST_NOT_USED,
    OPTION_STYLE_STD)


async def test_full_user_flow(
        hass: HomeAssistant,
        mock_setup_entry: MagicMock,
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE: ENTITY_ID_HOME,
                    CONF_STYLE: OPTION_STYLE_STD,
                    CONF_DARK_MODE: False},
    )
    print(result2)
    assert result2.get("type") == FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "test home"
    assert result2.get("data") == {CONF_ZONE: ENTITY_ID_HOME,
                                   CONF_STYLE: OPTION_STYLE_STD,
                                   CONF_DARK_MODE: False,
                                   CONF_USE_DEPRECATED_FORECAST: OPTION_DEPRECATED_FORECAST_NOT_USED}


async def test_config_entry_migration(hass: HomeAssistant) -> None:
    """Ensure that config entry migration takes the configuration to the latest version"""
    entry = MockConfigEntry(
        title="Home",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.home"},
        unique_id="zone.home",
        version=1
    )

    entry.add_to_hass(hass)
    await async_migrate_entry(hass, entry)
    result_entry = hass.config_entries.async_get_entry(entry_id=entry.entry_id)

    assert result_entry.version == CONFIG_FLOW_VERSION
