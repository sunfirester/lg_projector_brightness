import logging
import asyncio
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult

import aiowebostv

from .const import DOMAIN, CONF_KEY

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
})

class LgProjectorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LG Projector Settings."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.host = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.host = user_input[CONF_HOST]
            
            # Ensure the device is not already configured
            await self.async_set_unique_id(self.host)
            self._abort_if_unique_id_configured()
            
            return await self.async_step_pairing()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_pairing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the pairing step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # User clicked submit, attempt to pair
            client = aiowebostv.WebOsClient(self.host, None)
            try:
                # Add a timeout so we don't hang forever
                async with asyncio.timeout(60):
                    await client.connect()
                
                if client.client_key:
                    key = client.client_key
                    await client.disconnect()
                    
                    return self.async_create_entry(
                        title=self.host,
                        data={CONF_HOST: self.host, CONF_KEY: key},
                    )
                else:
                    errors["base"] = "auth_error"
            except asyncio.TimeoutError:
                errors["base"] = "auth_error"
            except Exception as e:
                _LOGGER.error("Failed to connect to %s: %s", self.host, e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="pairing", errors=errors
        )
