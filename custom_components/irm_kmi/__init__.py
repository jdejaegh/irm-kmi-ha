"""Integration for IRM KMI weather"""

# File inspired from https://github.com/ludeeus/integration_blueprint
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from irm_kmi_api.const import OPTION_STYLE_STD

from .const import (CONF_DARK_MODE, CONF_LANGUAGE_OVERRIDE, CONF_STYLE,
                    CONF_USE_DEPRECATED_FORECAST, CONFIG_FLOW_VERSION, DOMAIN,
                    OPTION_DEPRECATED_FORECAST_NOT_USED, PLATFORMS)
from .coordinator import IrmKmiCoordinator
from .weather import IrmKmiWeather

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator = IrmKmiCoordinator(hass, entry)

    # When integration is set up, set the logging level of the irm_kmi_api package to the same level to help debugging
    logging.getLogger('irm_kmi_api').setLevel(_LOGGER.getEffectiveLevel())
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
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug(f"Migrating from version {config_entry.version}")

    if config_entry.version > CONFIG_FLOW_VERSION - 1:
        # This means the user has downgraded from a future version
        _LOGGER.error(f"Downgrading configuration is not supported: your config version is {config_entry.version}, "
                      f"the current version used by the integration is {CONFIG_FLOW_VERSION}")
        return False

    new = {**config_entry.data}
    if config_entry.version == 1:
        new = new | {CONF_STYLE: OPTION_STYLE_STD, CONF_DARK_MODE: True}
        hass.config_entries.async_update_entry(config_entry, data=new, version=2)

    if config_entry.version == 2:
        new = new | {CONF_USE_DEPRECATED_FORECAST: OPTION_DEPRECATED_FORECAST_NOT_USED}
        hass.config_entries.async_update_entry(config_entry, data=new, version=3)

    if config_entry.version == 3:
        new = new | {CONF_LANGUAGE_OVERRIDE: None}
        hass.config_entries.async_update_entry(config_entry, data=new, version=4)

    if config_entry.version == 4:
        new[CONF_LANGUAGE_OVERRIDE] = 'none' if new[CONF_LANGUAGE_OVERRIDE] is None else new[CONF_LANGUAGE_OVERRIDE]
        hass.config_entries.async_update_entry(config_entry, data=new, version=5)

    _LOGGER.debug(f"Migration to version {config_entry.version} successful")

    return True
