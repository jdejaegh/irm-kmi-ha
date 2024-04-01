from custom_components.irm_kmi.pollen import PollenParser


def test_svg_pollen_parsing():
    with open("tests/fixtures/pollen.svg", "r") as file:
        svg_data = file.read()
    data = PollenParser(svg_data).get_pollen_data()
    assert data == {'birch': 'purple', 'oak': 'active', 'hazel': 'none', 'mugwort': 'none', 'alder': 'green',
                    'grasses': 'none', 'ash': 'active'}


def test_pollen_options():
    assert PollenParser.get_option_values() == ['active', 'green', 'yellow', 'orange', 'red', 'purple', 'none']


def test_pollen_default_values():
    assert PollenParser.get_default_data() == {'birch': 'none', 'oak': 'none', 'hazel': 'none', 'mugwort': 'none',
                                               'alder': 'none', 'grasses': 'none', 'ash': 'none'}
