"""Shared scrub helpers for fleet-config verify / serialize."""
from __future__ import annotations

import re
from typing import Iterable

HEX8_RE = re.compile(r"\b[0-9a-f]{8}\b", re.I)

SEED_SKILL_SLUGS = (
    "fleet-config-export",
    "fleet-config-import",
    "fleet-config-bootstrap",
)


def normalize_hex8_allowlist(raw: object) -> set[str]:
    """Return lowercase 8-hex tokens from pack.hex8Allowlist (or empty)."""
    if raw is None:
        return set()
    if not isinstance(raw, list):
        return set()
    out: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        tok = item.strip().lower()
        if HEX8_RE.fullmatch(tok):
            out.add(tok)
    return out


def hex8_hits_in_text(text: str) -> list[str]:
    if not isinstance(text, str) or not text:
        return []
    return HEX8_RE.findall(text)


def find_fleetdoc_hex8(
    pack: dict,
    allowlist: Iterable[str] | None = None,
) -> list[tuple[str, str]]:
    """Return (fleetDoc.path, token) for unallowlisted hex8 in fleetDocs[].content."""
    allowed = {a.lower() for a in (allowlist or [])}
    if allowlist is None:
        allowed = normalize_hex8_allowlist(pack.get("hex8Allowlist"))
    hits: list[tuple[str, str]] = []
    for doc in pack.get("fleetDocs") or []:
        if not isinstance(doc, dict):
            continue
        path = str(doc.get("path") or "")
        content = doc.get("content")
        if not isinstance(content, str):
            continue
        for tok in hex8_hits_in_text(content):
            if tok.lower() in allowed:
                continue
            hits.append((path, tok))
    return hits
