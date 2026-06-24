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
        async with asyncio.timeout(10):
            await client.connect()
    except Exception as e:
        _LOGGER.error("Error connecting to LG Projector %s: %s", host, e)
        # We return False here, HA will retry setup automatically later if it fails to connect initially.
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client = hass.data[DOMAIN].pop(entry.entry_id)
        if client:
            await client.disconnect()

    return unload_ok
