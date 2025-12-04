from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    EVENT_OUT_OF_RANGE,
    EVENT_BACK_IN_RANGE,
)


async def async_setup_entry(
        hass: HomeAssistantType,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
):
    """Création des entités pour une config_entry."""
    data = entry.data

    entity = TempAlertBinarySensor(
        hass=hass,
        entry_id=entry.entry_id,
        name=data[CONF_NAME],
        sensor_entity_id=data[CONF_SENSOR],
        min_temp=data[CONF_MIN_TEMP],
        max_temp=data[CONF_MAX_TEMP],
    )

    async_add_entities([entity])


class TempAlertBinarySensor(BinarySensorEntity):
    """Binary sensor d'alerte température."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
            self,
            hass: HomeAssistant,
            entry_id: str,
            name: str,
            sensor_entity_id: str,
            min_temp: float,
            max_temp: float,
    ):
        self._hass = hass
        self._entry_id = entry_id
        self._attr_name = name
        self._sensor_entity_id = sensor_entity_id
        self._min_temp = float(min_temp)
        self._max_temp = float(max_temp)

        self._attr_unique_id = f"{entry_id}_alert"
        self._attr_is_on = False
        self._out_of_range = False  # état logique interne

        self._attr_extra_state_attributes = {
            "sensor": sensor_entity_id,
            "min_temp": self._min_temp,
            "max_temp": self._max_temp,
        }

        self._unsub_state_listener = None

    @property
    def device_info(self):
        """Permet à HA de voir ça comme un 'appareil'."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self.name,
            "manufacturer": "Nicolas",
            "model": "Temperature Monitor",
        }

    async def async_added_to_hass(self):
        """Appelé quand l'entité est ajoutée."""
        @callback
        def _sensor_state_listener(event):
            self._handle_sensor_state_change()

        self._unsub_state_listener = async_track_state_change_event(
            self._hass, [self._sensor_entity_id], _sensor_state_listener
        )

        # Évalue l'état une première fois sans envoyer d'event
        self._handle_sensor_state_change(initial=True)

    async def async_will_remove_from_hass(self):
        """Cleanup."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None

    @callback
    def _handle_sensor_state_change(self, initial: bool = False):
        """Check la valeur du capteur, met à jour l'alerte et fire les events."""
        state_obj = self._hass.states.get(self._sensor_entity_id)
        if not state_obj:
            return

        try:
            value = float(state_obj.state)
        except (ValueError, TypeError):
            return

        in_range = self._min_temp <= value <= self._max_temp
        was_out_of_range = self._out_of_range

        # Mise à jour état logique
        self._out_of_range = not in_range
        self._attr_is_on = self._out_of_range

        # Mise à jour attributs
        self._attr_extra_state_attributes.update(
            {
                "current_temp": value,
                "in_range": in_range,
            }
        )

        # Pas d'event au premier calcul (au démarrage), juste sync l'état
        if initial:
            self.schedule_update_ha_state()
            return

        # Transition : in_range -> out_of_range
        if not was_out_of_range and self._out_of_range:
            self._fire_out_of_range_event(value)

        # Transition : out_of_range -> in_range
        if was_out_of_range and in_range:
            self._fire_back_in_range_event(value)

        self.schedule_update_ha_state()

    def _fire_out_of_range_event(self, value: float):
        """Fire l'event quand la temp sort de la plage."""
        self._hass.bus.fire(
            EVENT_OUT_OF_RANGE,
            {
                "monitor_entity_id": self.entity_id,
                "sensor_entity_id": self._sensor_entity_id,
                "current_temp": value,
                "min_temp": self._min_temp,
                "max_temp": self._max_temp,
                "reason": "below_min"
                if value < self._min_temp
                else "above_max",
                "entry_id": self._entry_id,
            },
        )

    def _fire_back_in_range_event(self, value: float):
        """Fire l'event quand la temp redevient dans la plage."""
        self._hass.bus.fire(
            EVENT_BACK_IN_RANGE,
            {
                "monitor_entity_id": self.entity_id,
                "sensor_entity_id": self._sensor_entity_id,
                "current_temp": value,
                "min_temp": self._min_temp,
                "max_temp": self._max_temp,
                "entry_id": self._entry_id,
            },
        )