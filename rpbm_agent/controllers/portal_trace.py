"""Traçage HTTP des agents portails (X'Glass, VSF).

Permet de déboguer l'authentification et le scraping sans rejouer le widget :
chaque requête sortante (redirections comprises) est journalisée — méthode,
URL, statut, cible de redirection, cookies posés — et le corps des réponses
peut être écrit sur disque pour inspecter le HTML réellement reçu.

Activation :
- hors Odoo : `configure(True, dump_dir=...)`, voir `debug_portals.py` ;
- sur une instance Odoo : paramètre système `rpbm_agent.trace` à `1`
  (et `rpbm_agent.trace_dir` pour les dumps), relu à chaque `/rpbm_agent_auth`.

Les valeurs des champs sensibles (mot de passe, jeton CSRF) et des cookies
sont systématiquement masquées — ce module ne doit jamais faire fuiter les
identifiants dans les logs Odoo.
"""

import logging
import os
import re
from pathlib import Path
from urllib.parse import parse_qsl

_logger = logging.getLogger(__name__)

_SECRET_RE = re.compile(r"pass|pwd|token|secret", re.I)

_enabled = bool(os.getenv("RPBM_TRACE"))
_dump_dir = None
_seq = 0


def configure(enabled=True, dump_dir=None):
    """Active/désactive le traçage. `dump_dir` non vide => dump des corps."""
    global _enabled, _dump_dir, _seq
    _enabled = bool(enabled)
    _dump_dir = Path(dump_dir) if dump_dir else None
    _seq = 0
    if _dump_dir:
        _dump_dir.mkdir(parents=True, exist_ok=True)
    return _enabled


def enabled():
    return _enabled


def attach(session, portal):
    """Branche le traçage sur une `requests.Session` (appelé à sa création)."""
    session.hooks["response"].append(lambda r, *a, **k: _trace(portal, r))


def _redact_body(body):
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    if not isinstance(body, str) or not body:
        return ""
    pairs = parse_qsl(body, keep_blank_values=True)
    if not pairs:
        return body[:200]
    return "&".join(f"{k}={'***' if _SECRET_RE.search(k) else v}" for k, v in pairs)


def _slug(url):
    return re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[-1])[:60]


def _trace(portal, r):
    if not _enabled:
        return
    global _seq
    _seq += 1
    req = r.request
    parts = [f"[{portal}#{_seq:03d}] {req.method} {req.url} -> {r.status_code}"]
    if r.is_redirect:
        parts.append(f"redirect -> {r.headers.get('Location', '')}")
    body = _redact_body(req.body)
    if body:
        parts.append(f"body: {body}")
    if "Set-Cookie" in r.headers:
        parts.append("Set-Cookie: " + re.sub(r"=[^;,]+", "=***", r.headers["Set-Cookie"]))
    parts.append(f"{r.elapsed.total_seconds() * 1000:.0f} ms, {len(r.content)} o")
    _logger.info(" | ".join(parts))
    if _dump_dir:
        dump = _dump_dir / f"{portal}-{_seq:03d}-{r.status_code}-{_slug(req.url)}.html"
        dump.write_bytes(r.content)
