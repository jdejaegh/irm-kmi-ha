import logging
import voluptuous as vol

from homeassistant.components.zone import DOMAIN as ZONE_DOMAIN
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ZONE
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IrmKmiConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:

        if user_input is not None:
            _LOGGER.debug(f"Provided config user is: {user_input}")

            await self.async_set_unique_id(user_input[CONF_ZONE])
            self._abort_if_unique_id_configured()

            state = self.hass.states.get(user_input[CONF_ZONE])
            return self.async_create_entry(
                title=state.name if state else "IRM KMI",
                data={CONF_ZONE: user_input[CONF_ZONE]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ZONE): EntitySelector(
                        EntitySelectorConfig(domain=ZONE_DOMAIN),
                    ),
                }
            ),
        )
