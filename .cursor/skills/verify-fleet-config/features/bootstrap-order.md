# Bootstrap order

Bootstrap order is the fixed sequence a fresh account must apply a pack: plugins, then rules, then skills, then agents, then rooms, then healthchecks. Verify and bootstrap skills treat any other order as invalid.

## Sub-features

- `order-contract` pack `bootstrap.order` equals the six-step list.
- `order-verify` verify script FAILs when order drifts.
- `order-docs` bootstrap skill and README cite the same sequence.

## How to get to it (user POV)

- Read pack field `bootstrap.order` after export or in fixtures.
- Follow `fleet-config-bootstrap` skill section **Order (must match pack bootstrap.order)**.
- Run verify on a pack; INFO line echoes `plugins → rules → skills → agents → rooms → healthchecks`.

## Driving it with fleet-config CLI

Preconditions:

- Doctor exited 0.
- Min fixture present.

- **Read fixture order.** Run `python3 -c "import json; print(json.load(open('tests/fixtures/fleet-config.v1.min.json'))['bootstrap']['order'])"`. Output is exactly `['plugins', 'rules', 'skills', 'agents', 'rooms', 'healthchecks']`.
- **Verify echoes order.** Run `python3 scripts/verify_fleet_config.py tests/fixtures/fleet-config.v1.min.json`. Stdout contains `bootstrap.order: plugins → rules → skills → agents → rooms → healthchecks` and `RESULT: PASS`.
- **Proof.** Save transcript to `.cursor/skills/verify-fleet-config/evidence/drive-bootstrap-order.txt`.

## Gotchas

- Order must be exact: plugins → rules → skills → agents → rooms → healthchecks. No swaps, no omissions.
- Import skill expands plugins→…→journal internally; the pack contract and verify gate use the six tokens above.
- Do not invent alternate orders in evidence or docs.
