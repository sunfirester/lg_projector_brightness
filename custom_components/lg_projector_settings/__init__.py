"""The LG Projector Settings integration."""
from __future__ import annotations

import logging
import asyncio

import aiowebostv

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_KEY

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SELECT]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LG Projector Settings from a config entry."""
    host = entry.data[CONF_HOST]
    key = entry.data[CONF_KEY]

    client = aiowebostv.WebOsClient(host, key)
    
    try:
        async with asyncio.timeout(5):
            await client.connect()
    except Exception as e:
        _LOGGER.warning(
            "Could not connect to LG Projector %s during setup (it may be off): %s. Will connect when online.",
            host,
            e,
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client = hass.data[DOMAIN].pop(entry.entry_id, None)
        if client and client.is_connected():
            await client.disconnect()

    return unload_ok
