---
name: Fleet config export
description: >-
  when user wants to serialize/share/replicate fleet config to another account
  or teammate
---
# Fleet config export

Serialize the **multi-agent fleet** (roles, rules, skills, rooms, routine recipes) into a scrubbed `fleet-config.v1` pack. Companion: [Fleet config import](sand-workflow:fleet-config-import), [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap), [Design a Grok Bot](sand-workflow:design-a-grok-bot).

Plugin root: this repo (`fleet-config`). Scripts live under `scripts/`; schema under `schema/`.

## When to use

- Operator wants to share / replicate the fleet to another account or teammate
- Building a gist/repo handoff of org shape (not a single bot template)

## Single bot vs fleet

| Ask | Path |
| --- | --- |
| **ONE** bot template | Managed skill `export-bot-template` + `create_bot_share_json` (profile, memory, skills, routines, plugins only) |
| **FLEET** org | This skill → `fleet-config.v1` pack |

Do not use this pack for a single-bot public template card.

## Steps

1. **Prefer the serialize script** (fast, consistent scrub):
   ```bash
   python3 scripts/serialize_fleet_config.py
   ```
   Exit 0 prints the path to `dist/fleet-config.v1.json`. Also writes `dist/README.md`.

   Env overrides (defaults are Grok Bot box paths): `FLEET_AGENTS_DIR`, `FLEET_WORKFLOWS_DIR`, `FLEET_RULES_DIR`, `FLEET_DIR`, `FLEET_DIST_DIR`.

2. **Or manual pack** matching schema `schema/fleet-config.v1.schema.json`:
   - `plugins`: marketplace `pluginId` only
   - `rules`: `~/.cursor/rules/*.mdc` (fleet-roles, pstack-herdr-agents, pstack-models, …)
   - `skills`: `/home/box/agent-data/workflows/*/SKILL.md` (slug, name, description, body)
   - `fleetDocs`: roles-map, rooms-map, registry, concurrency, pstack-herdr-agents, openspec binding note
   - `agents`: live personas by `roleKey` (skip empty **New Bot**); routines as **recipes** (slug, name, description, scheduleOrTriggerIntent, prompt) — never automation run ids
   - `rooms`: name, charter, memberRoleKeys (max 6) — no room UUIDs; collapse duplicate mixed rooms out of the pack
   - `bootstrap.order`: plugins → rules → skills → agents → rooms → healthchecks

3. **Scrub (public / teammate mode)**
   - Replace operator personal name → `operator`
   - Strip agent/room/run UUIDs (map to roleKeys where obvious)
   - Omit secrets files and their contents

4. **Never pack**
   - `box-secrets.json`, `host-secrets.json`, teach-queue keys
   - cookies / chrome Login Data / `chrome-cookie-seed.json`
   - transcripts, conversation DBs, user-memory shards
   - account scope hashes, machine permission maps as credentials

5. **Verify before handoff**
   ```bash
   python3 scripts/verify_fleet_config.py dist/fleet-config.v1.json
   ```
   Must print `RESULT: PASS` and exit 0.

6. **Hand off**
   - Offer the dist path: `dist/fleet-config.v1.json` (or `$FLEET_DIST_DIR/fleet-config.v1.json`)
   - Teammate options: private gist, shared repo, or file drop
   - Point importer at [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap)

## Done when

Dist JSON + README exist, verify PASS, scrub check clean (no operator legal name, no secret file contents), and the operator has a concrete handoff path.
