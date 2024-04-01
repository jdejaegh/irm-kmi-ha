import logging
import xml.etree.ElementTree as ET
from typing import List

from custom_components.irm_kmi.const import POLLEN_NAMES

_LOGGER = logging.getLogger(__name__)


class PollenParser:
    def __init__(
            self,
            xml_string: str
    ):
        self._xml = xml_string

    @staticmethod
    def _validate_svg(elements: List[ET.Element]) -> bool:
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
    def extract_elements(root) -> List[ET.Element]:
        elements = []
        for child in root:
            elements.append(child)
            elements.extend(PollenParser.extract_elements(child))
        return elements

    @staticmethod
    def dot_to_color_value(dot: ET.Element) -> str | None:

        try:
            cx = float(dot.attrib.get('cx'))
        except ValueError:
            return None

        if cx > 155:
            return None
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
            return None

    def get_pollen_data(self):
        try:
            root = ET.fromstring("self._xml")
        except ET.ParseError:
            # TODO Handle with default case
            return None

        elements: List[ET.Element] = self.extract_elements(root)

        if not self._validate_svg(elements):
            # TODO return default value
            return None

        pollens = [e for e in elements if 'tspan' in e.tag and e.text in POLLEN_NAMES]
        active = [e for e in elements if 'tspan' in e.tag and e.text == 'active']
        dots = [e for e in elements if 'ellipse' in e.tag
                and 'fill:#ffffff' in e.attrib.get('style', '')
                and 3 == float(e.attrib.get('rx', '0'))]

        pollen_data = {k: None for k in POLLEN_NAMES}

        for pollen in pollens:
            try:
                y = float(pollen.attrib.get('y'))
                if y in [float(e.attrib.get('y')) for e in active]:
                    pollen_data[pollen.text] = 'active'
                else:
                    dot = [d for d in dots if y - 3 <= float(d.attrib.get('cy', '0')) <= y + 3]
                    if len(dot) == 1:
                        dot = dot[0]
                        pollen_data[pollen.text] = self.dot_to_color_value(dot)
            except ValueError | NameError:
                pass

        print(pollen_data)
        for e in pollens + active:
            print(e.text)
        for d in dots:
            print(d.attrib)
