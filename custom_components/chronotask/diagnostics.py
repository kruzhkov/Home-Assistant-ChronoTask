from __future__ import annotations

import copy

from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN, INTEGRATION_VERSION

# Campi potenzialmente sensibili (es. token, password, API key). Attenzione a NON
# mettere qui "service_data"/"end_service_data": sono contenitori e verrebbero
# sostituiti in blocco, nascondendo anche campi utili al debug come entity_id.
_REDACT_FIELDS = {
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "client_secret",
    "secret",
    "pin",
}


def _redact_rule(rule: dict) -> dict:
    """Edita i service_data della singola regola prima del redact globale.

    ``async_redact_data`` non attraversa in modo affidabile le liste annidate
    (``rules`` è una lista di dict), quindi i segreti dentro le regole vanno
    rimossi esplicitamente qui.
    """
    clean = copy.deepcopy(rule)
    for field in ("service_data", "end_service_data"):
        value = clean.get(field)
        if isinstance(value, dict):
            clean[field] = async_redact_data(value, _REDACT_FIELDS)
    return clean


async def async_get_config_entry_diagnostics(hass, entry):
    ctx = (hass.data.get(DOMAIN) or {}).get(entry.entry_id)
    if not ctx:
        # Entry non (ancora) caricata: meglio un documento minimo che un crash
        # nella pagina di diagnostica.
        return {"version": INTEGRATION_VERSION, "loaded": False}

    storage = ctx["storage"]
    rules = storage.list_rules()
    data = {
        "name": ctx.get("name"),
        "version": INTEGRATION_VERSION,
        "loaded": True,
        "rules": [_redact_rule(r) for r in rules],
        "active_rules": sum(1 for r in rules if r.get("enabled", True)),
        "holds": storage.list_holds(),
    }
    return async_redact_data(data, _REDACT_FIELDS)
