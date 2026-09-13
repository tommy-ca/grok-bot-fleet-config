# fleet-config — agent notes

Plugin for scrubbed `fleet-config.v1` export / verify / import / bootstrap. Not an application server.

## Check

```bash
python3 scripts/verify_fleet_config.py tests/fixtures/fleet-config.v1.min.json
```

CI runs the same command via `.github/workflows/verify.yml`.

## Spawn / persona

- Agent file: `agents/fleet-config.md` (plugin id `fleet-config`)
- Skills under `skills/` — cite as `fleet-config-export`, `fleet-config-import`, `fleet-config-bootstrap`

## Scripts

Prefer `scripts/serialize_fleet_config.py` and `scripts/verify_fleet_config.py` with env overrides (`FLEET_*`) over hand-rolled JSON.

## Do not

- Commit live `dist/fleet-config.v1.json` with real fleet data into public forks without scrub PASS
- Pack secrets, UUIDs, or operator legal names
- Delete bots during import
