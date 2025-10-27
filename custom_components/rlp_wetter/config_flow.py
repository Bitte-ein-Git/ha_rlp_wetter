"""Config flow für RLP Wetter."""
import logging
from typing import Any

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_STATION_ID, STATION_LIST, API_ENDPOINT, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validiere die Benutzereingabe, um sicherzustellen, dass die Station erreichbar ist."""
    session = async_get_clientsession(hass)
    station_id = data[CONF_STATION_ID]
    url = f"{API_ENDPOINT}?sid={station_id}"

    try:
        async with session.get(url, timeout=REQUEST_TIMEOUT) as response:
            response.raise_for_status() # Löst einen Fehler aus bei 4xx oder 5xx
            # Optional: Prüfe, ob die Antwort gültiges JSON ist und Daten enthält
            json_data = await response.json()
            if not json_data or "messwerte" not in json_data or not json_data["messwerte"]:
                 raise vol.Invalid("Keine gültigen Messwerte von der API erhalten.")

            # Finde den Anzeigenamen zur ID für den Titel des Eintrags
            station_name = next((name for name, sid in STATION_LIST.items() if sid == station_id), f"Station {station_id}")
            return {"title": station_name}

    except aiohttp.ClientConnectorError as exc:
        _LOGGER.error("Verbindungsfehler beim Testen der Station %s: %s", station_id, exc)
        raise vol.Invalid("cannot_connect") from exc
    except aiohttp.ClientResponseError as exc:
        _LOGGER.error("API-Fehler beim Testen der Station %s: Status %s", station_id, exc.status)
        if exc.status == 400: # Spezifischer Fehler für ungültige SID vom Worker?
             raise vol.Invalid("Ungültige Stations-ID oder Parameter.") from exc
        elif exc.status == 404 or exc.status == 502 or exc.status == 500:
             # Diese Fehler könnten vom Worker kommen, wenn die Quelle nicht antwortet
             raise vol.Invalid("Daten konnten nicht abgerufen werden (möglicherweise ungültige SID oder Quell-Problem).") from exc
        else:
             raise vol.Invalid("cannot_connect") from exc # Allgemeiner Verbindungsfehler
    except Exception as exc:
        _LOGGER.exception("Unerwarteter Fehler beim Testen der Station %s", station_id)
        raise vol.Invalid("unknown") from exc


class RlpWetterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RLP Wetter."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Sortiere die Stationen alphabetisch nach Namen für das Dropdown
        sorted_stations = dict(sorted(STATION_LIST.items()))

        # Erstelle das Schema mit dem Dropdown
        # Wichtig: Die Werte im Dropdown müssen die SIDs (Integer) sein
        schema = vol.Schema({
            vol.Required(CONF_STATION_ID): vol.In({
                sid: name for name, sid in sorted_stations.items()
            })
        })

        if user_input is not None:
            # Stelle sicher, dass die Konfiguration für diese SID nicht bereits existiert
            station_id = user_input[CONF_STATION_ID]
            await self.async_set_unique_id(str(station_id)) # Eindeutige ID pro Station
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except vol.Invalid as err:
                 # err.path enthält den Key ('station_id'), err.error_message die Fehlermeldung
                 # Wenn validate_input direkt 'cannot_connect' etc. wirft, ist es in err.error_message
                 error_key = err.error_message if err.error_message in ["cannot_connect", "unknown"] else "validation_failed" # Generischer Fallback
                 if str(err).startswith("Ungültige"): error_key = "invalid_sid"
                 if str(err).startswith("Daten konnten"): error_key = "fetch_failed"

                 # In strings.json müssten ggf. noch Einträge für "invalid_sid", "fetch_failed", "validation_failed" hinzugefügt werden
                 errors["base"] = error_key # "base" zeigt Fehler allgemein an, nicht an einem Feld

            else:
                # Eingabe ist gültig, erstelle den Config Entry
                return self.async_create_entry(title=info["title"], data=user_input)

        # Zeige das Formular an (erneut, wenn Fehler aufgetreten sind)
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

