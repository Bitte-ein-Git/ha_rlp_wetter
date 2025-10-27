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
        # Send request
        async with session.get(url, timeout=REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            json_data = await response.json()
            
            # Check if valid data is returned from API
            if not json_data or "messwerte" not in json_data or not json_data["messwerte"]:
                 raise vol.Invalid("Keine gültigen Messwerte von der API erhalten.")

            # Find station name
            station_name = next((name for name, sid in STATION_LIST.items() if sid == station_id), f"Station {station_id}")
            return {"title": station_name}

    except aiohttp.ClientConnectorError as exc:
        _LOGGER.error("Verbindungsfehler beim Testen der Station %s: %s", station_id, exc)
        raise vol.Invalid("cannot_connect") from exc
    except aiohttp.ClientResponseError as exc:
        _LOGGER.warning("API-Fehler beim Testen der Station %s: Status %s", station_id, exc.status)
        if exc.status == 400:
             raise vol.Invalid("invalid_sid") from exc
        elif exc.status == 404 or exc.status == 500 or exc.status == 502:
             raise vol.Invalid("fetch_failed") from exc
        else:
             raise vol.Invalid("cannot_connect") from exc
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

        # Sort stations alphabetically
        sorted_stations = dict(sorted(STATION_LIST.items()))

        # Create schema
        schema = vol.Schema({
            vol.Required(CONF_STATION_ID): vol.In({
                sid: name for name, sid in sorted_stations.items()
            })
        })

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            await self.async_set_unique_id(str(station_id))
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except vol.Invalid as err:
                 # Map validation errors to keys in strings.json
                 if err.error_message in ["cannot_connect", "unknown", "invalid_sid", "fetch_failed"]:
                    errors["base"] = err.error_message
                 else:
                    errors["base"] = "validation_failed" # Fallback
            else:
                # Input is valid
                return self.async_create_entry(title=info["title"], data=user_input)

        # Show form
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )