from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.irm_kmi import IrmKmiCoordinator
from custom_components.irm_kmi.pollen import PollenParser
from tests.conftest import get_api_data


def test_svg_pollen_parsing():
    with open("tests/fixtures/pollen.svg", "r") as file:
        svg_data = file.read()
    data = PollenParser(svg_data).get_pollen_data()
    assert data == {'birch': 'purple', 'oak': 'active', 'hazel': 'none', 'mugwort': 'none', 'alder': 'green',
                    'grasses': 'none', 'ash': 'active'}

    with open("tests/fixtures/pollen_two.svg", "r") as file:
        svg_data = file.read()
    data = PollenParser(svg_data).get_pollen_data()
    assert data == {'birch': 'purple', 'oak': 'active', 'hazel': 'none', 'mugwort': 'none', 'alder': 'active',
                    'grasses': 'none', 'ash': 'active'}


def test_pollen_options():
    assert PollenParser.get_option_values() == ['active', 'green', 'yellow', 'orange', 'red', 'purple', 'none']


def test_pollen_default_values():
    assert PollenParser.get_default_data() == {'birch': 'none', 'oak': 'none', 'hazel': 'none', 'mugwort': 'none',
                                               'alder': 'none', 'grasses': 'none', 'ash': 'none'}


async def test_pollen_data_from_api(
        hass: HomeAssistant,
        mock_svg_pollen: AsyncMock,
        mock_config_entry: MockConfigEntry
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    api_data = get_api_data("be_forecast_warning.json")

    result = await coordinator._async_pollen_data(api_data)
    expected = {'mugwort': 'none', 'birch': 'purple', 'alder': 'green', 'ash': 'active', 'oak': 'active',
                'grasses': 'none', 'hazel': 'none'}
    assert result == expected


async def test_pollen_error_leads_to_default_values(
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        mock_exception_irm_kmi_api_svg_pollen: AsyncMock
) -> None:
    coordinator = IrmKmiCoordinator(hass, mock_config_entry)
    api_data = get_api_data("be_forecast_warning.json")

    result = await coordinator._async_pollen_data(api_data)
    expected = PollenParser.get_default_data()
    assert result == expected
