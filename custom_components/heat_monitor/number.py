from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_MIN_TEMP, CONF_MAX_TEMP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Création des entités number pour une config_entry."""
    entities = [
        MinTempNumber(hass=hass, entry_id=entry.entry_id),
        MaxTempNumber(hass=hass, entry_id=entry.entry_id),
    ]
    async_add_entities(entities)


class BaseTempNumber(NumberEntity):
    """Classe de base pour les entités number de température."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = -50.0
    _attr_native_max_value = 80.0
    _attr_native_step = 0.5

    def __init__(self, hass: HomeAssistant, entry_id: str):
        self._hass = hass
        self._entry_id = entry_id
        self._data_key = ""  # Sera défini dans les sous-classes

    @property
    def device_info(self):
        """Permet à HA de voir ça comme un 'appareil'."""
        data = self._hass.data[DOMAIN][self._entry_id]
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": data["name"],
            "manufacturer": "iDrunK",
            "model": "Heat Monitor",
        }

    @property
    def native_value(self) -> float:
        """Retourne la valeur actuelle depuis hass.data."""
        return self._hass.data[DOMAIN][self._entry_id][self._data_key]

    async def async_set_native_value(self, value: float) -> None:
        """Met à jour la valeur dans hass.data et persiste dans config_entry."""
        # Mettre à jour hass.data
        self._hass.data[DOMAIN][self._entry_id][self._data_key] = float(value)

        # Persister dans config_entry
        entry = self._hass.config_entries.async_get_entry(self._entry_id)
        if entry:
            new_data = entry.data.copy()
            new_data[self._data_key] = float(value)
            self._hass.config_entries.async_update_entry(entry, data=new_data)

        # Notifier le binary_sensor pour recalculer
        self._notify_binary_sensor()

        # Mettre à jour l'état de cette entité
        self.async_write_ha_state()

    @callback
    def _notify_binary_sensor(self):
        """Notifie le binary_sensor pour qu'il recalcule avec les nouvelles valeurs."""
        # Déclencher un événement personnalisé que le binary_sensor écoute
        self._hass.bus.async_fire(
            f"{DOMAIN}_temp_updated",
            {"entry_id": self._entry_id},
        )


class MinTempNumber(BaseTempNumber):
    """Entité number pour la température minimale."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        super().__init__(hass, entry_id)
        self._data_key = CONF_MIN_TEMP
        data = hass.data[DOMAIN][entry_id]
        self._attr_name = f"{data['name']} Min Temp"
        self._attr_unique_id = f"heatmonitor_{entry_id}_min_temp"


class MaxTempNumber(BaseTempNumber):
    """Entité number pour la température maximale."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        super().__init__(hass, entry_id)
        self._data_key = CONF_MAX_TEMP
        data = hass.data[DOMAIN][entry_id]
        self._attr_name = f"{data['name']} Max Temp"
        self._attr_unique_id = f"heatmonitor_{entry_id}_max_temp"

