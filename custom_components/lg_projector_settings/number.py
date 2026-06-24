"""Number platform for LG Projector Settings."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the LG Projector number platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]

    async_add_entities([LgProjectorBacklight(client, host, entry.entry_id)])

class LgProjectorBacklight(NumberEntity):
    """Representation of the LG Projector Backlight number entity."""

    _attr_has_entity_name = True
    _attr_name = "Backlight"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:brightness-6"

    def __init__(self, client, host, entry_id):
        """Initialize the number entity."""
        self._client = client
        self._host = host
        self._attr_unique_id = f"{entry_id}_backlight"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"LG Projector ({host})",
            manufacturer="LG",
        )
        self._attr_native_value = None

    async def async_update(self) -> None:
        """Fetch the latest state of the backlight."""
        try:
            payload = {"category": "picture", "keys": ["backlight"]}
            ret = await self._client.request("settings/getSystemSettings", payload=payload)
            settings = ret.get("settings", {})
            if "backlight" in settings:
                self._attr_native_value = float(settings["backlight"])
        except Exception as e:
            _LOGGER.error("Failed to fetch backlight settings: %s", e)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        try:
            backlight = int(value)
            uri = "com.webos.settingsservice/setSystemSettings"
            settings = {"backlight": backlight}
            params = {"category": "picture", "settings": settings}
            
            await self._async_luna_request(uri, params)
            self._attr_native_value = value
        except Exception as e:
            _LOGGER.error("Failed to set backlight to %s: %s", value, e)

    async def _async_luna_request(self, uri, params):
        """Perform a restricted luna request using the alert notification trick."""
        lunauri = f"luna://{uri}"
        buttons = [{"label": "", "onClick": lunauri, "params": params}]
        payload = {
            "message": " ",
            "buttons": buttons,
            "onclose": {"uri": lunauri, "params": params},
            "onfail": {"uri": lunauri, "params": params},
        }
        ret = await self._client.request("system.notifications/createAlert", payload)
        alert_id = ret.get("alertId")
        if alert_id is not None:
            await self._client.request("system.notifications/closeAlert", payload={"alertId": alert_id})
