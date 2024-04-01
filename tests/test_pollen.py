from custom_components.irm_kmi.pollen import PollenParser


def test_svg_pollen_parsing():
    # TODO make it an actual test
    with open("tests/fixtures/pollen.svg", "r") as file:
        svg_data = file.read()
    PollenParser(svg_data).get_pollen_data()
