from datetime import datetime

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator
from custom_components.irm_kmi.binary_sensor import IrmKmiWarning
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
async def test_warning_data(
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
