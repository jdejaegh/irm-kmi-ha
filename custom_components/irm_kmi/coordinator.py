"""DataUpdateCoordinator for the IRM KMI integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator, UpdateFailed)
from homeassistant.util import dt
from homeassistant.util.dt import utcnow
from irm_kmi_api import IrmKmiApiClientHa, IrmKmiApiError, PollenParser, RainGraph, RadarStyle

from .const import CONF_DARK_MODE, CONF_STYLE, DOMAIN, IRM_KMI_NAME
from .const import IRM_KMI_TO_HA_CONDITION_MAP as CDT_MAP
from .const import OUT_OF_BENELUX, USER_AGENT
from .data import ProcessedCoordinatorData
from .utils import disable_from_config, get_config_value, preferred_language

_LOGGER = logging.getLogger(__name__)


class IrmKmiCoordinator(TimestampDataUpdateCoordinator):
    """Coordinator to update data from IRM KMI"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            # Name of the data. For logging purposes.
            name="IRM KMI weather",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=7),
        )
        self._api = IrmKmiApiClientHa(session=async_get_clientsession(hass), user_agent=USER_AGENT, cdt_map=CDT_MAP)
        self._zone = get_config_value(entry, CONF_ZONE)
        self._dark_mode = get_config_value(entry, CONF_DARK_MODE)
        try:
            self._style = RadarStyle(get_config_value(entry, CONF_STYLE))
        except ValueError:
            self._style = RadarStyle.OPTION_STYLE_STD
        self.shared_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=IRM_KMI_NAME.get(preferred_language(self.hass, self.config_entry)),
            name=f"{entry.title}"
        )

    async def _async_update_data(self) -> ProcessedCoordinatorData:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        # When integration is set up, set the logging level of the irm_kmi_api package to the same level to help debugging
        logging.getLogger('irm_kmi_api').setLevel(_LOGGER.getEffectiveLevel())

        self._api.expire_cache()
        if (zone := self.hass.states.get(self._zone)) is None:
            raise UpdateFailed(f"Zone '{self._zone}' not found")
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(60):
                await self._api.refresh_forecasts_coord(
                    {'lat': zone.attributes[ATTR_LATITUDE],
                     'long': zone.attributes[ATTR_LONGITUDE]}
                )

        except IrmKmiApiError as err:
            if self.last_update_success_time is not None \
                    and self.last_update_success_time - utcnow() < 2.5 * self.update_interval:
                _LOGGER.warning(f"Error communicating with API for general forecast: {err}. Keeping the old data.")
                return self.data
            else:
                raise UpdateFailed(f"Error communicating with API for general forecast: {err}. "
                                   f"Last success time is: {self.last_update_success_time}")

        if self._api.get_city() in OUT_OF_BENELUX:
            _LOGGER.error(f"The zone {self._zone} is now out of Benelux and forecast is only available in Benelux. "
                          f"Associated device is now disabled.  Move the zone back in Benelux and re-enable to fix "
                          f"this")
            disable_from_config(self.hass, self.config_entry)

            issue_registry.async_create_issue(
                self.hass,
                DOMAIN,
                "zone_moved",
                is_fixable=True,
                severity=issue_registry.IssueSeverity.ERROR,
                translation_key='zone_moved',
                data={'config_entry_id': self.config_entry.entry_id, 'zone': self._zone},
                translation_placeholders={'zone': self._zone}
            )
            return ProcessedCoordinatorData()

        return await self.process_api_data()

    async def async_refresh(self) -> None:
        """Refresh data and log errors."""
        await self._async_refresh(log_failures=True, raise_on_entry_error=True)

    async def process_api_data(self) -> ProcessedCoordinatorData:
        """From the API data, create the object that will be used in the entities"""
        tz = await dt.async_get_time_zone('Europe/Brussels')
        lang = preferred_language(self.hass, self.config_entry)
        try:
            pollen = await self._api.get_pollen()
        except IrmKmiApiError as err:
            _LOGGER.warning(f"Could not get pollen data from the API: {err}. Keeping the same data.")
            pollen = self.data.get('pollen', PollenParser.get_unavailable_data()) \
                if self.data is not None else PollenParser.get_unavailable_data()

        try:
            radar_animation = self._api.get_animation_data(tz, lang, self._style, self._dark_mode)
            animation = await RainGraph(radar_animation,
                                        country=self._api.get_country(),
                                        style=self._style,
                                        tz=tz,
                                        dark_mode=self._dark_mode,
                                        api_client=self._api
                                        ).build()
        except ValueError:
            animation = None

        return ProcessedCoordinatorData(
            current_weather=self._api.get_current_weather(tz),
            daily_forecast=self._api.get_daily_forecast(tz, lang),
            hourly_forecast=self._api.get_hourly_forecast(tz),
            radar_forecast=self._api.get_radar_forecast(),
            animation=animation,
            warnings=self._api.get_warnings(lang),
            pollen=pollen,
            country=self._api.get_country()
        )
