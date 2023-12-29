import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

_LOGGER = logging.getLogger(__name__)


def disable_from_config(hass: HomeAssistant, config_entry: ConfigEntry):
    modify_from_config(hass, config_entry, False)


def enable_from_config(hass: HomeAssistant, config_entry: ConfigEntry):
    modify_from_config(hass, config_entry, True)


def modify_from_config(hass: HomeAssistant, config_entry: ConfigEntry, enable: bool):
    dr = device_registry.async_get(hass)
    devices = device_registry.async_entries_for_config_entry(dr, config_entry.entry_id)
    _LOGGER.info(f"Trying to {'enable' if enable else 'disable'} {config_entry.entry_id}: {len(devices)} device(s)")
    for device in devices:
        _LOGGER.info(f"Disabling device {device.name} because it is out of Benelux")
        dr.async_update_device(device_id=device.id,
                               disabled_by=None if enable else device_registry.DeviceEntryDisabler.INTEGRATION)
