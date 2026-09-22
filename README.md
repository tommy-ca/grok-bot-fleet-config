# grok-bot-fleet-config

Grok Bot / Grok Build plugin for **scrubbed multi-agent fleet packs** (`fleet-config.v1`).

Serialize live fleet surfaces → verify dry-run → import / bootstrap onto another account, **without** packing secrets, agent/room UUIDs, or operator personal names.


## Marketplace install

### Cursor / Grok Bot (InstallPlugin)

1. Repo must be **public**.
2. Local test (optional): copy checkout to `~/.cursor/plugins/local/grok-bot-fleet-config`.
3. Submit at https://cursor.com/marketplace/publish. After review you get a numeric plugin id for `InstallPlugin` / SearchPlugins. **No Cursor InstallPlugin id yet**; until listed, use the pack + cold-start path below.
4. Manifest: `.cursor-plugin/plugin.json` (skills + agents).

Until listed, use the fleet-config.v1 pack + [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap) path.

### Grok Build CLI

```bash
grok plugin install tommy-ca/grok-bot-fleet-config --trust
grok plugin enable grok-bot-fleet-config
# new grok session after enable
```

Or via catalog after sibling listing in `tommy-ca/grok-build-plugins`.


## Cold-start (teammate handoff)

For a fresh Grok Bot account that does not yet have the three fleet-config skills.

**Default (pack-extract).** Recipients with only the gist JSON:

1. Obtain `fleet-config.v1.json` from the secret gist (invite or file-drop; do not rely on a public gist link alone):
   `https://gist.github.com/tommy-ca/ee862a22f4baa2ccf5e1fd8b6e182232`
2. Have this repo checked out (or at least `scripts/seed_fleet_config_skills.py` + `scripts/lib_scrub.py`).
3. Seed the three skills into your workflows dir:

```bash
python3 scripts/seed_fleet_config_skills.py --pack path/to/fleet-config.v1.json
```

Default out dir is `/home/box/agent-data/workflows` (override with `--out` or `FLEET_WORKFLOWS_DIR`). Idempotent: skips existing `SKILL.md` unless `--force`.

**Alternate (repo-copy).** When you already cloned this repo:

```bash
cp -R skills/fleet-config-export skills/fleet-config-import skills/fleet-config-bootstrap \
  /home/box/agent-data/workflows/
```

Then verify the pack and follow [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap):

```bash
python3 scripts/verify_fleet_config.py path/to/fleet-config.v1.json
```

## Install

```bash
# from this repo (Grok Build / Grok plugin host)
grok plugin install tommy-ca/grok-bot-fleet-config --trust
```

Or clone and point skills/scripts at the checkout. After enable, start a **new session** so skills resolve. Prefer [Cold-start](#cold-start-teammate-handoff) when you only have a pack JSON.

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
scripts/seed_fleet_config_skills.py
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

MIT. See [LICENSE](LICENSE).
