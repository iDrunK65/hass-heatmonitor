from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Retourne le options flow handler."""
        return TempMonitorOptionsFlowHandler(config_entry)


class TempMonitorOptionsFlowHandler(OptionsFlow):
    """Handler pour le options flow de Heat Monitor."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialise le options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gère le options flow."""
        errors = {}

        if user_input is not None:
            # Mettre à jour la config entry avec les nouvelles valeurs
            # On met à jour entry.data pour que les changements soient persistés
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            # Mettre à jour hass.data immédiatement
            from .const import DOMAIN, CONF_NAME, CONF_SENSOR, CONF_MIN_TEMP, CONF_MAX_TEMP
            self.hass.data.setdefault(DOMAIN, {})
            self.hass.data[DOMAIN][self.config_entry.entry_id] = {
                "name": user_input[CONF_NAME],
                "sensor": user_input[CONF_SENSOR],
                "min_temp": float(user_input[CONF_MIN_TEMP]),
                "max_temp": float(user_input[CONF_MAX_TEMP]),
            }
            return self.async_create_entry(title="", data={})

        # Pré-remplir avec les valeurs actuelles
        current_data = self.config_entry.data

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=current_data.get(CONF_NAME, "")): str,
                vol.Required(CONF_SENSOR, default=current_data.get(CONF_SENSOR)): selector.selector(
                    {
                        "entity": {
                            "domain": "sensor",
                            "device_class": "temperature",
                        }
                    }
                ),
                vol.Required(
                    CONF_MIN_TEMP, default=current_data.get(CONF_MIN_TEMP, 5.0)
                ): vol.Coerce(float),
                vol.Required(
                    CONF_MAX_TEMP, default=current_data.get(CONF_MAX_TEMP, 30.0)
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=data_schema, errors=errors
        )