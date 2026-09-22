#!/usr/bin/env bash
# Read-only health check for verify-fleet-config. Exit 0 when the CLI surface is worth driving.
set -euo pipefail

ROOT="${FLEET_PACK_ROOT:-}"
if [[ -z "$ROOT" ]]; then
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # helpers/ -> verify-fleet-config/ -> skills/ -> .cursor/ -> repo root
  ROOT="$(cd "$HERE/../../../.." && pwd)"
fi

fail=0
warn=0

ok() { printf 'OK   %s\n' "$1"; }
bad() { printf 'FAIL %s\n' "$1"; fail=1; }
note() { printf 'WARN %s\n' "$1"; warn=1; }

printf 'doctor: repo=%s\n' "$ROOT"

command -v python3 >/dev/null 2>&1 && ok "python3=$(command -v python3)" || bad "python3 missing"

need=(
  "scripts/verify_fleet_config.py"
  "scripts/serialize_fleet_config.py"
  "schema/fleet-config.v1.schema.json"
  "tests/fixtures/fleet-config.v1.min.json"
)
for rel in "${need[@]}"; do
  if [[ -e "$ROOT/$rel" ]]; then
    ok "$rel"
  else
    bad "missing $rel"
  fi
done

if [[ -x "$ROOT/scripts/verify_fleet_config.py" ]]; then
  ok "verify_fleet_config.py executable"
else
  # still runnable via python3 even if not +x
  if [[ -f "$ROOT/scripts/verify_fleet_config.py" ]]; then
    note "verify_fleet_config.py not executable (python3 path still OK)"
  fi
fi

if [[ -f "$ROOT/scripts/seed_fleet_config_skills.py" ]]; then
  ok "seed_fleet_config_skills.py present"
else
  note "seed_fleet_config_skills.py missing (FC-1); seed-skills Drive blocked until FC-1 lands"
fi

map="$ROOT/.cursor/skills/verify-fleet-config/features/README.md"
if [[ -f "$map" ]]; then
  ok "feature map README present"
else
  bad "feature map README missing"
fi

printf 'doctor: fail=%s warn=%s\n' "$fail" "$warn"
if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
exit 0
