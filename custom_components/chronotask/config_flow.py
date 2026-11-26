from __future__ import annotations

import re

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_NAME, DOMAIN


def _slugify(text: str) -> str:
    """Crea uno slug dal nome del planner per l'unique_id.

    Deve mantenere le lettere non-ASCII (es. cirillico, accenti): usando solo
    ``[a-z0-9]`` nomi diversi come "Отопление" e "Освещение" collassavano sullo
    stesso slug "planner", rendendo impossibile creare più planner.
    """
    t = str(text or "planner").strip().lower()
    t = re.sub(r"[^\w]+", "_", t, flags=re.UNICODE)
    t = t.strip("_")
    return t or "planner"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            title = (user_input.get(CONF_NAME) or "ChronoTask").strip()
            unique_id = _slugify(title)

            # Evita duplicati con lo stesso nome
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=title, data={CONF_NAME: title})

        data_schema = vol.Schema({
            vol.Optional(CONF_NAME, default="ChronoTask"): str,
        })
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        # Home Assistant >= 2024.11 imposta da sé `self.config_entry`:
        # passare l'entry al costruttore è deprecato.
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Permette di rinominare il planner dopo la creazione."""

    def _entry(self):
        """ConfigEntry della flow.

        Da HA 2024.11 il framework imposta ``self.config_entry``; con le
        versioni precedenti (minimo supportato 2024.7) la stessa entry va
        recuperata dall'``handler``, cioè l'entry_id della flow.
        """
        entry = getattr(self, "config_entry", None)
        if entry is None:
            entry = self.hass.config_entries.async_get_entry(self.handler)
        return entry

    async def async_step_init(self, user_input=None):
        entry = self._entry()
        if user_input is not None:
            new_name = (user_input.get(CONF_NAME) or "ChronoTask").strip()
            # Aggiorna il titolo dell'entry
            self.hass.config_entries.async_update_entry(
                entry,
                title=new_name,
                data={**entry.data, CONF_NAME: new_name},
            )
            return self.async_create_entry(title=new_name, data={})

        current_name = entry.data.get(CONF_NAME, entry.title)
        data_schema = vol.Schema({
            vol.Optional(CONF_NAME, default=current_name): str,
        })
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
