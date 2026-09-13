---
name: Fleet config import
description: >-
  when bootstrapping or importing a fleet-config.v1 pack onto this account
---
# Fleet config import

Apply a scrubbed `fleet-config.v1` pack onto **this** Grok Bot account. Does not delete existing bots. Companion: [Fleet config export](sand-workflow:fleet-config-export), [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap), [Design a Grok Bot](sand-workflow:design-a-grok-bot).

## Inputs

- Path to `fleet-config.v1.json` (default: `dist/fleet-config.v1.json` in this plugin, or `$FLEET_DIST_DIR/fleet-config.v1.json`)
- Schema: `schema/fleet-config.v1.schema.json`
- Dry-run verifier (does **not** import):
  ```bash
  python3 scripts/verify_fleet_config.py /path/to/fleet-config.v1.json
  ```

## Steps

1. **Validate schema**
   - Run `scripts/verify_fleet_config.py` first; refuse on FAIL.
   - Confirm `"schema": "fleet-config.v1"` and required top-level keys.
   - Refuse packs that embed secrets, cookie jars, or raw agent UUIDs as identity.

2. **Plugins** (`bootstrap.order` first)
   - For each `plugins[].pluginId`: SearchPlugins → InstallPlugin if missing.
   - Marketplace ids only; no custom MCP secrets from the pack.

3. **Rules**
   - Write each `rules[]` to `~/.cursor/rules/<path>` (create dir if needed).
   - Typical: `fleet-roles.mdc`, `pstack-herdr-agents.mdc`, `pstack-models.mdc`.

4. **Skills**
   - For each `skills[]`: write via `update_state` skill write (or filesystem under `/home/box/agent-data/workflows/<slug>/SKILL.md` when that is the live convention on this host).
   - Preserve slug; do not clobber unrelated local-only skills without asking.

5. **Fleet docs**
   - Write `fleetDocs[]` under `$FLEET_DIR` (default `/workspace/fleet-external-agents/`) and openspec binding note.
   - Refresh rooms-map / roles-map twins after agents/rooms exist.

6. **Agents**
   - Inventory live agents under `$FLEET_AGENTS_DIR` (default `/home/box/agent-data/agents/*/profile.json`).
   - **Skip New Bot** (empty).
   - **Do NOT delete** existing bots.
   - For each pack `agents[]` entry: if no bot with matching **name**, `CreateAgent` with name + description from pack (`roleKey` is the stable key for rooms/RACI).
   - Match existing by name when present; leave their UUIDs local.
   - For each new (or explicitly requested) bot: `SendToAgent` with instructions to create routine **recipes** from pack (`update_state` routine create: name, scheduleOrTriggerIntent, prompt). Do not invent automation.json ids.

7. **Rooms**
   - For each `rooms[]`: `CreateChannel` by name/charter; members from `memberRoleKeys` resolved to live agent ids (max **6** members; include self if managing the channel).
   - Do not recreate collapsed duplicate rooms from old fleets.
   - Do not delete channels via tools if the platform forbids it — journal for operator sidebar cleanup.

8. **Healthchecks**
   - On the designer bot (`bot-designer` / local equivalent), run [Design a Grok Bot](sand-workflow:design-a-grok-bot) **fresh-install** healthchecks (transcript-healthcheck + routine-healthcheck routines).
   - Run setup-pstack if `~/.cursor/rules/pstack-models.mdc` missing (via bootstrap skill).

9. **Journal**
   - Append a short note under `$FLEET_DIR` (or herd-journal style) listing: plugins installed, rules written, skills written, agents created (names/roleKeys), rooms created, routines requested, healthcheck status.
   - Tell the operator what was created vs skipped.

## Anti-jobs

- Never pack or re-emit secrets during import
- Never delete bots or wipe memories to “match” the pack
- Never CreateChannel with >6 members
- Never treat room/agent UUIDs from a foreign pack as valid on this account

## Done when

Pack applied per bootstrap order, journal written, designer healthchecks verified or explicitly noted missing.
