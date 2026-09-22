# Seed skills

Seed skills lets a user extract the three fleet-config workflow skills (`fleet-config-export`, `fleet-config-import`, `fleet-config-bootstrap`) from a pack into a target workflows directory for cold-start.

## Sub-features

- `seed-dry-run` lists the three slugs without writing.
- `seed-write` writes three `SKILL.md` trees under the out dir.
- `seed-idempotent` second write is no-op or overwrite-stable.

## How to get to it (user POV)

- Intended command (FC-1): `python3 scripts/seed_fleet_config_skills.py --pack tests/fixtures/fleet-config.v1.min.json --out /tmp/seed-test --dry-run`
- Write form: `python3 scripts/seed_fleet_config_skills.py --pack <pack.json> --out <workflows-dir>`

## Driving it with fleet-config CLI

Preconditions:

- Doctor exited 0.
- **Depends on FC-1:** `scripts/seed_fleet_config_skills.py` must exist. If Doctor WARNs that the seed script is missing, skip this Drive and report unmet precondition — still keep this map entry shipped.

- **Dry-run.** Run `python3 scripts/seed_fleet_config_skills.py --pack tests/fixtures/fleet-config.v1.min.json --out /tmp/fleet-verify-$RUN_ID --dry-run`. Exit code `0`. Stdout lists three slugs: `fleet-config-export`, `fleet-config-import`, `fleet-config-bootstrap`.
- **Write.** Run the same command without `--dry-run`. Three `SKILL.md` files exist under the out dir.
- **Re-run.** Run write again. Second run is no-op or overwrite-stable (still three skills, exit 0).
- **Proof.** Save transcript to `.cursor/skills/verify-fleet-config/evidence/drive-seed-skills.txt`. On FC-1-missing skip, save a short `evidence/drive-seed-skills-SKIP.txt` naming the unmet path.

## Gotchas

- Until FC-1 merges, the script is absent on `main`; do not invent a local seed implementation inside this skill tree.
- Default out dir in production docs may be `/home/box/agent-data/workflows` — verification runs must use a disposable `/tmp/fleet-verify-$RUN_ID` out dir.
- Seeding must not delete unrelated skills in the out dir.
