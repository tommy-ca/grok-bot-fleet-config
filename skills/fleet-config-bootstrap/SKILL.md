---
name: Fleet config bootstrap
description: >-
  when standing up a fresh Grok Bot account from a fleet pack or after template
  import; orchestrates import + healthchecks
---
# Fleet config bootstrap

Stand up a **fresh** Grok Bot account (or heal a thin install) from a `fleet-config.v1` pack. Orchestrates import + healthchecks. Companion: [Fleet config import](sand-workflow:fleet-config-import), [Fleet config export](sand-workflow:fleet-config-export), [Design a Grok Bot](sand-workflow:design-a-grok-bot), setup-pstack (pstack plugin).

## When to use

- New account after receiving a fleet pack (gist/repo/file)
- After importing a designer **template** and the operator wants the full fleet next
- Re-hydrate rules/skills/rooms on a box that lost fleet docs under `$FLEET_DIR`

## Steps

1. Locate pack (`fleet-config.v1.json`): default `dist/fleet-config.v1.json` or operator-provided path. If the three fleet-config skills are missing, follow README cold-start (pack-extract seed default; repo-copy alternate).
2. **Dry-run verify** (must PASS before mutate):
   ```bash
   python3 scripts/verify_fleet_config.py /path/to/fleet-config.v1.json
   ```
3. Run **[Fleet config import](sand-workflow:fleet-config-import)** end-to-end (validate → plugins → rules → skills → fleet docs → agents → rooms → journal). Import is match-by-name idempotent for agents, rooms, and routines; it never deletes.
4. **setup-pstack**: if `~/.cursor/rules/pstack-models.mdc` is missing, run pstack `/setup-pstack` (do not ask). Skip if present.
5. **Designer fresh install**: on the bot-designer agent, follow [Design a Grok Bot](sand-workflow:design-a-grok-bot) fresh-install; ensure `transcript-healthcheck` and `routine-healthcheck` routines exist.
6. Optional: offer Routine healthcheck across all bots once.
7. Confirm rooms Eng lead / QStack / Ferro / Fleet meta (or pack equivalents) exist; note any operator sidebar cleanup for duplicates.

## Order (must match pack bootstrap.order)

plugins → rules → skills → agents → rooms → healthchecks

## Single-bot note

If the operator only imported a **single** bot template via `create_bot_share_json`, do designer fresh-install first; run this bootstrap only when they want the multi-agent fleet pack applied.

## Sandbox note

Fleet pack does **not** copy `~/bin/agy` wrappers or host PATH. After import on a Grok Bot sandbox, Opus (or operator) must reinstall sandbox permissions per `/home/box/reference/agy-sandbox-permissions.md` when that reference exists on the box. Do not document brief-only skip-permissions as the default. Do not pack OAuth tokens or credentials.

## Done when

Import journal complete, pstack models rule present (when applicable), designer healthcheck routines present, operator told what to do next (credentials for external CLIs, sidebar delete of New Bot if any).
