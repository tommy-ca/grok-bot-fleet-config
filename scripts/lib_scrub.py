"""Shared scrub helpers for fleet-config verify / serialize."""
from __future__ import annotations

import re
from typing import Iterable

HEX8_RE = re.compile(r"\b[0-9a-f]{8}\b", re.I)

# Historical short room ids still cited in operator notes. Tokens are replaced
# in pack output; this map only chooses room:<name> vs [room-id].
DEFAULT_ROOM_SHORT_IDS: dict[str, str] = {
    "fea03f4a": "QStack",
    "75b15bb0": "Ferro",
    "cb3014b1": "Ferro",
    "58226516": "Eng lead",
    "c2b33e48": "QStack R&D",
}

ROOM_ID_PLACEHOLDER = "[room-id]"

SEED_SKILL_SLUGS = (
    "fleet-config-export",
    "fleet-config-import",
    "fleet-config-bootstrap",
)

_TABLE_ID_NAME_RE = re.compile(
    r"^\|\s*`?([0-9a-f]{8})`?(?:\s*\([^)|]*\))?\s*\|\s*([^|\n]+?)\s*\|",
    re.I | re.M,
)
_MAPS_TO_KEEP_RE = re.compile(
    r"(?P<name>[A-Za-z][^`\n→\-]{0,60}?)\s*(?:→|->)\s*maps to keep\s*`(?P<id>[0-9a-f]{8})`",
    re.I,
)
_KEEP_NAME_ID_RE = re.compile(
    r"keep\s+(?P<name>[A-Za-z][\w ./-]{0,40}?)\s*`(?P<id>[0-9a-f]{8})`",
    re.I,
)
_LEGACY_ID_RE = re.compile(
    r"`(?P<id>[0-9a-f]{8})`\s*\(\s*legacy\s+(?P<name>[^)]+)\)",
    re.I,
)
_CREATED_ID_RE = re.compile(
    r"(?P<name>Ferro|QStack|Eng lead|Fleet meta|grok-build-plugins)"
    r"[^`\n]{0,80}?created\s*`(?P<id>[0-9a-f]{8})`",
    re.I,
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


def _clean_room_name(raw: str) -> str:
    name = re.sub(r"[*_`]", "", raw or "").strip()
    name = re.split(r"\s*\(", name, 1)[0].strip()
    # Drop trailing fluff like "room (eng)" leftovers already split
    if name.lower().endswith(" room"):
        name = name[: -len(" room")].strip()
    return name


def extract_hex8_room_names(text: str) -> dict[str, str]:
    """Best-effort lowercase hex8 → room display name from rooms-map-like markdown."""
    mapping: dict[str, str] = dict(DEFAULT_ROOM_SHORT_IDS)
    if not isinstance(text, str) or not text:
        return mapping

    for m in _TABLE_ID_NAME_RE.finditer(text):
        tok = m.group(1).lower()
        name = _clean_room_name(m.group(2))
        if not name or name.lower() in {"intended name", "was", "id", "---"}:
            continue
        mapping[tok] = name

    for m in _MAPS_TO_KEEP_RE.finditer(text):
        tok = m.group("id").lower()
        name = _clean_room_name(m.group("name"))
        if name:
            mapping[tok] = name

    for m in _KEEP_NAME_ID_RE.finditer(text):
        tok = m.group("id").lower()
        name = _clean_room_name(m.group("name"))
        if name:
            mapping[tok] = name

    for m in _LEGACY_ID_RE.finditer(text):
        tok = m.group("id").lower()
        name = _clean_room_name(m.group("name"))
        if name:
            mapping[tok] = name

    for m in _CREATED_ID_RE.finditer(text):
        tok = m.group("id").lower()
        name = _clean_room_name(m.group("name"))
        if name:
            mapping[tok] = name

    return mapping


def scrub_hex8(text: str, id_to_name: dict[str, str] | None = None) -> str:
    """Replace \\b[0-9a-f]{8}\\b with room:<name> when known, else [room-id]."""
    if not isinstance(text, str) or not text:
        return text
    mapping = {k.lower(): v for k, v in (id_to_name or DEFAULT_ROOM_SHORT_IDS).items()}

    def _sub(m: re.Match[str]) -> str:
        tok = m.group(0).lower()
        name = mapping.get(tok)
        if name:
            return f"room:{name}"
        return ROOM_ID_PLACEHOLDER

    return HEX8_RE.sub(_sub, text)
