"""Config flow to set up IRM KMI integration via the UI."""
import logging

import voluptuous as vol
from homeassistant.components.zone import DOMAIN as ZONE_DOMAIN
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ZONE
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (EntitySelector,
                                            EntitySelectorConfig,
                                            SelectSelector,
                                            SelectSelectorConfig,
                                            SelectSelectorMode)

from .const import (CONF_DARK_MODE, CONF_STYLE, CONF_STYLE_OPTIONS,
                    CONF_STYLE_STD, DOMAIN)

_LOGGER = logging.getLogger(__name__)


class IrmKmiConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Define the user step of the configuration flow."""
        print(f"IN CONFIG FLOW HERE with {user_input}")
        if user_input is not None:
            _LOGGER.debug(f"Provided config user is: {user_input}")

            await self.async_set_unique_id(user_input[CONF_ZONE])
            self._abort_if_unique_id_configured()

            state = self.hass.states.get(user_input[CONF_ZONE])
            return self.async_create_entry(
                title=state.name if state else "IRM KMI",
                data={CONF_ZONE: user_input[CONF_ZONE],
                      CONF_STYLE: user_input[CONF_STYLE],
                      CONF_DARK_MODE: user_input[CONF_DARK_MODE]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ZONE):
                    EntitySelector(EntitySelectorConfig(domain=ZONE_DOMAIN)),

                vol.Optional(CONF_STYLE, default=CONF_STYLE_STD):
                    SelectSelector(SelectSelectorConfig(options=CONF_STYLE_OPTIONS,
                                                        mode=SelectSelectorMode.DROPDOWN,
                                                        translation_key=CONF_STYLE)),

                vol.Optional(CONF_DARK_MODE, default=False): bool
            }))
