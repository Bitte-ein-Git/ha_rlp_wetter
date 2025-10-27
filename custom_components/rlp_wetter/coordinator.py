"""DataUpdateCoordinator für RLP Wetter."""
import logging
from datetime import timedelta
import async_timeout
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, API_ENDPOINT, CONF_STATION_ID, REQUEST_TIMEOUT, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RlpWetterDataUpdateCoordinator(DataUpdateCoordinator):
    """Koordinator zum Abrufen von RLP Wetterdaten."""

    def __init__(self, hass: HomeAssistant, station_id: int):
        """Initialisiere den Koordinator."""
        self.station_id = station_id
        self.api_url = f"{API_ENDPOINT}?sid={self.station_id}"
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} Station {self.station_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict:
        """Rufe Daten vom API-Endpunkt ab."""
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                # Send request
                response = await self.session.get(self.api_url)
                response.raise_for_status()
                data = await response.json()

                if not data or "messwerte" not in data or not data["messwerte"]:
                    raise UpdateFailed("Keine gültigen Messwerte in der API-Antwort gefunden.")

                # Return the latest measurement
                latest_measurement = data["messwerte"][0]

                # Add station info
                latest_measurement["station_name"] = data.get("station_name")
                latest_measurement["station_id"] = data.get("station_id")
                latest_measurement["station_height"] = data.get("station_height")

                return latest_measurement

        except aiohttp.ClientConnectorError as err:
            raise UpdateFailed(f"Verbindungsfehler zur API: {err}") from err
        except aiohttp.ClientResponseError as err:
             # Log 5xx errors as warnings (transient) and 4xx as errors (config issue)
             if 500 <= err.status <= 599:
                 _LOGGER.warning("API-Fehler (Server/Gateway) %s für Station %s: %s", err.status, self.station_id, err.message)
             else:
                _LOGGER.error("API-Fehler (Client) %s für Station %s: %s", err.status, self.station_id, err.message)
             raise UpdateFailed(f"API-Fehler: {err.status} - {err.message}") from err
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout bei der API-Abfrage: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unerwarteter Fehler beim Abrufen der Wetterdaten für Station %s", self.station_id)
            raise UpdateFailed(f"Unerwarteter Fehler: {err}") from err