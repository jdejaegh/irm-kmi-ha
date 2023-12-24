"""Integration for IRM KMI weather"""

from homeassistant.components.weather import Forecast
class IrmKmiForecast(Forecast):
    """Forecast class with additional attributes for IRM KMI"""
    text_fr: str | None
    text_nl: str | None
