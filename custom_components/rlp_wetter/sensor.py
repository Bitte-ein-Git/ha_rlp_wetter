"""Sensor-Plattform für RLP Wetter."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo # Hinzugefügt für Geräte-Info

from .const import DOMAIN, SENSOR_TYPES, CONF_STATION_ID
from .coordinator import RlpWetterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Richte RLP Wetter Sensoren von einem Config Entry ein."""
    coordinator: RlpWetterDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Erstelle Entitäten basierend auf den Sensorbeschreibungen
    entities = [
        RlpWetterSensor(coordinator, description)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class RlpWetterSensor(CoordinatorEntity[RlpWetterDataUpdateCoordinator], SensorEntity):
    """Repräsentation eines RLP Wetter Sensors."""

    entity_description: SensorEntityDescription # Typ-Hint für die Beschreibung

    def __init__(
        self,
        coordinator: RlpWetterDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialisiere den Sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = coordinator.station_id

        # Eindeutige ID für den Sensor
        self._attr_unique_id = f"{DOMAIN}_{self._station_id}_{description.key}"

        # Geräte-Info, um alle Sensoren einer Station zu gruppieren
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self._station_id))}, # Eindeutiger Identifier für das Gerät
            name=f"RLP Wetter Station {self.coordinator.data.get('station_name', self._station_id)}",
            manufacturer="RLP Agrarmeteorologie (via Proxy)",
            model=f"Station ID {self._station_id}",
            entry_type="service", # oder None
            configuration_url=f"https://www.wetter.rlp.de/Agrarmeteorologie/Wetterdaten/Alphabetisch/AM{self._station_id}" # Link zur Originalseite (optional)
        )


    @property
    def native_value(self) -> Any | None:
        """Return the state of the sensor."""
        # Daten kommen vom Koordinator
        if self.coordinator.data and self.entity_description.key in self.coordinator.data:
            value = self.coordinator.data[self.entity_description.key]
            # Sicherstellen, dass der Wert nicht None ist, bevor er zurückgegeben wird
            # (obwohl die API 0 zurückgeben sollte, falls kein Niederschlag etc.)
            return value
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Die Entität ist verfügbar, wenn der Koordinator erfolgreich Daten hat
        # und der spezifische Schlüssel in den Daten vorhanden ist.
        return super().available and self.coordinator.data is not None and self.entity_description.key in self.coordinator.data

    # Optional: Zusätzliche Attribute hinzufügen
    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data:
             return {
                 "station_id": self.coordinator.data.get("station_id"),
                 "station_name": self.coordinator.data.get("station_name"),
                 "station_height": self.coordinator.data.get("station_height"),
                 "measurement_time": f"{self.coordinator.data.get('datum')} {self.coordinator.data.get('zeit')}",
                 "last_update": self.coordinator.last_update_success_time,
             }
        return None

