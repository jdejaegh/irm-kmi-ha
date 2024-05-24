"""Integration for IRM KMI weather"""

# File inspired from https://github.com/ludeeus/integration_blueprint
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import (CONF_DARK_MODE, CONF_LANGUAGE_OVERRIDE, CONF_STYLE,
                    CONF_USE_DEPRECATED_FORECAST, CONFIG_FLOW_VERSION, DOMAIN,
                    OPTION_DEPRECATED_FORECAST_NOT_USED, OPTION_STYLE_STD,
                    PLATFORMS)
from .coordinator import IrmKmiCoordinator
from .weather import IrmKmiWeather

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator = IrmKmiCoordinator(hass, entry)

    try:
        # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryError:
        # This happens when the zone is out of Benelux (no forecast available there)
        # This should be caught by the config flow anyway
        return False

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug(f"Migrating from version {config_entry.version}")

    if config_entry.version > CONFIG_FLOW_VERSION - 1:
        # This means the user has downgraded from a future version
        return False

    new = {**config_entry.data}
    if config_entry.version == 1:
        new = new | {CONF_STYLE: OPTION_STYLE_STD, CONF_DARK_MODE: True}
        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    if config_entry.version == 2:
        new = new | {CONF_USE_DEPRECATED_FORECAST: OPTION_DEPRECATED_FORECAST_NOT_USED}
        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, data=new)

    if config_entry.version == 3:
        new = new | {CONF_LANGUAGE_OVERRIDE: None}
        config_entry.version = 4
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.debug(f"Migration to version {config_entry.version} successful")

    return True
