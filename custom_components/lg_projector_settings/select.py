"""Select platform for LG Projector Settings."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_HOST, PICTURE_MODES, SDR_MODES, HDR_MODES, DOLBY_VISION_MODES

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)

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
        self._attr_available = client.is_connected()

    async def _async_ensure_connected(self) -> bool:
        """Ensure the client is connected to the projector."""
        if self._client.is_connected():
            return True

        try:
            async with asyncio.timeout(5):
                await self._client.connect()
            self._attr_available = True
            return True
        except Exception as e:
            _LOGGER.debug("Projector %s is offline or unreachable: %s", self._host, e)
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._attr_available = False
            return False

    async def async_update(self) -> None:
        """Fetch the latest state of the picture mode."""
        if not await self._async_ensure_connected():
            return

        try:
            payload = {"category": "picture", "keys": ["pictureMode"]}
            ret = await self._client.request("settings/getSystemSettings", payload=payload)
            self._attr_available = True
            settings = ret.get("settings", {})
            mode = settings.get("pictureMode")
            if mode and isinstance(mode, str) and mode.strip():
                mode = mode.strip()
                # Determine which category the current mode belongs to
                if mode in DOLBY_VISION_MODES or "dolby" in mode.lower():
                    valid_options = DOLBY_VISION_MODES.copy()
                elif mode in HDR_MODES or mode.lower().startswith("hdr") or "hdr" in mode.lower():
                    valid_options = HDR_MODES.copy()
                else:
                    valid_options = SDR_MODES.copy()
                
                # Add it to options if it's an unknown mode the TV reported
                if mode not in valid_options:
                    valid_options.append(mode)
                        
                self._attr_options = valid_options
                self._attr_current_option = mode
        except Exception as e:
            _LOGGER.debug("Failed to fetch picture mode settings from %s: %s", self._host, e)
            if not self._client.is_connected():
                self._attr_available = False

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if not await self._async_ensure_connected():
            _LOGGER.error("Cannot set picture mode to %s: Projector %s is not connected", option, self._host)
            return

        try:
            uri = "com.webos.settingsservice/setSystemSettings"
            params = {"category": "picture", "settings": {"pictureMode": option}}
            
            await self._async_luna_request(uri, params)
            
            # The luna request trick doesn't return success/failure
            # Wait a moment for the projector to apply the setting, then poll to verify
            await asyncio.sleep(1)
            await self.async_update()
            
            if self._attr_current_option != option:
                _LOGGER.warning(
                    "Set picture mode to %s may have failed, current mode is %s", 
                    option, 
                    self._attr_current_option
                )
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
