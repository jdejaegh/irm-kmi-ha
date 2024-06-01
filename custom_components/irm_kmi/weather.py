"""Support for IRM KMI weather."""
import logging
from datetime import datetime
from typing import List

import voluptuous as vol
from homeassistant.components.weather import (Forecast, WeatherEntity,
                                              WeatherEntityFeature)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (UnitOfPrecipitationDepth, UnitOfPressure,
                                 UnitOfSpeed, UnitOfTemperature)
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt

from . import CONF_USE_DEPRECATED_FORECAST, DOMAIN
from .const import (OPTION_DEPRECATED_FORECAST_DAILY,
                    OPTION_DEPRECATED_FORECAST_HOURLY,
                    OPTION_DEPRECATED_FORECAST_NOT_USED,
                    OPTION_DEPRECATED_FORECAST_TWICE_DAILY)
from .coordinator import IrmKmiCoordinator
from .utils import get_config_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the weather entry."""
    add_services()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IrmKmiWeather(coordinator, entry)])


def add_services() -> None:
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        "get_forecasts_radar",
        cv.make_entity_service_schema({
            vol.Optional("include_past_forecasts"): vol.Boolean()
        }),
        IrmKmiWeather.get_forecasts_radar_service.__name__,
        supports_response=SupportsResponse.ONLY
    )


class IrmKmiWeather(CoordinatorEntity, WeatherEntity):
    _attr_attribution = "Weather data from the Royal Meteorological Institute of Belgium meteo.be"

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry
                 ) -> None:
        super().__init__(coordinator)
        WeatherEntity.__init__(self)
        self._name = entry.title
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = coordinator.shared_device_info
        self._deprecated_forecast_as = get_config_value(entry, CONF_USE_DEPRECATED_FORECAST)

        if self._deprecated_forecast_as != OPTION_DEPRECATED_FORECAST_NOT_USED:
            _LOGGER.warning(f"You are using the forecast attribute for {entry.title} weather. Home Assistant deleted "
                            f"that attribute in 2024.4. Consider using the service weather.get_forecasts instead "
                            f"as the attribute will be delete from this integration in a future release.")

    @property
    def supported_features(self) -> WeatherEntityFeature:
        features = WeatherEntityFeature(0)
        features |= WeatherEntityFeature.FORECAST_DAILY
        features |= WeatherEntityFeature.FORECAST_TWICE_DAILY
        features |= WeatherEntityFeature.FORECAST_HOURLY
        return features

    @property
    def name(self) -> str:
        return self._name

    @property
    def condition(self) -> str | None:
        return self.coordinator.data.get('current_weather', {}).get('condition')

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('temperature')

    @property
    def native_temperature_unit(self) -> str | None:
        return UnitOfTemperature.CELSIUS

    @property
    def native_wind_speed_unit(self) -> str | None:
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('wind_speed')

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('wind_gust_speed')

    @property
    def wind_bearing(self) -> float | str | None:
        return self.coordinator.data.get('current_weather', {}).get('wind_bearing')

    @property
    def native_precipitation_unit(self) -> str | None:
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('pressure')

    @property
    def native_pressure_unit(self) -> str | None:
        return UnitOfPressure.HPA

    @property
    def uv_index(self) -> float | None:
        return self.coordinator.data.get('current_weather', {}).get('uv_index')

    async def async_forecast_twice_daily(self) -> List[Forecast] | None:
        return self.coordinator.data.get('daily_forecast')

    async def async_forecast_daily(self) -> list[Forecast] | None:
        return self.daily_forecast()

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        return self.coordinator.data.get('hourly_forecast')

    def daily_forecast(self) -> list[Forecast] | None:
        data: list[Forecast] = self.coordinator.data.get('daily_forecast')
        if not isinstance(data, list):
            return None
        if len(data) > 1 and not data[0].get('is_daytime') and data[1].get('native_templow') is None:
            data[1]['native_templow'] = data[0].get('native_templow')
            if data[1]['native_templow'] > data[1]['native_temperature']:
                (data[1]['native_templow'], data[1]['native_temperature']) = \
                    (data[1]['native_temperature'], data[1]['native_templow'])

        if len(data) > 0 and not data[0].get('is_daytime'):
            return data
        if len(data) > 1 and data[0].get('native_templow') is None and not data[1].get('is_daytime'):
            data[0]['native_templow'] = data[1].get('native_templow')
            if data[0]['native_templow'] > data[0]['native_temperature']:
                (data[0]['native_templow'], data[0]['native_temperature']) = \
                    (data[0]['native_temperature'], data[0]['native_templow'])

        return [f for f in data if f.get('is_daytime')]

    def get_forecasts_radar_service(self, include_past_forecasts: bool = False) -> List[Forecast] | None:
        """
        Forecast service based on data from the radar.  Only contains datetime and precipitation amount.
        The result always include the current 10 minutes interval, even if include_past_forecast is false.
        :param include_past_forecasts: whether to include data points that are in the past
        :return: ordered list of forecasts
        """
        now = dt.now()
        now = now.replace(minute=(now.minute // 10) * 10, second=0, microsecond=0)

        # TODO adapt the return value to match the weather.get_forecasts in next breaking change release
        #  return { 'forecast': [...] }
        return [f for f in self.coordinator.data.get('radar_forecast')
                if include_past_forecasts or datetime.fromisoformat(f.get('datetime')) >= now]

    @property
    def extra_state_attributes(self) -> dict:
        """Here to keep the DEPRECATED forecast attribute.
        This attribute is deprecated by Home Assistant by still implemented for compatibility
        with older components.  Newer components should use the service weather.get_forecasts instead.
        """
        data: List[Forecast] = list()
        if self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_NOT_USED:
            return {}
        elif self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_HOURLY:
            data = self.coordinator.data.get('hourly_forecast')
        elif self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_DAILY:
            data = self.daily_forecast()
        elif self._deprecated_forecast_as == OPTION_DEPRECATED_FORECAST_TWICE_DAILY:
            data = self.coordinator.data.get('daily_forecast')

        for forecast in data:
            for k in list(forecast.keys()):
                if k.startswith('native_'):
                    forecast[k[7:]] = forecast[k]

        return {'forecast': data}
