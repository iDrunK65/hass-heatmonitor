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
    EVENT_OUT_OF_RANGE,
    EVENT_BACK_IN_RANGE,
)


async def async_setup_entry(
        hass: HomeAssistantType,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
):
    """Création des entités pour une config_entry."""
    # Lire depuis hass.data au lieu de entry.data
    data = hass.data[DOMAIN][entry.entry_id]

    entity = TempAlertBinarySensor(
        hass=hass,
        entry_id=entry.entry_id,
        name=data[CONF_NAME],
        sensor_entity_id=data[CONF_SENSOR],
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
    ):
        self._hass = hass
        self._entry_id = entry_id
        self._attr_name = name
        self._sensor_entity_id = sensor_entity_id

        self._attr_unique_id = f"{entry_id}_alert"
        self._attr_is_on = False
        self._out_of_range = False  # état logique interne

        self._unsub_state_listener = None
        self._unsub_temp_update_listener = None

    @property
    def _min_temp(self) -> float:
        """Lit min_temp depuis hass.data."""
        return self._hass.data[DOMAIN][self._entry_id]["min_temp"]

    @property
    def _max_temp(self) -> float:
        """Lit max_temp depuis hass.data."""
        return self._hass.data[DOMAIN][self._entry_id]["max_temp"]

    @property
    def device_info(self):
        """Permet à HA de voir ça comme un 'appareil'."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self.name,
            "manufacturer": "Nicolas",
            "model": "Heat Monitor",
        }

    async def async_added_to_hass(self):
        """Appelé quand l'entité est ajoutée."""
        @callback
        def _sensor_state_listener(event):
            self._handle_sensor_state_change()

        @callback
        def _temp_update_listener(event):
            """Écoute les mises à jour de température depuis les number entities."""
            if event.data.get("entry_id") == self._entry_id:
                # Recalculer avec les nouvelles valeurs
                self._handle_sensor_state_change(initial=False)

        self._unsub_state_listener = async_track_state_change_event(
            self._hass, [self._sensor_entity_id], _sensor_state_listener
        )

        # Écouter les mises à jour de température depuis les number entities
        self._unsub_temp_update_listener = self._hass.bus.async_listen(
            f"{DOMAIN}_temp_updated",
            _temp_update_listener,
        )

        # Évalue l'état une première fois sans envoyer d'event
        self._handle_sensor_state_change(initial=True)

    async def async_will_remove_from_hass(self):
        """Cleanup."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        if self._unsub_temp_update_listener:
            self._unsub_temp_update_listener()
            self._unsub_temp_update_listener = None

    def _get_sensor_info(self):
        """Récupère le friendly name et l'area du capteur depuis l'entity registry."""
        entity_registry = self._hass.helpers.entity_registry.async_get()
        entity_entry = entity_registry.async_get(self._sensor_entity_id)
        
        sensor_friendly_name = None
        sensor_area = None
        
        if entity_entry:
            # Récupérer le friendly name
            sensor_friendly_name = entity_entry.name or entity_entry.original_name
            
            # Récupérer l'area si disponible
            if entity_entry.area_id:
                area_registry = self._hass.helpers.area_registry.async_get()
                area_entry = area_registry.async_get_area(entity_entry.area_id)
                if area_entry:
                    sensor_area = area_entry.name
        
        # Si pas de friendly name dans le registry, utiliser celui de l'état
        if not sensor_friendly_name:
            state_obj = self._hass.states.get(self._sensor_entity_id)
            if state_obj:
                sensor_friendly_name = state_obj.attributes.get("friendly_name")
        
        return sensor_friendly_name, sensor_area

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

        # Récupérer les infos du capteur
        sensor_friendly_name, sensor_area = self._get_sensor_info()

        # Mise à jour attributs (lire les valeurs actuelles depuis hass.data)
        self._attr_extra_state_attributes = {
            "sensor": self._sensor_entity_id,
            "sensor_friendly_name": sensor_friendly_name,
            "sensor_area": sensor_area,
            "min_temp": self._min_temp,
            "max_temp": self._max_temp,
            "current_temp": value,
            "in_range": in_range,
        }

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