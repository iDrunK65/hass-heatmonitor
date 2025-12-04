from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
)

PLATFORMS: list[str] = ["binary_sensor", "number"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Setup via configuration.yaml (non utilisé)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup d'une config_entry (un appareil)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "name": entry.data[CONF_NAME],
        "sensor": entry.data[CONF_SENSOR],
        "min_temp": float(entry.data[CONF_MIN_TEMP]),
        "max_temp": float(entry.data[CONF_MAX_TEMP]),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload d'une config_entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok