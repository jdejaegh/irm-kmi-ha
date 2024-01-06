import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

_LOGGER = logging.getLogger(__name__)


def disable_from_config(hass: HomeAssistant, config_entry: ConfigEntry):
    modify_from_config(hass, config_entry.entry_id, False)


def enable_from_config(hass: HomeAssistant, config_entry: ConfigEntry):
    modify_from_config(hass, config_entry.entry_id, True)


def modify_from_config(hass: HomeAssistant, config_entry_id: str, enable: bool):
    dr = device_registry.async_get(hass)
    devices = device_registry.async_entries_for_config_entry(dr, config_entry_id)
    _LOGGER.info(f"Trying to {'enable' if enable else 'disable'} {config_entry_id}: {len(devices)} device(s)")
    for device in devices:
        dr.async_update_device(device_id=device.id,
                               disabled_by=None if enable else device_registry.DeviceEntryDisabler.INTEGRATION)


def get_config_value(config_entry: ConfigEntry, key: str) -> Any:
    if config_entry.options and key in config_entry.options:
        return config_entry.options[key]
    return config_entry.data[key]
