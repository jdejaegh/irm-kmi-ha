from homeassistant.components.weather import Forecast


class IrmKmiForecast(Forecast):
    """Forecast class with additional attributes for IRM KMI"""

    # TODO: add condition_2 as well and evolution to match data from the API?
    text_fr: str | None
    text_nl: str | None
