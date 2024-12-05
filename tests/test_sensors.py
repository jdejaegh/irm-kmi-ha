from datetime import datetime

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator
from custom_components.irm_kmi.binary_sensor import IrmKmiWarning
from custom_components.irm_kmi.const import CONF_LANGUAGE_OVERRIDE
from custom_components.irm_kmi.sensor import (IrmKmiNextSunMove,
                                              IrmKmiNextWarning)
from tests.conftest import get_api_data


@freeze_time(datetime.fromisoformat('2024-01-12T07:55:00+01:00'))
async def test_warning_data(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("be_forecast_warning.json")
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = coordinator.warnings_from_data(api_data.get('for', {}).get('warning'))

    coordinator.data = {'warnings': result}
    warning = IrmKmiWarning(coordinator, mock_config_entry)
    warning.hass = hass

    assert warning.is_on
    assert len(warning.extra_state_attributes['warnings']) == 2

    for w in warning.extra_state_attributes['warnings']:
        assert w['is_active']

    assert warning.extra_state_attributes['active_warnings_friendly_names'] == "Fog, Ice or snow"


@freeze_time(datetime.fromisoformat('2024-01-12T07:55:00+01:00'))
async def test_warning_data_unknown_lang(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    # When language is unknown, default to english setting
    hass.config.language = "foo"

    api_data = get_api_data("be_forecast_warning.json")
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = coordinator.warnings_from_data(api_data.get('for', {}).get('warning'))

    coordinator.data = {'warnings': result}
    warning = IrmKmiWarning(coordinator, mock_config_entry)
    warning.hass = hass

    assert warning.is_on
    assert len(warning.extra_state_attributes['warnings']) == 2

    for w in warning.extra_state_attributes['warnings']:
        assert w['is_active']

    assert warning.extra_state_attributes['active_warnings_friendly_names'] == "Fog, Ice or snow"


@freeze_time(datetime.fromisoformat('2024-01-11T20:00:00+01:00'))
async def test_next_warning_when_data_available(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("be_forecast_warning.json")
    await hass.config_entries.async_add(mock_config_entry)
    hass.config_entries.async_update_entry(mock_config_entry, data=mock_config_entry.data | {CONF_LANGUAGE_OVERRIDE: 'de'})

    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = coordinator.warnings_from_data(api_data.get('for', {}).get('warning'))

    coordinator.data = {'warnings': result}
    warning = IrmKmiNextWarning(coordinator, mock_config_entry)
    warning.hass = hass

    # This somehow fixes the following error that popped since 2024.12.0
    # ValueError: Entity <class 'custom_components.irm_kmi.sensor.IrmKmiNextWarning'> cannot have a translation key for
    # unit of measurement before being added to the entity platform
    warning._attr_translation_key = None

    assert warning.state == "2024-01-12T06:00:00+00:00"
    assert len(warning.extra_state_attributes['next_warnings']) == 2

    assert warning.extra_state_attributes['next_warnings_friendly_names'] == "Nebel, Glätte"


@freeze_time(datetime.fromisoformat('2024-01-12T07:30:00+01:00'))
async def test_next_warning_none_when_only_active_warnings(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("be_forecast_warning.json")
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = coordinator.warnings_from_data(api_data.get('for', {}).get('warning'))

    coordinator.data = {'warnings': result}
    warning = IrmKmiNextWarning(coordinator, mock_config_entry)
    warning.hass = hass

    # This somehow fixes the following error that popped since 2024.12.0
    # ValueError: Entity <class 'custom_components.irm_kmi.sensor.IrmKmiNextWarning'> cannot have a translation key for
    # unit of measurement before being added to the entity platform
    warning._attr_translation_key = None

    assert warning.state is None
    assert len(warning.extra_state_attributes['next_warnings']) == 0

    assert warning.extra_state_attributes['next_warnings_friendly_names'] == ""


@freeze_time(datetime.fromisoformat('2024-01-12T07:30:00+01:00'))
async def test_next_warning_none_when_no_warnings(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    coordinator.data = {'warnings': []}
    warning = IrmKmiNextWarning(coordinator, mock_config_entry)
    warning.hass = hass

    # This somehow fixes the following error that popped since 2024.12.0
    # ValueError: Entity <class 'custom_components.irm_kmi.sensor.IrmKmiNextWarning'> cannot have a translation key for
    # unit of measurement before being added to the entity platform
    warning._attr_translation_key = None

    assert warning.state is None
    assert len(warning.extra_state_attributes['next_warnings']) == 0

    assert warning.extra_state_attributes['next_warnings_friendly_names'] == ""

    coordinator.data = dict()
    warning = IrmKmiNextWarning(coordinator, mock_config_entry)
    warning.hass = hass

    # This somehow fixes the following error that popped since 2024.12.0
    # ValueError: Entity <class 'custom_components.irm_kmi.sensor.IrmKmiNextWarning'> cannot have a translation key for
    # unit of measurement before being added to the entity platform
    warning._attr_translation_key = None

    assert warning.state is None
    assert len(warning.extra_state_attributes['next_warnings']) == 0

    assert warning.extra_state_attributes['next_warnings_friendly_names'] == ""


@freeze_time(datetime.fromisoformat('2023-12-26T18:30:00+01:00'))
async def test_next_sunrise_sunset(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("forecast.json")

    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = await coordinator.daily_list_to_forecast(api_data.get('for', {}).get('daily'))

    coordinator.data = {'daily_forecast': result}

    sunset = IrmKmiNextSunMove(coordinator, mock_config_entry, 'sunset')
    sunrise = IrmKmiNextSunMove(coordinator, mock_config_entry, 'sunrise')

    # This somehow fixes the following error that popped since 2024.12.0
    # ValueError: Entity <class 'custom_components.irm_kmi.sensor.IrmKmiNextSunMove'> cannot have a translation key for
    # unit of measurement before being added to the entity platform
    sunrise._attr_translation_key = None
    sunset._attr_translation_key = None

    assert datetime.fromisoformat(sunrise.state) == datetime.fromisoformat('2023-12-27T08:44:00+01:00')
    assert datetime.fromisoformat(sunset.state) == datetime.fromisoformat('2023-12-27T16:43:00+01:00')


@freeze_time(datetime.fromisoformat('2023-12-26T15:30:00+01:00'))
async def test_next_sunrise_sunset_bis(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry
) -> None:
    api_data = get_api_data("forecast.json")

    coordinator = IrmKmiCoordinator(hass, mock_config_entry)

    result = await coordinator.daily_list_to_forecast(api_data.get('for', {}).get('daily'))

    coordinator.data = {'daily_forecast': result}

    sunset = IrmKmiNextSunMove(coordinator, mock_config_entry, 'sunset')
    sunrise = IrmKmiNextSunMove(coordinator, mock_config_entry, 'sunrise')

    # This somehow fixes the following error that popped since 2024.12.0
    # ValueError: Entity <class 'custom_components.irm_kmi.sensor.IrmKmiNextSunMove'> cannot have a translation key for
    # unit of measurement before being added to the entity platform
    sunrise._attr_translation_key = None
    sunset._attr_translation_key = None

    assert datetime.fromisoformat(sunrise.state) == datetime.fromisoformat('2023-12-27T08:44:00+01:00')
    assert datetime.fromisoformat(sunset.state) == datetime.fromisoformat('2023-12-26T16:42:00+01:00')
