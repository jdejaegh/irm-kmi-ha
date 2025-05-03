from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from irm_kmi_api.api import IrmKmiApiError
from irm_kmi_api.pollen import PollenParser
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator
from tests.conftest import get_api_with_data


async def test_pollen_error_leads_to_unavailable_on_first_call(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    api = get_api_with_data("be_forecast_warning.json")

    api.get_svg = AsyncMock()
    api.get_svg.side_effect = IrmKmiApiError

    coordinator._api = api

    result = await coordinator.process_api_data()
    expected = PollenParser.get_unavailable_data()
    assert result['pollen'] == expected
