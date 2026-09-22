---
name: verify-fleet-config
description: "CLI verification skill for grok-bot-fleet-config: doctor the serialize/verify/seed scripts, drive export/verify/seed/bootstrap-order features, and leave transcripts. Use when proving fleet-config.v1 scrub/verify/seed behavior without a browser."
---

# Verify fleet-config

Project-local verification for the **fleet-config CLI surface** (`scripts/serialize_fleet_config.py`, `scripts/verify_fleet_config.py`, and `scripts/seed_fleet_config_skills.py` when present). No browser, Playwright, or CDP. Cold agents run Launch → Doctor → Drive one mapped feature → Evidence → Cleanup.

Keep the feature map honest with `/maintain-verification-skill` as scripts and fixtures change.

## Launch

There is no long-lived server. Launch means: work from the plugin repo root and confirm Python can invoke the scripts.

```bash
cd <repo-root>   # directory that contains scripts/ and tests/fixtures/
python3 --version
```

Ready when `python3` prints a version and `scripts/verify_fleet_config.py` exists. Teardown is a no-op (no process to kill). Optional env overrides (`FLEET_PACK_ROOT`, `FLEET_SCHEMA_PATH`, `FLEET_PACK_PATH`, …) are documented in the repo README; prefer unset defaults for fixture drives.

## Doctor

Read-only. Run before every Drive when anything looks off:

```bash
bash .cursor/skills/verify-fleet-config/helpers/doctor.sh
```

Pass when exit 0 and stdout lists OK for `python3`, `scripts/verify_fleet_config.py`, `scripts/serialize_fleet_config.py`, `schema/fleet-config.v1.schema.json`, and `tests/fixtures/fleet-config.v1.min.json`. A WARN that `seed_fleet_config_skills.py` is missing is expected until FC-1 lands; do not treat that WARN as Doctor failure. Fail (exit 1) means do not Drive.

## Drive

Pick one feature file under `.cursor/skills/verify-fleet-config/features/` and follow its **Driving it with fleet-config CLI** section literally. Default first proof: [verify-pack](features/verify-pack.md) against `tests/fixtures/fleet-config.v1.min.json`.

```bash
python3 scripts/verify_fleet_config.py tests/fixtures/fleet-config.v1.min.json
```

Observable pass: stdout contains `RESULT: PASS` and exit code 0. For other features see the map index.

## Evidence

Save CLI proof under `.cursor/skills/verify-fleet-config/evidence/` (inside the skill tree; do not write outside `.cursor/skills/verify-fleet-config/` on this PR).

For each Drive:

1. Capture the exact command, stdout, stderr, and exit code into a transcript (example: `evidence/drive-verify-pack.txt`).
2. Record feature id and fixture path in the transcript header.
3. Keep evidence after Cleanup. Cleanup must never delete `evidence/`.

Proof standards: drive the real script path the user would run; assert `RESULT:` lines and exit codes; do not mock pack JSON parsers; do not treat a dry-run seed as written skills until files exist on disk.

## Cleanup

- Remove only scratch dirs this run created (for example `/tmp/fleet-verify-$RUN_ID` used by seed-skills).
- Never kill by process name (no server was started).
- Never delete `.cursor/skills/verify-fleet-config/evidence/**`.
- Leave Doctor and Drive transcripts in place for review.

## Helpers

| Helper | Invocation |
| --- | --- |
| Doctor | `bash .cursor/skills/verify-fleet-config/helpers/doctor.sh` |

All helpers are executable shell. Invocation is shown above and in Doctor.

## Feature map

Index and recipes: [features/README.md](features/README.md).

- [export-pack](features/export-pack.md)
- [verify-pack](features/verify-pack.md)
- [seed-skills](features/seed-skills.md)
- [bootstrap-order](features/bootstrap-order.md)
