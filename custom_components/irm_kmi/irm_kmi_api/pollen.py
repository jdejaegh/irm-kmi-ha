"""Parse pollen info from SVG from IRM KMI api"""
import logging
import xml.etree.ElementTree as ET
from typing import List

from .const import POLLEN_NAMES, POLLEN_LEVEL_TO_COLOR

_LOGGER = logging.getLogger(__name__)


class PollenParser:
    """
    Extract pollen level from an SVG provided by the IRM KMI API.
    To get the data, match pollen names and pollen levels that are vertically aligned or the dot on the color scale.
    Then, map the value to the corresponding color on the scale.
    """

    def __init__(
            self,
            xml_string: str
    ):
        self._xml = xml_string

    @staticmethod
    def get_default_data() -> dict:
        """Return all the known pollen with 'none' value"""
        return {k.lower(): 'none' for k in POLLEN_NAMES}

    @staticmethod
    def get_unavailable_data() -> dict:
        """Return all the known pollen with 'none' value"""
        return {k.lower(): None for k in POLLEN_NAMES}

    @staticmethod
    def get_option_values() -> List[str]:
        """List all the values that the pollen can have"""
        return list(POLLEN_LEVEL_TO_COLOR.values()) + ['none']

    @staticmethod
    def _extract_elements(root) -> List[ET.Element]:
        """Recursively collect all elements of the SVG in a list"""
        elements = []
        for child in root:
            elements.append(child)
            elements.extend(PollenParser._extract_elements(child))
        return elements

    @staticmethod
    def _get_elem_text(e) -> str | None:
        if e.text is not None:
            return e.text.strip()
        return None

    def get_pollen_data(self) -> dict:
        """From the XML string, parse the SVG and extract the pollen data from the image.
        If an error occurs, return the default value"""
        pollen_data = self.get_default_data()
        try:
            _LOGGER.debug(f"Full SVG: {self._xml}")
            root = ET.fromstring(self._xml)
        except ET.ParseError as e:
            _LOGGER.warning(f"Could not parse SVG pollen XML: {e}")
            return pollen_data

        elements: List[ET.Element] = self._extract_elements(root)

        pollens = {e.attrib.get('x', None): self._get_elem_text(e).lower()
                   for e in elements if 'tspan' in e.tag and self._get_elem_text(e) in POLLEN_NAMES}

        pollen_levels = {e.attrib.get('x', None): POLLEN_LEVEL_TO_COLOR[self._get_elem_text(e)]
                         for e in elements if 'tspan' in e.tag and self._get_elem_text(e) in POLLEN_LEVEL_TO_COLOR}

        level_dots = {e.attrib.get('cx', None) for e in elements if 'circle' in e.tag}

        # For each pollen name found, check the text just below.
        # As of January 2025, the text is always 'active' and the dot shows the real level
        # If text says 'active', check the dot; else trust the text
        for position, pollen in pollens.items():
            # Determine pollen level based on text
            if position is not None and position in pollen_levels:
                pollen_data[pollen] = pollen_levels[position]
                _LOGGER.debug(f"{pollen} is {pollen_data[pollen]} according to text")

            # If text is 'active' or if there is no text, check the dot as a fallback
            if pollen_data[pollen] not in {'none', 'active'}:
                _LOGGER.debug(f"{pollen} trusting text")
            else:
                for dot in level_dots:
                    try:
                        relative_x_position = float(position) - float(dot)
                    except TypeError:
                        pass
                    else:
                        if 24 <= relative_x_position <= 34:
                            pollen_data[pollen] = 'green'
                        elif 13 <= relative_x_position <= 23:
                            pollen_data[pollen] = 'yellow'
                        elif -5 <= relative_x_position <= 5:
                            pollen_data[pollen] = 'orange'
                        elif -23 <= relative_x_position <= -13:
                            pollen_data[pollen] = 'red'
                        elif -34 <= relative_x_position <= -24:
                            pollen_data[pollen] = 'purple'

                _LOGGER.debug(f"{pollen} is {pollen_data[pollen]} according to dot")

        _LOGGER.debug(f"Pollen data: {pollen_data}")
        return pollen_data
