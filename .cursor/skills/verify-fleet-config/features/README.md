# Fleet-config verification map

This directory is the maintained source for verifying the user-facing CLI behavior of `grok-bot-fleet-config`. Read the index before driving, then use the matching feature file as the recipe. Surface is scripts only — no browser.

## Baseline preconditions

- Working directory is the plugin repo root (contains `scripts/`, `tests/fixtures/`, `schema/`).
- `python3` is on `PATH`.
- Run `bash .cursor/skills/verify-fleet-config/helpers/doctor.sh` and require exit 0.
- Prefer disposable output dirs under `/tmp/fleet-verify-$RUN_ID` for serialize and seed writes.
- Never drive against a live account import; verify is dry-run only.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Treat every command as literal. Keep quoted paths and flags unchanged.
- Drive through `python3 scripts/*.py` from the repo root.
- Restore or discard disposable dirs after a mutation. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the command, stdout, stderr, and exit code.
- Mutation proof (seed write, serialize output) includes a second read of the written files.
- Record the feature ID and entry point used with every artifact under `.cursor/skills/verify-fleet-config/evidence/`.
- Report an unreachable path with the attempted command and the unmet precondition (for example seed script missing until FC-1).
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with fleet-config CLI` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

## Features

- [Export pack](./export-pack.md) covers serialize to `dist/fleet-config.v1.json` via `scripts/serialize_fleet_config.py`.
- [Verify pack](./verify-pack.md) covers dry-run verify PASS/FAIL on fixtures and packs.
- [Seed skills](./seed-skills.md) covers pack-extract seed of three fleet-config skills (depends on FC-1 script).
- [Bootstrap order](./bootstrap-order.md) covers the required plugins → rules → skills → agents → rooms → healthchecks order.
