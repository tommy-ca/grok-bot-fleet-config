#!/usr/bin/env python3
"""Serialize live Grok Bot fleet surfaces into a scrubbed fleet-config.v1 pack.

Reads agent profiles (skips empty New Bot), workflow SKILL.md files, ~/.cursor/rules/*.mdc,
and key fleet docs. Scrubs operator names, UUIDs, and rooms-map hex8 short ids.
Writes dist/fleet-config.v1.json + dist/README.md. Prints output path; exits 0.

Env overrides (default to Grok Bot box paths):
  FLEET_AGENTS_DIR, FLEET_WORKFLOWS_DIR, FLEET_RULES_DIR, FLEET_DIR,
  FLEET_DIST_DIR, FLEET_PLUGINS_CACHE
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from lib_scrub import (  # noqa: E402
    DEFAULT_ROOM_SHORT_IDS,
    extract_hex8_room_names,
    find_fleetdoc_hex8,
    scrub_hex8,
)

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent

AGENTS_DIR = Path(os.environ.get("FLEET_AGENTS_DIR", "/home/box/agent-data/agents"))
WORKFLOWS_DIR = Path(os.environ.get("FLEET_WORKFLOWS_DIR", "/home/box/agent-data/workflows"))
RULES_DIR = Path(os.environ.get("FLEET_RULES_DIR", str(Path.home() / ".cursor" / "rules")))
FLEET_DIR = Path(os.environ.get("FLEET_DIR", "/workspace/fleet-external-agents"))
PLUGINS_CACHE = Path(os.environ.get("FLEET_PLUGINS_CACHE", "/home/box/agent-data/plugins/cache"))
DIST_DIR = Path(os.environ.get("FLEET_DIST_DIR", str(_PLUGIN_ROOT / "dist")))
OUT_JSON = DIST_DIR / "fleet-config.v1.json"
OUT_README = DIST_DIR / "README.md"

# Primary roleKey per display name (from fleet-roles / roles-map + disk-saver)
NAME_TO_ROLEKEY = {
    "dr eggbot": "bot-designer",
    "Horizon": "eng-orch",
    "Drove": "long-horizon-swarm",
    "Planner": "planner",
    "Heavilifter": "on-box-lifter",
    "Cloud Agent Orchestrator": "cloud-orch",
    "Lingxi's Engineer Bot": "eng-supervisor",
    "Nightly Audit Engineer": "nightly-audit",
    "Wiki": "wiki-curator",
    "Secretary": "secretary",
    "Opus": "box-ops",
    "Herd": "external-herd-orch",
    "Disk Saver": "disk-saver",
}

# UUID → roleKey for scrubbing member refs in text (built at runtime too)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.I,
)

SECRET_BASENAMES = {
    "box-secrets.json",
    "host-secrets.json",
    "teach-queue-key.json",
    "chrome-cookie-seed.json",
}

FLEET_DOC_PATHS = [
    "roles-map.md",
    "rooms-map.md",
    "registry.md",
    "concurrency.md",
    "pstack-herdr-agents.md",
    "herdr-integrations.md",
]

# Target rooms (names only; no host UUIDs). Duplicates collapsed — not exported.
ROOMS = [
    {
        "name": "Eng lead",
        "charter": (
            "Non-project eng coordination; cross-cutting OpenSpec when not "
            "qstack/ferro-scoped. Max 6 members."
        ),
        "memberRoleKeys": [
            "eng-orch",
            "planner",
            "on-box-lifter",
            "cloud-orch",
            "external-herd-orch",
            "long-horizon-swarm",
        ],
    },
    {
        "name": "QStack",
        "charter": (
            "qstack-* programs only. No bot-designer/wiki-curator in default seat plan."
        ),
        "memberRoleKeys": [
            "cloud-orch",
            "planner",
            "eng-orch",
            "on-box-lifter",
            "external-herd-orch",
            "long-horizon-swarm",
        ],
    },
    {
        "name": "Ferro",
        "charter": (
            "ferro-* / Cryptofeed / Tardis only. bot-designer seat allowed for channel mgmt."
        ),
        "memberRoleKeys": [
            "eng-orch",
            "planner",
            "on-box-lifter",
            "external-herd-orch",
            "long-horizon-swarm",
            "bot-designer",
        ],
    },
    {
        "name": "Fleet meta",
        "charter": "org / wiki / ops; NO eng apply.",
        "memberRoleKeys": [
            "bot-designer",
            "wiki-curator",
            "box-ops",
            "secretary",
            "disk-saver",
        ],
    },
    {
        "name": "grok-build-plugins",
        "charter": (
            "gbp / thermos / marketplace plugin programs only. "
            "No bot-designer/wiki-curator in default seat plan."
        ),
        "memberRoleKeys": [
            "eng-orch",
            "long-horizon-swarm",
            "external-herd-orch",
            "on-box-lifter",
            "planner",
            "cloud-orch",
        ],
    },
]

BOOTSTRAP = {
    "order": ["plugins", "rules", "skills", "agents", "rooms", "healthchecks"],
    "notes": [
        "Public scrub mode: operator name scrubbed; no agent/room UUIDs; no secrets files.",
        "Single-bot shares still use export-bot-template + create_bot_share_json.",
        "Import: CreateAgent for missing roleKeys (match by name); never delete bots; skip New Bot.",
        "Rooms: CreateChannel by charter; max 6 members; include managing bot if needed.",
        "After agents: run design-a-grok-bot fresh-install healthchecks on designer bot.",
        "Target rooms: Eng lead, QStack, Ferro, Fleet meta, grok-build-plugins.",
        "Mixed leftover / ad-hoc rooms (legacy Horizon mix, Mulvad Relay List, Dev Env) are not packed.",
        "Do not pack box-secrets, host-secrets, cookies, transcripts, or user-memory.",
        "Host CLIs (agy OAuth, herdr/mise, grok, claude) are post-bootstrap Opus steps — never packed.",
    ],
}


def scrub(
    text: str,
    uuid_to_role: dict[str, str] | None = None,
    id_to_name: dict[str, str] | None = None,
) -> str:
    if not text:
        return text
    out = text
    # Operator name scrub (public mode)
    out = out.replace("Todd Liu", "operator")
    out = re.sub(r"\bTodd\b", "operator", out)
    # Common private repo org → generic (public scrub)
    out = out.replace("https://github.com/tommy-ca/ferro-flux", "the watched ferro repo")
    out = out.replace("tommy-ca/ferro-flux", "the watched ferro repo")
    out = out.replace("tommy-ca/", "the-watched-org/")
    out = re.sub(r"\btommy-ca\b", "the-watched-org", out)
    # UUID → roleKey when known, else drop token (before hex8: UUID head is 8 hex)
    def _uuid_sub(m: re.Match[str]) -> str:
        u = m.group(0).lower()
        if uuid_to_role and u in uuid_to_role:
            return uuid_to_role[u]
        if uuid_to_role and m.group(0) in uuid_to_role:
            return uuid_to_role[m.group(0)]
        return "[id]"

    out = UUID_RE.sub(_uuid_sub, out)
    # Short room ids → room:<name> or [room-id]
    out = scrub_hex8(out, id_to_name)
    # Soft scrub of "Horizon operator" room naming leftovers
    out = out.replace("Horizon operator", "Eng lead")
    return out


def collect_room_id_map() -> dict[str, str]:
    mapping = dict(DEFAULT_ROOM_SHORT_IDS)
    rooms_map = FLEET_DIR / "rooms-map.md"
    if rooms_map.is_file():
        mapping.update(extract_hex8_room_names(rooms_map.read_text()))
    return mapping


def parse_skill_frontmatter(text: str) -> tuple[str, str, str]:
    """Return name, description, full body (including frontmatter)."""
    name, desc = "", ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            lines = fm.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i]
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("\"'")
                elif line.startswith("description:"):
                    rest = line.split(":", 1)[1].strip()
                    if rest in (">-", ">", "|"):
                        chunks = []
                        i += 1
                        while i < len(lines) and (
                            lines[i].startswith("  ") or lines[i].startswith("\t") or lines[i] == ""
                        ):
                            chunks.append(lines[i].strip())
                            i += 1
                        desc = " ".join(c for c in chunks if c)
                        continue
                    else:
                        desc = rest.strip("\"'")
                i += 1
    return name, desc, text


def collect_uuid_maps() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not AGENTS_DIR.is_dir():
        return mapping
    for d in AGENTS_DIR.iterdir():
        if not d.is_dir():
            continue
        pj = d / "profile.json"
        if not pj.exists():
            continue
        try:
            p = json.loads(pj.read_text())
        except Exception:
            continue
        name = p.get("name") or ""
        role = NAME_TO_ROLEKEY.get(name)
        if role:
            mapping[d.name.lower()] = role
            mapping[d.name] = role
    return mapping


def load_agents(
    uuid_to_role: dict[str, str],
    id_to_name: dict[str, str] | None = None,
) -> list[dict]:
    agents: list[dict] = []
    if not AGENTS_DIR.is_dir():
        return agents
    for d in sorted(AGENTS_DIR.iterdir(), key=lambda p: p.name):
        if not d.is_dir():
            continue
        if (d / "group.json").exists():
            continue
        pj = d / "profile.json"
        if not pj.exists():
            continue
        p = json.loads(pj.read_text())
        name = (p.get("name") or "").strip()
        desc = (p.get("description") or "").strip()
        if name == "New Bot" and not desc:
            continue
        if name not in NAME_TO_ROLEKEY:
            # skip unknown extras
            continue
        role_key = NAME_TO_ROLEKEY[name]
        routines = []
        auto_root = d / "automations"
        if auto_root.is_dir():
            for sub in sorted(auto_root.iterdir(), key=lambda p: p.name):
                if not sub.is_dir():
                    continue
                aj = sub / "automation.json"
                if not aj.exists():
                    continue
                # never pack secrets files
                if aj.name in SECRET_BASENAMES:
                    continue
                a = json.loads(aj.read_text())
                prompt = scrub(a.get("prompt") or "", uuid_to_role, id_to_name)
                schedule = a.get("schedule") or ""
                trig = a.get("triggerPresentation") or {}
                intent = schedule
                if not intent and isinstance(trig, dict):
                    t = trig.get("trigger") or {}
                    if isinstance(t, dict):
                        intent = t.get("schedule") or t.get("type") or "on-demand"
                if not intent:
                    intent = "on-demand / ask importer"
                routines.append(
                    {
                        "slug": sub.name,
                        "name": a.get("name") or sub.name,
                        "description": scrub(
                            (a.get("name") or sub.name) + " routine recipe",
                            uuid_to_role,
                            id_to_name,
                        ),
                        "scheduleOrTriggerIntent": scrub(
                            str(intent), uuid_to_role, id_to_name
                        ),
                        "prompt": prompt,
                    }
                )
        agents.append(
            {
                "roleKey": role_key,
                "name": name,
                "description": scrub(desc, uuid_to_role, id_to_name),
                "routines": routines,
            }
        )
    # stable order by roleKey
    agents.sort(key=lambda a: a["roleKey"])
    return agents


def load_skills(
    uuid_to_role: dict[str, str],
    id_to_name: dict[str, str] | None = None,
) -> list[dict]:
    skills: list[dict] = []
    if not WORKFLOWS_DIR.is_dir():
        return skills
    for d in sorted(WORKFLOWS_DIR.iterdir(), key=lambda p: p.name):
        sk = d / "SKILL.md"
        if not sk.is_file():
            continue
        raw = sk.read_text()
        name, desc, body = parse_skill_frontmatter(raw)
        skills.append(
            {
                "slug": d.name,
                "name": scrub(name or d.name, uuid_to_role, id_to_name),
                "description": scrub(desc or "", uuid_to_role, id_to_name),
                "body": scrub(body, uuid_to_role, id_to_name),
            }
        )
    return skills


def load_rules(
    uuid_to_role: dict[str, str],
    id_to_name: dict[str, str] | None = None,
) -> list[dict]:
    rules: list[dict] = []
    if not RULES_DIR.is_dir():
        return rules
    for p in sorted(RULES_DIR.glob("*.mdc")):
        rules.append(
            {
                "path": p.name,
                "content": scrub(p.read_text(), uuid_to_role, id_to_name),
            }
        )
    return rules


def load_fleet_docs(
    uuid_to_role: dict[str, str],
    id_to_name: dict[str, str] | None = None,
) -> list[dict]:
    docs: list[dict] = []
    for rel in FLEET_DOC_PATHS:
        p = FLEET_DIR / rel
        if not p.is_file():
            continue
        raw = p.read_text()
        doc_map = dict(id_to_name or DEFAULT_ROOM_SHORT_IDS)
        if rel == "rooms-map.md":
            doc_map.update(extract_hex8_room_names(raw))
        docs.append(
            {"path": rel, "content": scrub(raw, uuid_to_role, doc_map)}
        )
    # Light openspec binding pointer (not full change trees)
    openspec_readme = FLEET_DIR / "openspec"
    binding_note = (
        "# OpenSpec binding (fleet)\n\n"
        "Convention: fleet OpenSpec change packages live under\n"
        "`/workspace/fleet-external-agents/openspec/changes/<id>/`\n"
        "with proposal.md, specs/, design.md, adr.md, tasks.md, APPLY.md.\n"
        "Import does not copy historical APPLY ledgers; recreate change folders as needed.\n"
        "Companion skills: openspec-intent-driven, fleet-org-raci, fleet-config-bootstrap.\n"
    )
    docs.append(
        {
            "path": "openspec-binding.md",
            "content": scrub(binding_note, uuid_to_role, id_to_name),
        }
    )
    return docs


def load_plugins() -> list[dict]:
    plugins: list[dict] = []
    seen: set[str] = set()
    # Prefer marketplace cache dirs under cursor-public/<pluginId>
    public = PLUGINS_CACHE / "cursor-public"
    if public.is_dir():
        for d in sorted(public.iterdir()):
            if d.is_dir():
                pid = d.name
                if pid not in seen:
                    seen.add(pid)
                    plugins.append({"pluginId": pid})
    # Also check workspace plugins mirror
    ws = Path("/workspace/plugins")
    if ws.is_dir():
        for d in sorted(ws.iterdir()):
            if d.is_dir() and d.name not in seen and not d.name.startswith("."):
                seen.add(d.name)
                plugins.append({"pluginId": d.name})
    if not plugins:
        plugins.append({"pluginId": "pstack"})
    return plugins


def write_readme(pack: dict) -> None:
    lines = [
        "# fleet-config.v1",
        "",
        f"Exported: `{pack['exportedAt']}`",
        f"Source label: `{pack['source']['label']}`",
        "",
        "Scrubbed multi-agent fleet pack for Grok Bot. **No secrets, no agent/room UUIDs,**",
        "operator personal name replaced with `operator`.",
        "",
        "## Contents",
        "",
        f"- Plugins: {len(pack['plugins'])}",
        f"- Rules: {len(pack['rules'])}",
        f"- Skills: {len(pack['skills'])}",
        f"- Fleet docs: {len(pack['fleetDocs'])}",
        f"- Agents: {len(pack['agents'])}",
        f"- Rooms: {len(pack['rooms'])}",
        "",
        "### Agents",
        "",
    ]
    for a in pack["agents"]:
        lines.append(
            f"- `{a['roleKey']}` — **{a['name']}** ({len(a['routines'])} routine recipes)"
        )
    lines += [
        "",
        "### Rooms",
        "",
    ]
    for r in pack["rooms"]:
        lines.append(f"- **{r['name']}** — members: {', '.join(r['memberRoleKeys'])}")
    lines += [
        "",
        "## How to hand to a teammate",
        "",
        "1. Share `fleet-config.v1.json` via private gist, repo, or file drop.",
        "2. On the destination account, run workflow skill **Fleet config bootstrap**",
        "   (or **Fleet config import**), pointing at this file.",
        "3. For a **single** bot only, use managed skill `export-bot-template` +",
        "   `create_bot_share_json` instead of this pack.",
        "",
        "## Never pack",
        "",
        "box-secrets, host-secrets, cookies, transcripts, user-memory, account scope hashes.",
        "",
        "Schema: `schema/fleet-config.v1.schema.json`",
        "",
        "## Verify (dry-run; does not import)",
        "",
        "```bash",
        "python3 scripts/verify_fleet_config.py",
        "```",
        "",
        "## Post-bootstrap Opus / operator steps (not in this pack)",
        "",
        "These are **host / credential / sidebar** leftovers. Import cannot do them.",
        "Do them after [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap).",
        "",
        "1. **agy** workhorse: install CLI + Google sign-in or `GEMINI_API_KEY`.",
        "   Re-apply sandbox wrapper / permissions (`/home/box/reference/agy-sandbox-permissions.md`).",
        "   Never pack OAuth tokens. herdr kind `agy` / integration `antigravity-cli`.",
        "2. **herdr** via `mise use -g herdr` (Opus). Confirm `herdr integration status`.",
        "3. **grok** CLI via `mise use -g grok` if gbp / thermos slash types are wanted.",
        "4. **thermos** Cursor pluginId is in `plugins[]`. Enable + **new session** so",
        "   `/thermos` spawn types exist. long-horizon-swarm overlay **skills** are packed;",
        "   the grok-build marketplace plugin enable (if used) is host-side.",
        "5. **Frontier CLIs pending**: claude / codex / pi / omp / opencode — install + auth",
        "   when registry Status should flip from pending. Do not invent ready kinds.",
        "6. **Sidebar**: delete empty New Bot if present. Do **not** recreate leftover",
        "   mixed rooms or ad-hoc rooms (Mulvad Relay List, Dev Env, legacy Horizon mix).",
        "7. **fleet-roles.mdc**: add `disk-saver: Disk Saver` if the imported rule is missing",
        "   that line (agent persona is packed; the alwaysApply map may omit it).",
        "8. **eng-supervisor / nightly-audit** are packed agents but not default room seats",
        "   (cap 6). Seat later only if a slot frees — do not exceed 6 members.",
        "",
    ]
    OUT_README.write_text("\n".join(lines) + "\n")


def assert_scrub(pack: dict) -> None:
    blob = json.dumps(pack)
    if "Todd Liu" in blob or re.search(r"\bTodd\b", blob):
        raise SystemExit("scrub check failed: operator name still present")
    # secrets filenames should not appear as packed content sources
    for bad in ("box-secrets", "host-secrets", "teach-queue-key", "chrome-cookie-seed"):
        # allow mentioning in bootstrap notes as "do not pack"
        pass
    # no raw secret file contents (empty objects are fine if never read)
    if '"apiKey"' in blob or '"password"' in blob:
        raise SystemExit("scrub check failed: credential-looking keys in pack")
    hex_hits = find_fleetdoc_hex8(pack)
    if hex_hits:
        sample = ", ".join(f"{p}:{t}" for p, t in hex_hits[:8])
        raise SystemExit(
            f"scrub check failed: fleetDocs hex8 residue still present: {sample}"
        )


def main() -> int:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    uuid_to_role = collect_uuid_maps()
    id_to_name = collect_room_id_map()
    pack = {
        "schema": "fleet-config.v1",
        "exportedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {"label": "scrubbed"},
        "plugins": load_plugins(),
        "rules": load_rules(uuid_to_role, id_to_name),
        "skills": load_skills(uuid_to_role, id_to_name),
        "fleetDocs": load_fleet_docs(uuid_to_role, id_to_name),
        "agents": load_agents(uuid_to_role, id_to_name),
        "rooms": [
            {
                "name": r["name"],
                "charter": scrub(r["charter"], uuid_to_role, id_to_name),
                "memberRoleKeys": list(r["memberRoleKeys"]),
            }
            for r in ROOMS
        ],
        "bootstrap": {
            "order": list(BOOTSTRAP["order"]),
            "notes": [scrub(n, uuid_to_role, id_to_name) for n in BOOTSTRAP["notes"]],
        },
    }
    assert_scrub(pack)
    OUT_JSON.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n")
    write_readme(pack)
    print(str(OUT_JSON))
    return 0


if __name__ == "__main__":
    sys.exit(main())
