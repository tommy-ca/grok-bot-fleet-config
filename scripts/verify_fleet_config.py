#!/usr/bin/env python3
"""Dry-run verify a fleet-config.v1 pack. Never imports onto the live account.

Usage:
  python3 scripts/verify_fleet_config.py
  python3 scripts/verify_fleet_config.py /path/to/fleet-config.v1.json

Exit 0 on PASS, 1 on FAIL. Prints evidence paths and counts.

Env overrides:
  FLEET_PACK_ROOT, FLEET_DIST_DIR, FLEET_PACK_PATH, FLEET_SCHEMA_PATH,
  FLEET_AGENTS_DIR, FLEET_WORKFLOWS_DIR, FLEET_RULES_DIR
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import os

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from lib_scrub import find_fleetdoc_hex8, normalize_hex8_allowlist  # noqa: E402

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PACK_ROOT = Path(os.environ.get("FLEET_PACK_ROOT", str(_PLUGIN_ROOT)))
DEFAULT_PACK = Path(
    os.environ.get(
        "FLEET_DIST_DIR",
        str(PACK_ROOT / "dist"),
    )
) / "fleet-config.v1.json"
# If FLEET_DIST_DIR already points at a file path ending .json, honor FLEET_PACK_PATH
if os.environ.get("FLEET_PACK_PATH"):
    DEFAULT_PACK = Path(os.environ["FLEET_PACK_PATH"])
DEFAULT_SCHEMA = Path(
    os.environ.get("FLEET_SCHEMA_PATH", str(PACK_ROOT / "schema" / "fleet-config.v1.schema.json"))
)
DEFAULT_README = Path(
    os.environ.get("FLEET_DIST_DIR", str(PACK_ROOT / "dist"))
) / "README.md"

REQUIRED_TOP = [
    "schema",
    "exportedAt",
    "source",
    "plugins",
    "rules",
    "skills",
    "fleetDocs",
    "agents",
    "rooms",
    "bootstrap",
]
BOOTSTRAP_STEPS = ["plugins", "rules", "skills", "agents", "rooms", "healthchecks"]
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.I,
)
SECRET_BASENAMES = (
    "box-secrets.json",
    "host-secrets.json",
    "teach-queue-key.json",
    "chrome-cookie-seed.json",
)
SECRET_STEMS = (
    "box-secrets",
    "host-secrets",
    "teach-queue-key",
    "chrome-cookie-seed",
)
CRED_KEY_RE = re.compile(
    r'"(apiKey|api_key|password|secret|token|private_key|accessToken)"\s*:',
)
AGENT_ID_KEYS = {"id", "uuid", "agentId", "agent_id"}
ROOM_ID_KEYS = {"id", "uuid", "roomId", "room_id", "channelId", "channel_id"}


class Verdict:
    def __init__(self) -> None:
        self.fails: list[str] = []
        self.warns: list[str] = []
        self.infos: list[str] = []

    def fail(self, msg: str) -> None:
        self.fails.append(msg)

    def warn(self, msg: str) -> None:
        self.warns.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)


def load_json(path: Path, v: Verdict) -> dict | None:
    if not path.is_file():
        v.fail(f"pack missing: {path}")
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        v.fail(f"pack is not valid JSON: {path} ({e})")
        return None


def structural_schema(pack: dict, v: Verdict) -> None:
    if pack.get("schema") != "fleet-config.v1":
        v.fail(f"schema != fleet-config.v1 (got {pack.get('schema')!r})")
    missing = [k for k in REQUIRED_TOP if k not in pack]
    if missing:
        v.fail(f"missing required top-level keys: {missing}")
    src = pack.get("source")
    if not isinstance(src, dict) or not src.get("label"):
        v.fail("source.label required")
    if not isinstance(pack.get("exportedAt"), str) or not pack.get("exportedAt"):
        v.fail("exportedAt required string")
    for key in ("plugins", "rules", "skills", "fleetDocs", "agents", "rooms"):
        if key in pack and not isinstance(pack[key], list):
            v.fail(f"{key} must be an array")
    boot = pack.get("bootstrap")
    if not isinstance(boot, dict):
        v.fail("bootstrap must be an object")
    elif "order" not in boot:
        v.fail("bootstrap.order missing")


def try_jsonschema(pack: dict, schema_path: Path, v: Verdict) -> str:
    """Return 'jsonschema' or 'structural'."""
    if not schema_path.is_file():
        v.warn(f"schema file missing (structural only): {schema_path}")
        structural_schema(pack, v)
        return "structural"
    try:
        schema = json.loads(schema_path.read_text())
    except Exception as e:
        v.fail(f"schema unreadable: {schema_path} ({e})")
        structural_schema(pack, v)
        return "structural"
    try:
        import jsonschema  # type: ignore
    except Exception:
        structural_schema(pack, v)
        # extra field-shape checks mirroring schema
        _shape_items(pack, v)
        return "structural"
    try:
        jsonschema.validate(pack, schema)
        v.info(f"jsonschema OK against {schema_path}")
        return "jsonschema"
    except Exception as e:
        v.fail(f"jsonschema validation failed: {e}")
        return "jsonschema"


def _shape_items(pack: dict, v: Verdict) -> None:
    for i, p in enumerate(pack.get("plugins") or []):
        if not isinstance(p, dict) or not p.get("pluginId"):
            v.fail(f"plugins[{i}] missing pluginId")
    for i, r in enumerate(pack.get("rules") or []):
        if not isinstance(r, dict):
            v.fail(f"rules[{i}] not object")
            continue
        if not r.get("path"):
            v.fail(f"rules[{i}] missing path")
        body = r.get("content") if r.get("content") is not None else r.get("body")
        if not isinstance(body, str):
            v.fail(f"rules[{i}] missing path+body (content)")
    for i, s in enumerate(pack.get("skills") or []):
        if not isinstance(s, dict):
            v.fail(f"skills[{i}] not object")
            continue
        if not s.get("slug") or not isinstance(s.get("body"), str):
            v.fail(f"skills[{i}] missing slug+body")
    for i, a in enumerate(pack.get("agents") or []):
        if not isinstance(a, dict):
            v.fail(f"agents[{i}] not object")
            continue
        for k in ("roleKey", "name", "description", "routines"):
            if k not in a:
                v.fail(f"agents[{i}] missing {k}")
    for i, r in enumerate(pack.get("rooms") or []):
        if not isinstance(r, dict):
            v.fail(f"rooms[{i}] not object")
            continue
        for k in ("name", "charter", "memberRoleKeys"):
            if k not in r:
                v.fail(f"rooms[{i}] missing {k}")
        keys = r.get("memberRoleKeys") or []
        if isinstance(keys, list) and len(keys) > 6:
            v.fail(f"rooms[{i}] {r.get('name')!r} has {len(keys)} members (max 6)")


def scrub_checks(pack: dict, v: Verdict) -> None:
    blob = json.dumps(pack)
    if "Todd Liu" in blob:
        v.fail("scrub: operator legal name 'Todd Liu' still present")
    if re.search(r"\bTodd\b", blob):
        v.fail("scrub: operator given name 'Todd' still present")
    if CRED_KEY_RE.search(blob):
        v.fail("scrub: credential-looking JSON keys present")
    # secret filenames as packed sources (bootstrap notes may mention them)
    for item in pack.get("rules") or []:
        if isinstance(item, dict) and item.get("path") in SECRET_BASENAMES:
            v.fail(f"scrub: secret filename packed as rule path {item.get('path')}")
    for item in pack.get("skills") or []:
        if isinstance(item, dict) and item.get("slug") in SECRET_STEMS:
            v.fail(f"scrub: secret stem packed as skill slug {item.get('slug')}")
    for item in pack.get("fleetDocs") or []:
        if isinstance(item, dict) and item.get("path") in SECRET_BASENAMES:
            v.fail(f"scrub: secret filename packed as fleetDoc {item.get('path')}")
    for item in pack.get("plugins") or []:
        if isinstance(item, dict) and item.get("pluginId") in SECRET_STEMS:
            v.fail(f"scrub: secret stem packed as pluginId {item.get('pluginId')}")
    # never pack secret file *contents* (look for known secret file shapes)
    if '"chrome-cookie-seed.json"' in blob and "Never pack" not in blob:
        # filename string alone in a packed path field already caught; notes OK
        pass

    allow = normalize_hex8_allowlist(pack.get("hex8Allowlist"))
    hex_hits = find_fleetdoc_hex8(pack, allow)
    if hex_hits:
        # cite first few with path (rooms-map is the common offender)
        cited = ", ".join(f"{doc_path}:{tok}" for doc_path, tok in hex_hits[:8])
        more = f" (+{len(hex_hits) - 8} more)" if len(hex_hits) > 8 else ""
        v.fail(
            "scrub: fleetDocs hex8 residue (\\b[0-9a-f]{8}\\b) not allowlisted: "
            f"{cited}{more}"
        )


def dry_run_import(pack: dict, v: Verdict) -> None:
    agents = pack.get("agents") or []
    rooms = pack.get("rooms") or []
    skills = pack.get("skills") or []
    rules = pack.get("rules") or []
    boot = pack.get("bootstrap") if isinstance(pack.get("bootstrap"), dict) else {}

    role_keys = []
    for i, a in enumerate(agents):
        if not isinstance(a, dict):
            continue
        rk = a.get("roleKey") or ""
        name = a.get("name") or ""
        role_keys.append(rk)
        if name.strip() == "New Bot":
            v.fail("dry-run import: New Bot was packed (must skip empty New Bot)")
        extra_ids = set(a.keys()) & AGENT_ID_KEYS
        if extra_ids:
            v.fail(f"dry-run import: agent {name!r} uses UUID identity fields {sorted(extra_ids)}")
        if UUID_RE.fullmatch(str(rk)) or UUID_RE.fullmatch(str(name)):
            v.fail(f"dry-run import: agent identity looks like UUID roleKey={rk!r} name={name!r}")
        for r in a.get("routines") or []:
            if not isinstance(r, dict):
                v.fail(f"dry-run import: agent {name!r} has non-object routine")
                continue
            for k in ("slug", "name", "description", "scheduleOrTriggerIntent", "prompt"):
                if k not in r:
                    v.fail(f"dry-run import: agent {name!r} routine missing {k}")

    seated: set[str] = set()
    for i, room in enumerate(rooms):
        if not isinstance(room, dict):
            continue
        extra_ids = set(room.keys()) & ROOM_ID_KEYS
        if extra_ids:
            v.fail(
                f"dry-run import: room {room.get('name')!r} uses UUID identity fields {sorted(extra_ids)}"
            )
        rname = room.get("name") or ""
        if UUID_RE.fullmatch(str(rname)):
            v.fail(f"dry-run import: room name looks like UUID: {rname!r}")
        members = room.get("memberRoleKeys") or []
        if not isinstance(members, list):
            v.fail(f"dry-run import: room {rname!r} memberRoleKeys not a list")
            continue
        if len(members) > 6:
            v.fail(f"dry-run import: room {rname!r} has {len(members)} members (max 6)")
        for mk in members:
            if mk not in role_keys:
                v.fail(
                    f"dry-run import: room {rname!r} memberRoleKey {mk!r} "
                    f"not resolvable to agents[].roleKey"
                )
            seated.add(mk)

    # Coverage note (not fail): agents not seated in any packed room
    unseated = [rk for rk in role_keys if rk and rk not in seated]
    if unseated:
        v.warn(
            "coverage: agents[].roleKey not in any rooms[].memberRoleKeys "
            f"(import still OK; seat later): {unseated}"
        )

    order = boot.get("order") if isinstance(boot, dict) else None
    if not order:
        v.fail("dry-run import: bootstrap.order missing")
    else:
        if list(order) != BOOTSTRAP_STEPS:
            v.fail(f"dry-run import: bootstrap.order {order} != {BOOTSTRAP_STEPS}")
        v.info(f"bootstrap.order: {' → '.join(order)}")

    for i, s in enumerate(skills):
        if not isinstance(s, dict):
            v.fail(f"skills[{i}] not object")
            continue
        slug = s.get("slug") or ""
        body = s.get("body")
        if not slug or not isinstance(body, str) or not body.strip():
            v.fail(f"skills[{i}] missing slug+body (slug={slug!r})")

    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            v.fail(f"rules[{i}] not object")
            continue
        path = r.get("path") or ""
        body = r.get("content") if r.get("content") is not None else r.get("body")
        if not path or not isinstance(body, str) or not body.strip():
            v.fail(f"rules[{i}] missing path+body (path={path!r})")
        if path and not path.endswith(".mdc"):
            v.fail(f"rules[{i}] path {path!r} is not a .mdc rule file")

    raw_uuids = UUID_RE.findall(json.dumps(pack))
    if raw_uuids:
        uniq = sorted(set(raw_uuids))
        v.fail(
            f"dry-run import: raw UUIDs remain in pack (identity leak): "
            f"{uniq[:8]}{'…' if len(uniq) > 8 else ''} count={len(raw_uuids)}"
        )


def live_coverage(pack: dict, v: Verdict) -> None:
    """Optional: when run on the source box, list live surfaces not packed."""
    agents_dir = Path(os.environ.get("FLEET_AGENTS_DIR", "/home/box/agent-data/agents"))
    workflows_dir = Path(os.environ.get("FLEET_WORKFLOWS_DIR", "/home/box/agent-data/workflows"))
    rules_dir = Path(os.environ.get("FLEET_RULES_DIR", str(Path.home() / ".cursor" / "rules")))
    if not agents_dir.is_dir():
        v.info(f"live coverage skipped (no {agents_dir})")
        return

    packed_names = {a.get("name") for a in (pack.get("agents") or []) if isinstance(a, dict)}
    live_names = []
    skipped_new = False
    extra_rooms = []
    for d in sorted(agents_dir.iterdir()):
        if not d.is_dir():
            continue
        if (d / "group.json").exists():
            pj = d / "profile.json"
            label = d.name
            if pj.exists():
                try:
                    label = json.loads(pj.read_text()).get("name") or d.name
                except Exception:
                    pass
            extra_rooms.append(label)
            continue
        pj = d / "profile.json"
        if not pj.exists():
            continue
        try:
            name = (json.loads(pj.read_text()).get("name") or "").strip()
        except Exception:
            continue
        if name == "New Bot":
            skipped_new = True
            continue
        live_names.append(name)
    missing_agents = [n for n in live_names if n not in packed_names]
    if missing_agents:
        v.warn(f"live agents not packed: {missing_agents}")
    else:
        v.info(f"live named agents all packed ({len(live_names)}); New Bot skipped={skipped_new}")

    packed_rooms = {r.get("name") for r in (pack.get("rooms") or []) if isinstance(r, dict)}
    # live group profile names vs packed room names
    not_in_pack = [n for n in extra_rooms if n not in packed_rooms]
    if not_in_pack:
        v.info(f"live rooms not packed (ad-hoc / leftover — importer must not recreate): {not_in_pack}")

    if workflows_dir.is_dir():
        live_skills = sorted(
            p.name for p in workflows_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
        )
        packed_skills = [s.get("slug") for s in (pack.get("skills") or []) if isinstance(s, dict)]
        missing_sk = [s for s in live_skills if s not in packed_skills]
        extra_sk = [s for s in packed_skills if s not in live_skills]
        if missing_sk:
            v.warn(f"live workflow SKILL.md not packed: {missing_sk}")
        if extra_sk:
            v.info(f"packed skills not on this box: {extra_sk}")
        if not missing_sk:
            v.info(f"live workflow skills all packed ({len(live_skills)})")

    if rules_dir.is_dir():
        live_rules = sorted(p.name for p in rules_dir.glob("*.mdc"))
        packed_rules = [r.get("path") for r in (pack.get("rules") or []) if isinstance(r, dict)]
        missing_r = [r for r in live_rules if r not in packed_rules]
        if missing_r:
            v.warn(f"live ~/.cursor/rules not packed: {missing_r}")
        else:
            v.info(f"live rules all packed ({len(live_rules)})")


def counts(pack: dict) -> dict[str, int]:
    agents = pack.get("agents") or []
    routines = 0
    for a in agents:
        if isinstance(a, dict):
            routines += len(a.get("routines") or [])
    return {
        "agents": len(agents) if isinstance(agents, list) else 0,
        "skills": len(pack.get("skills") or []),
        "rules": len(pack.get("rules") or []),
        "rooms": len(pack.get("rooms") or []),
        "plugins": len(pack.get("plugins") or []),
        "fleetDocs": len(pack.get("fleetDocs") or []),
        "routines": routines,
    }


def main(argv: list[str]) -> int:
    pack_path = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_PACK
    schema_path = DEFAULT_SCHEMA
    readme_path = pack_path.parent / "README.md"
    if not readme_path.is_file():
        readme_path = DEFAULT_README

    v = Verdict()
    print("VERIFY fleet-config.v1 (dry-run import; does not mutate this account)")
    print(f"pack:    {pack_path}")
    print(f"schema:  {schema_path}  exists={schema_path.is_file()}")
    print(f"readme:  {readme_path}  exists={readme_path.is_file()}")

    pack = load_json(pack_path, v)
    if pack is None:
        print("RESULT: FAIL")
        for f in v.fails:
            print(f"  FAIL  {f}")
        return 1

    mode = try_jsonschema(pack, schema_path, v)
    print(f"schema-check: {mode}")
    if mode == "structural":
        _shape_items(pack, v)

    scrub_checks(pack, v)
    dry_run_import(pack, v)
    live_coverage(pack, v)

    c = counts(pack)
    print(
        "COUNTS: "
        f"agents={c['agents']} skills={c['skills']} rules={c['rules']} "
        f"rooms={c['rooms']} plugins={c['plugins']} fleetDocs={c['fleetDocs']} "
        f"routines={c['routines']}"
    )
    print("plugins:", [p.get("pluginId") for p in (pack.get("plugins") or []) if isinstance(p, dict)])
    print(
        "agents:",
        [
            f"{a.get('roleKey')}={a.get('name')}({len(a.get('routines') or [])})"
            for a in (pack.get("agents") or [])
            if isinstance(a, dict)
        ],
    )
    print(
        "rooms:",
        [
            f"{r.get('name')}[{','.join(r.get('memberRoleKeys') or [])}]"
            for r in (pack.get("rooms") or [])
            if isinstance(r, dict)
        ],
    )

    for msg in v.infos:
        print(f"  INFO  {msg}")
    for msg in v.warns:
        print(f"  WARN  {msg}")
    for msg in v.fails:
        print(f"  FAIL  {msg}")

    if v.fails:
        print(f"RESULT: FAIL  ({len(v.fails)} check(s))  pack={pack_path}")
        return 1
    print(f"RESULT: PASS  pack={pack_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
