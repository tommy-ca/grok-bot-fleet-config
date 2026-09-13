# fleet-config — workflow map

Pointer/index for export → verify → import → bootstrap. **Not** a second source of truth; skill bodies under `skills/` own the steps.

---
tracker:
  board: fleet pack handoff + bootstrap journal
polling:
  tick: on-demand (operator / Fleet Config bot)
workspace:
  isolation: Grok Bot box + destination account
agent:
  max_concurrent: 1
  backpressure: verify must PASS before import mutate
hooks: optional CI verify.yml on PR/push
observability:
  - verify RESULT: PASS/FAIL
  - import journal under $FLEET_DIR
---

## Cite (SoT)

| Skill | Id |
| --- | --- |
| Fleet config export | [Fleet config export](sand-workflow:fleet-config-export) |
| Fleet config import | [Fleet config import](sand-workflow:fleet-config-import) |
| Fleet config bootstrap | [Fleet config bootstrap](sand-workflow:fleet-config-bootstrap) |
| Design a Grok Bot | [Design a Grok Bot](sand-workflow:design-a-grok-bot) |

## Loop

```
serialize  →  verify (dry-run)  →  handoff  →  verify on dest  →  import  →  healthchecks
```

1. **Export** — `python3 scripts/serialize_fleet_config.py` → `dist/fleet-config.v1.json`
2. **Verify** — `python3 scripts/verify_fleet_config.py <pack>` must exit 0
3. **Bootstrap / import** — follow bootstrap skill order: plugins → rules → skills → agents → rooms → healthchecks
4. **Journal** — create-vs-skip + operator leftovers (host CLIs, New Bot sidebar)

## Eligibility

- Pack declares `"schema": "fleet-config.v1"`
- Scrub clean (no operator legal name, no raw UUIDs as identity, no credential keys)
- Rooms ≤ 6 members; no New Bot packed

## Handoff states

| State | Meaning |
| --- | --- |
| `PASS` | verify dry-run clean; safe to share / import |
| `FAIL` | refuse import; fix pack or scrub |
| `IMPORTED` | journal written; designer healthchecks noted |
| `human_review` | host CLIs / credentials / sidebar cleanup left to operator |
