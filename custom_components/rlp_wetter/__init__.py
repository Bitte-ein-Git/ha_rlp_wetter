"""Die RLP Wetter Integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, CONF_STATION_ID, PLATFORMS
from .coordinator import RlpWetterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richte RLP Wetter von einem Config Entry ein."""
    hass.data.setdefault(DOMAIN, {})

    station_id = entry.data[CONF_STATION_ID]

    # Erstelle den Koordinator
    coordinator = RlpWetterDataUpdateCoordinator(hass, station_id)

    # Erster Refresh, um sicherzustellen, dass Daten verfügbar sind, bevor die Plattformen geladen werden
    await coordinator.async_config_entry_first_refresh()

    # Speichere den Koordinator für die Plattformen
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Lade die Sensor-Plattform
    await hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlade einen Config Entry."""
    # Entlade die Plattformen
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Entferne den Koordinator aus hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
