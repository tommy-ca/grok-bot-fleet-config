#!/usr/bin/env python3
"""Unit checks for fleetDocs hex8 scrub gate (pytest-free)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from lib_scrub import (  # noqa: E402
    find_fleetdoc_hex8,
    normalize_hex8_allowlist,
    HEX8_RE,
)

FIXTURES = ROOT / "tests" / "fixtures"
VERIFY = ROOT / "scripts" / "verify_fleet_config.py"


def _run_verify(pack: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(VERIFY), str(pack)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_helper_miss_and_hit() -> None:
    dirty = json.loads((FIXTURES / "fleet-config.v1.dirty-hex8.json").read_text())
    hits = find_fleetdoc_hex8(dirty)
    assert hits, "expected hex8 hits on dirty fixture"
    paths = {p for p, _ in hits}
    assert "rooms-map.md" in paths
    tokens = {t.lower() for _, t in hits}
    assert "fea03f4a" in tokens

    allow = normalize_hex8_allowlist(["fea03f4a", "75b15bb0"])
    assert allow == {"fea03f4a", "75b15bb0"}
    allowed_hits = find_fleetdoc_hex8(dirty, allow)
    assert allowed_hits == []

    # partial allowlist still fails remaining token
    partial = find_fleetdoc_hex8(dirty, {"fea03f4a"})
    assert any(t.lower() == "75b15bb0" for _, t in partial)


def test_verify_dirty_fails_with_rooms_map() -> None:
    code, out = _run_verify(FIXTURES / "fleet-config.v1.dirty-hex8.json")
    assert code != 0, out
    assert "RESULT: FAIL" in out, out
    assert "rooms-map" in out, out
    assert "fea03f4a" in out, out


def test_verify_min_passes() -> None:
    code, out = _run_verify(FIXTURES / "fleet-config.v1.min.json")
    assert code == 0, out
    assert "RESULT: PASS" in out, out
    assert "schema-check:" in out, out


def test_verify_allowlisted_passes() -> None:
    code, out = _run_verify(FIXTURES / "fleet-config.v1.hex8-allowlisted.json")
    assert code == 0, out
    assert "RESULT: PASS" in out, out


def test_hex8_re_word_boundary() -> None:
    assert HEX8_RE.search("fea03f4a")
    assert not HEX8_RE.search("xxfea03f4ayy")  # no boundary
    assert HEX8_RE.search("id fea03f4a name")


def main() -> int:
    tests = [
        test_helper_miss_and_hit,
        test_verify_dirty_fails_with_rooms_map,
        test_verify_min_passes,
        test_verify_allowlisted_passes,
        test_hex8_re_word_boundary,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {fn.__name__}: {e}")
    print(f"RESULT: {'FAIL' if failed else 'PASS'} ({failed} failed / {len(tests)})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
