from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_NAME, CONF_SENSOR, CONF_MIN_TEMP, CONF_MAX_TEMP


class TempMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow pour Heat Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Nom par défaut si vide
            if not user_input.get(CONF_NAME):
                user_input[CONF_NAME] = f"Heat Monitor {user_input[CONF_SENSOR]}"

            # Un config_entry par capteur (éviter les doublons)
            await self.async_set_unique_id(user_input[CONF_SENSOR])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=""): str,
                vol.Required(CONF_SENSOR): selector.selector(
                    {
                        "entity": {
                            "domain": "sensor",
                            "device_class": "temperature",
                        }
                    }
                ),
                vol.Required(CONF_MIN_TEMP, default=5.0): vol.Coerce(float),
                vol.Required(CONF_MAX_TEMP, default=30.0): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )