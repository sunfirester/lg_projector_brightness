"""Select platform for LG Projector Settings."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_DOLBY_VISION_VALUE,
    CONF_HDR_SENSOR,
    CONF_HDR_VALUE,
    CONF_HOST,
    DEFAULT_DOLBY_VISION_VALUE,
    DEFAULT_HDR_VALUE,
    DOLBY_VISION_MODES,
    DOMAIN,
    HDR_MODES,
    PICTURE_MODES,
    SDR_MODES,
)

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

    async_add_entities([LgProjectorPictureMode(client, host, entry)])

class LgProjectorPictureMode(SelectEntity, RestoreEntity):
    """Representation of the LG Projector Picture Mode select entity."""

    _attr_has_entity_name = True
    _attr_name = "Picture Mode"
    _attr_options = PICTURE_MODES
    _attr_icon = "mdi:television-guide"
    _attr_should_poll = True

    def __init__(self, client, host, entry: ConfigEntry):
        """Initialize the select entity."""
        self._client = client
        self._host = host
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_picture_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"LG Projector ({host})",
            manufacturer="LG",
        )
        self._attr_current_option = None
        self._attr_available = client.is_connected()
        self._hdr_sensor = entry.options.get(CONF_HDR_SENSOR)
        self._hdr_values = [
            v.strip().lower()
            for v in entry.options.get(CONF_HDR_VALUE, DEFAULT_HDR_VALUE).split(",")
            if v.strip()
        ]
        self._dolby_values = [
            v.strip().lower()
            for v in entry.options.get(
                CONF_DOLBY_VISION_VALUE, DEFAULT_DOLBY_VISION_VALUE
            ).split(",")
            if v.strip()
        ]

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant."""
        await super().async_added_to_hass()

        # Restore previous selection across restarts
        if (last_state := await self.async_get_last_state()) is not None:
            if (
                last_state.state
                and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
            ):
                self._attr_current_option = last_state.state

        # Track external HDR sensor if configured
        if self._hdr_sensor:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._hdr_sensor], self._async_hdr_sensor_changed
                )
            )
            # Evaluate initial state of HDR sensor
            if sensor_state := self.hass.states.get(self._hdr_sensor):
                self._update_options_from_hdr_state(sensor_state.state)
            else:
                self._update_options_from_hdr_state(None)
        else:
            self._update_options_from_hdr_state(None)

    @callback
    def _async_hdr_sensor_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle state change of the configured HDR sensor."""
        new_state = event.data.get("new_state")
        state_str = new_state.state if new_state else None
        self._update_options_from_hdr_state(state_str)
        self.async_write_ha_state()

    def _update_options_from_hdr_state(self, state_str: str | None) -> None:
        """Update available options based on HDR sensor state."""
        if not state_str or state_str.lower() in (STATE_UNKNOWN, STATE_UNAVAILABLE, "none", ""):
            # Fallback: sensor is unknown, unavailable, or not configured -> show all modes
            valid_options = PICTURE_MODES.copy()
        else:
            normalized = state_str.strip().lower()
            if any(val == normalized or val in normalized for val in self._dolby_values):
                valid_options = DOLBY_VISION_MODES.copy()
            elif any(val == normalized or val in normalized for val in self._hdr_values):
                valid_options = HDR_MODES.copy()
            else:
                # Sensor is reported active/valid, but not HDR/Dolby -> SDR mode
                valid_options = SDR_MODES.copy()

        # Ensure currently selected option is preserved in the dropdown so HA doesn't discard it
        if self._attr_current_option and self._attr_current_option not in valid_options:
            valid_options.append(self._attr_current_option)

        self._attr_options = valid_options

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
        """Check connection state and maintain availability."""
        if not await self._async_ensure_connected():
            return

        self._attr_available = True

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if not await self._async_ensure_connected():
            _LOGGER.error("Cannot set picture mode to %s: Projector %s is not connected", option, self._host)
            return

        try:
            uri = "com.webos.settingsservice/setSystemSettings"
            params = {"category": "picture", "settings": {"pictureMode": option}}
            
            await self._async_luna_request(uri, params)
            
            # Optimistically update current option so UI immediately reflects change
            self._attr_current_option = option

            # If no external HDR sensor is configured, dynamically adapt options to selected mode's category
            if not self._hdr_sensor:
                if option in DOLBY_VISION_MODES or "dolby" in option.lower():
                    valid_options = DOLBY_VISION_MODES.copy()
                elif option in HDR_MODES or option.lower().startswith("hdr") or "hdr" in option.lower():
                    valid_options = HDR_MODES.copy()
                else:
                    valid_options = SDR_MODES.copy()
                if option not in valid_options:
                    valid_options.append(option)
                self._attr_options = valid_options

            self.async_write_ha_state()
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
