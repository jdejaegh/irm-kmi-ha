"""Parse pollen info from SVG from IRM KMI api"""
import logging
import xml.etree.ElementTree as ET
from typing import List

from custom_components.irm_kmi.const import POLLEN_NAMES

_LOGGER = logging.getLogger(__name__)


class PollenParser:
    """
    The SVG looks as follows (see test fixture for a real example)

    Active pollens
    ---------------------------------
    Oak                        active
    Ash                        active
    ---------------------------------
    Birch         ---|---|---|---|-*-
    Alder         -*-|---|---|---|---

    This classe parses the oak and ash as active, birch as purple and alder as green in the example.
    For active pollen, check if an active text is present on the same line as the pollen name
    For the color scale, look for a white dot (nearly) at the same level as the pollen name.  From the white dot
    horizontal position, determine the level
    """
    def __init__(
            self,
            xml_string: str
    ):
        self._xml = xml_string

    @staticmethod
    def _validate_svg(elements: List[ET.Element]) -> bool:
        """Make sure that the colors of the scale are still where we expect them"""
        x_values = {"rectgreen": 80,
                    "rectyellow": 95,
                    "rectorange": 110,
                    "rectred": 125,
                    "rectpurple": 140}
        for e in elements:
            if e.attrib.get('id', '') in x_values.keys():
                try:
                    if float(e.attrib.get('x', '0')) != x_values.get(e.attrib.get('id')):
                        return False
                except ValueError:
                    return False
        return True

    @staticmethod
    def get_default_data() -> dict:
        """Return all the known pollen with 'none' value"""
        return {k.lower(): 'none' for k in POLLEN_NAMES}

    @staticmethod
    def get_option_values() -> List[str]:
        """List all the values that the pollen can have"""
        return ['active', 'green', 'yellow', 'orange', 'red', 'purple', 'none']

    @staticmethod
    def _extract_elements(root) -> List[ET.Element]:
        """Recursively collect all elements of the SVG in a list"""
        elements = []
        for child in root:
            elements.append(child)
            elements.extend(PollenParser._extract_elements(child))
        return elements

    @staticmethod
    def _dot_to_color_value(dot: ET.Element) -> str:
        """Map the dot horizontal position to a color or 'none'"""
        try:
            cx = float(dot.attrib.get('cx'))
        except ValueError:
            return 'none'

        if cx > 155:
            return 'none'
        elif cx > 140:
            return 'purple'
        elif cx > 125:
            return 'red'
        elif cx > 110:
            return 'orange'
        elif cx > 95:
            return 'yellow'
        elif cx > 80:
            return 'green'
        else:
            return 'none'

    def get_pollen_data(self) -> dict:
        """From the XML string, parse the SVG and extract the pollen data from the image.
        If an error occurs, return the default value"""
        pollen_data = self.get_default_data()
        try:
            _LOGGER.debug(f"Full SVG: {self._xml}")
            root = ET.fromstring(self._xml)
        except ET.ParseError:
            _LOGGER.warning("Could not parse SVG pollen XML")
            return pollen_data

        elements: List[ET.Element] = self._extract_elements(root)

        if not self._validate_svg(elements):
            _LOGGER.warning("Could not validate SVG pollen data")
            return pollen_data

        pollens = [e for e in elements if 'tspan' in e.tag and e.text in POLLEN_NAMES]
        active = [e for e in elements if 'tspan' in e.tag and e.text == 'active']
        dots = [e for e in elements if 'ellipse' in e.tag
                and 'fill:#ffffff' in e.attrib.get('style', '')
                and 3 == float(e.attrib.get('rx', '0'))]

        for pollen in pollens:
            try:
                y = float(pollen.attrib.get('y'))
                if y in [float(e.attrib.get('y')) for e in active]:
                    pollen_data[pollen.text.lower()] = 'active'
                else:
                    dot = [d for d in dots if y - 3 <= float(d.attrib.get('cy', '0')) <= y + 3]
                    if len(dot) == 1:
                        dot = dot[0]
                        pollen_data[pollen.text.lower()] = self._dot_to_color_value(dot)
            except ValueError | NameError:
                _LOGGER.warning("Skipped some data in the pollen SVG")

        _LOGGER.debug(f"Pollen data: {pollen_data}")
        return pollen_data

