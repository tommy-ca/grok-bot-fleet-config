# Export pack

Export pack lets a user serialize live fleet surfaces into a scrubbed `fleet-config.v1` JSON pack (plus README) without packing secrets, agent/room UUIDs, or operator personal names.

## Sub-features

- `export-run` writes `dist/fleet-config.v1.json` and `dist/README.md` via serialize.
- `export-path` prints the output path and exits 0 on success.
- `export-env` honors `FLEET_*` env overrides for agents/workflows/rules/dist roots.

## How to get to it (user POV)

- Run `python3 scripts/serialize_fleet_config.py` from the repo root (README Export section).
- Follow the `fleet-config-export` skill steps that cite the same script.

## Driving it with fleet-config CLI

Preconditions:

- Doctor exited 0.
- `scripts/serialize_fleet_config.py` exists.
- Disposable dist preferred: `export FLEET_DIST_DIR=/tmp/fleet-verify-$RUN_ID/dist`.

- **Serialize.** Run `python3 scripts/serialize_fleet_config.py`. Exit code `0`. Stdout names the written JSON path under `$FLEET_DIST_DIR` (default `<repo>/dist/fleet-config.v1.json`).
- **Confirm files.** Run `test -f "$FLEET_DIST_DIR/fleet-config.v1.json" && test -f "$FLEET_DIST_DIR/README.md"`. Both exist.
- **Follow-up verify (optional).** Run `python3 scripts/verify_fleet_config.py "$FLEET_DIST_DIR/fleet-config.v1.json"`. Until FC-4 scrubs live rooms-map hex8, a live pack may `RESULT: FAIL`; that is expected and not an export-pack failure. Fixture-only export proofs should use a scrubbed source or skip live follow-up verify.
- **Proof.** Save the serialize command transcript to `.cursor/skills/verify-fleet-config/evidence/drive-export-pack.txt` including the output path and exit code.

## Gotchas

- Default serialize reads live box paths (`/home/box/agent-data/agents`, workflows, rules). Override with `FLEET_*` when isolating.
- Writing into the repo `dist/` mutates tracked/untracked output; prefer `/tmp/fleet-verify-$RUN_ID/dist` for verification runs.
- Export success is file write + exit 0, not verify PASS on a dirty live pack.
- Cite `scripts/serialize_fleet_config.py` — never an absolute `/workspace/fleet-external-agents/...` script path as the user entry point.
