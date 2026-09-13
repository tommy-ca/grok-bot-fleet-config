# fleet-config

Grok Bot / Grok Build plugin for **scrubbed multi-agent fleet packs** (`fleet-config.v1`).

Serialize live fleet surfaces → verify dry-run → import / bootstrap onto another account — **without** packing secrets, agent/room UUIDs, or operator personal names.

## Install

```bash
# from this repo (Grok Build / Grok plugin host)
grok plugin install tommy-ca/fleet-config --trust
```

Or clone and point skills/scripts at the checkout. After enable, start a **new session** so skills resolve.

## Quick verify

```bash
python3 scripts/verify_fleet_config.py tests/fixtures/fleet-config.v1.min.json
```

Expect `RESULT: PASS` and exit 0.

## Export (serialize)

```bash
python3 scripts/serialize_fleet_config.py
# → dist/fleet-config.v1.json (+ dist/README.md)
python3 scripts/verify_fleet_config.py dist/fleet-config.v1.json
```

## Skills

| Skill | Purpose |
| --- | --- |
| `fleet-config-export` | Serialize scrubbed pack |
| `fleet-config-import` | Apply pack (never delete bots) |
| `fleet-config-bootstrap` | Fresh account: verify → import → healthchecks |

Persona: `agents/fleet-config.md`.

## Layout

```
plugin.json
.grok-plugin/marketplace.json
agents/fleet-config.md
skills/fleet-config-{export,import,bootstrap}/SKILL.md
scripts/serialize_fleet_config.py
scripts/verify_fleet_config.py
schema/fleet-config.v1.schema.json
dist/                    # serialize output (.gitkeep in repo)
tests/fixtures/fleet-config.v1.min.json
```

## Env overrides

Scripts default to Grok Bot box paths. Override as needed:

| Variable | Default |
| --- | --- |
| `FLEET_AGENTS_DIR` | `/home/box/agent-data/agents` |
| `FLEET_WORKFLOWS_DIR` | `/home/box/agent-data/workflows` |
| `FLEET_RULES_DIR` | `~/.cursor/rules` |
| `FLEET_DIR` | `/workspace/fleet-external-agents` |
| `FLEET_DIST_DIR` | `<plugin>/dist` |
| `FLEET_SCHEMA_PATH` | `<plugin>/schema/fleet-config.v1.schema.json` |
| `FLEET_PACK_PATH` | (optional explicit pack JSON) |

## Pack contract (never pack)

- Secrets: `box-secrets`, `host-secrets`, cookies, teach-queue keys
- Identity: agent/room UUIDs (use `roleKey` + name)
- Operator personal name (scrub → `operator`)
- Transcripts / user-memory

Rooms: max **6** `memberRoleKeys`. Bootstrap order: plugins → rules → skills → agents → rooms → healthchecks.

## Single bot vs fleet

| Need | Path |
| --- | --- |
| One bot public template | Managed `export-bot-template` + `create_bot_share_json` |
| Full fleet org | This plugin → `fleet-config.v1` |

## License

MIT — see [LICENSE](LICENSE).
