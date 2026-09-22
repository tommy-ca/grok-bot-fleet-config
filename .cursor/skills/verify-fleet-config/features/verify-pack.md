# Verify pack

Verify pack lets a user dry-run-check a `fleet-config.v1` JSON pack for structure, scrub rules, and bootstrap order without importing onto the live account.

## Sub-features

- `verify-min-pass` PASSes the scrubbed min fixture.
- `verify-missing-path` fails closed when the pack path is absent.
- `verify-counts` prints agent/skill/rule/room/plugin counts on PASS.

## How to get to it (user POV)

- Run `python3 scripts/verify_fleet_config.py tests/fixtures/fleet-config.v1.min.json`.
- Run `python3 scripts/verify_fleet_config.py` to use the default dist pack path.
- Run `python3 scripts/verify_fleet_config.py /path/to/fleet-config.v1.json` for an arbitrary pack.

## Driving it with fleet-config CLI

Preconditions:

- Doctor exited 0.
- `tests/fixtures/fleet-config.v1.min.json` exists.
- Working directory is the repo root.

- **Min fixture PASS.** Run `python3 scripts/verify_fleet_config.py tests/fixtures/fleet-config.v1.min.json`. Exit code `0`. Stdout contains `RESULT: PASS` and a `COUNTS:` line.
- **Missing path FAIL.** Run `python3 scripts/verify_fleet_config.py /tmp/fleet-verify-missing-pack.json`. Exit code non-zero. Stdout contains `RESULT: FAIL` (or a pack-missing failure) without a Python traceback storm.
- **Proof.** Save the min-fixture transcript to `.cursor/skills/verify-fleet-config/evidence/drive-verify-pack.txt` with command, full stdout, and exit code.

## Gotchas

- Verify never mutates the account; WARN lines about live agents/skills not packed are informational on a fixture run.
- Default path without args points at `dist/fleet-config.v1.json`, which may be absent on a clean checkout — prefer the min fixture for Doctor follow-up.
- Dirty hex8 FAIL fixtures arrive with FC-1; until then, do not claim dirty-fail coverage from this feature alone.
