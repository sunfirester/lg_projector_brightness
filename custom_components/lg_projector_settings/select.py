"""Select platform for LG Projector Settings."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_HOST, PICTURE_MODES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the LG Projector select platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]

    async_add_entities([LgProjectorPictureMode(client, host, entry.entry_id)])

class LgProjectorPictureMode(SelectEntity):
    """Representation of the LG Projector Picture Mode select entity."""

    _attr_has_entity_name = True
    _attr_name = "Picture Mode"
    _attr_options = PICTURE_MODES
    _attr_icon = "mdi:television-guide"

    def __init__(self, client, host, entry_id):
        """Initialize the select entity."""
        self._client = client
        self._host = host
        self._attr_unique_id = f"{entry_id}_picture_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"LG Projector ({host})",
            manufacturer="LG",
        )
        self._attr_current_option = None

    async def async_update(self) -> None:
        """Fetch the latest state of the picture mode."""
        try:
            payload = {"category": "picture", "keys": ["pictureMode"]}
            ret = await self._client.request("settings/getSystemSettings", payload=payload)
            settings = ret.get("settings", {})
            if "pictureMode" in settings:
                mode = settings["pictureMode"]
                # Add it to options if it's an unknown mode the TV reported
                if mode not in self._attr_options:
                    self._attr_options.append(mode)
                self._attr_current_option = mode
        except Exception as e:
            _LOGGER.error("Failed to fetch picture mode settings: %s", e)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            uri = "com.webos.settingsservice/setSystemSettings"
            params = {"category": "picture", "settings": {"pictureMode": option}}
            
            await self._async_luna_request(uri, params)
            self._attr_current_option = option
        except Exception as e:
            _LOGGER.error("Failed to set picture mode to %s: %s", option, e)

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
