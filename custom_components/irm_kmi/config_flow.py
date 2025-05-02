"""Config flow to set up IRM KMI integration via the UI."""
import logging

import async_timeout
import voluptuous as vol
from homeassistant.components.zone import DOMAIN as ZONE_DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_ZONE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (EntitySelector,
                                            EntitySelectorConfig,
                                            SelectSelector,
                                            SelectSelectorConfig,
                                            SelectSelectorMode)

from . import OPTION_STYLE_STD
from .const import (CONF_DARK_MODE, CONF_LANGUAGE_OVERRIDE,
                    CONF_LANGUAGE_OVERRIDE_OPTIONS, CONF_STYLE,
                    CONF_STYLE_OPTIONS, CONF_USE_DEPRECATED_FORECAST,
                    CONF_USE_DEPRECATED_FORECAST_OPTIONS, CONFIG_FLOW_VERSION,
                    DOMAIN, OPTION_DEPRECATED_FORECAST_NOT_USED,
                    OUT_OF_BENELUX, USER_AGENT)
from .irm_kmi_api.api import IrmKmiApiClient
from .utils import get_config_value

_LOGGER = logging.getLogger(__name__)


class IrmKmiConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return IrmKmiOptionFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Define the user step of the configuration flow."""
        errors = {}

        if user_input:
            _LOGGER.debug(f"Provided config user is: {user_input}")

            if (zone := self.hass.states.get(user_input[CONF_ZONE])) is None:
                errors[CONF_ZONE] = 'zone_not_exist'

            # Check if zone is in Benelux
            if not errors:
                api_data = {}
                try:
                    async with (async_timeout.timeout(60)):
                        api_data = await IrmKmiApiClient(
                            session=async_get_clientsession(self.hass),
                            user_agent=USER_AGENT
                        ).get_forecasts_coord(
                            {'lat': zone.attributes[ATTR_LATITUDE],
                             'long': zone.attributes[ATTR_LONGITUDE]}
                        )
                except Exception:
                    errors['base'] = "api_error"

                if api_data.get('cityName', None) in OUT_OF_BENELUX:
                    errors[CONF_ZONE] = 'out_of_benelux'

                if not errors:
                    await self.async_set_unique_id(user_input[CONF_ZONE])
                    self._abort_if_unique_id_configured()

                    state = self.hass.states.get(user_input[CONF_ZONE])
                    return self.async_create_entry(
                        title=state.name if state else "IRM KMI",
                        data={CONF_ZONE: user_input[CONF_ZONE],
                              CONF_STYLE: user_input[CONF_STYLE],
                              CONF_DARK_MODE: user_input[CONF_DARK_MODE],
                              CONF_USE_DEPRECATED_FORECAST: user_input[CONF_USE_DEPRECATED_FORECAST],
                              CONF_LANGUAGE_OVERRIDE: user_input[CONF_LANGUAGE_OVERRIDE]},
                    )

        return self.async_show_form(
            step_id="user",
            errors=errors,
            description_placeholders={'zone': user_input.get('zone') if user_input is not None else None},
            data_schema=vol.Schema({
                vol.Required(CONF_ZONE):
                    EntitySelector(EntitySelectorConfig(domain=ZONE_DOMAIN)),

                vol.Optional(CONF_STYLE, default=OPTION_STYLE_STD):
                    SelectSelector(SelectSelectorConfig(options=CONF_STYLE_OPTIONS,
                                                        mode=SelectSelectorMode.DROPDOWN,
                                                        translation_key=CONF_STYLE)),

                vol.Optional(CONF_DARK_MODE, default=False): bool,

                vol.Optional(CONF_USE_DEPRECATED_FORECAST, default=OPTION_DEPRECATED_FORECAST_NOT_USED):
                    SelectSelector(SelectSelectorConfig(options=CONF_USE_DEPRECATED_FORECAST_OPTIONS,
                                                        mode=SelectSelectorMode.DROPDOWN,
                                                        translation_key=CONF_USE_DEPRECATED_FORECAST)),

                vol.Optional(CONF_LANGUAGE_OVERRIDE, default='none'):
                    SelectSelector(SelectSelectorConfig(options=CONF_LANGUAGE_OVERRIDE_OPTIONS,
                                                        mode=SelectSelectorMode.DROPDOWN,
                                                        translation_key=CONF_LANGUAGE_OVERRIDE))

            }))


class IrmKmiOptionFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.current_config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug(user_input)
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_STYLE, default=get_config_value(self.current_config_entry, CONF_STYLE)):
                        SelectSelector(SelectSelectorConfig(options=CONF_STYLE_OPTIONS,
                                                            mode=SelectSelectorMode.DROPDOWN,
                                                            translation_key=CONF_STYLE)),

                    vol.Optional(CONF_DARK_MODE, default=get_config_value(self.current_config_entry, CONF_DARK_MODE)): bool,

                    vol.Optional(CONF_USE_DEPRECATED_FORECAST,
                                 default=get_config_value(self.current_config_entry, CONF_USE_DEPRECATED_FORECAST)):
                        SelectSelector(SelectSelectorConfig(options=CONF_USE_DEPRECATED_FORECAST_OPTIONS,
                                                            mode=SelectSelectorMode.DROPDOWN,
                                                            translation_key=CONF_USE_DEPRECATED_FORECAST)),

                    vol.Optional(CONF_LANGUAGE_OVERRIDE,
                                 default=get_config_value(self.current_config_entry, CONF_LANGUAGE_OVERRIDE)):
                        SelectSelector(SelectSelectorConfig(options=CONF_LANGUAGE_OVERRIDE_OPTIONS,
                                                            mode=SelectSelectorMode.DROPDOWN,
                                                            translation_key=CONF_LANGUAGE_OVERRIDE))
                }
            ),
        )
