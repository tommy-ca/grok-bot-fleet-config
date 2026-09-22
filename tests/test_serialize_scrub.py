#!/usr/bin/env python3
"""Unit checks for serialize-time hex8 scrub (pytest-free)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from lib_scrub import (  # noqa: E402
    HEX8_RE,
    extract_hex8_room_names,
    scrub_hex8,
)

FIXTURE_ROOMS = ROOT / "tests" / "fixtures" / "serialize-hex8-input" / "rooms-map.md"
SERIALIZE = ROOT / "scripts" / "serialize_fleet_config.py"


def test_scrub_helper_maps_known_and_strips_unknown() -> None:
    raw = FIXTURE_ROOMS.read_text()
    assert "fea03f4a" in raw
    mapping = extract_hex8_room_names(raw)
    assert mapping.get("fea03f4a") == "QStack"
    assert mapping.get("75b15bb0") == "Ferro"
    assert mapping.get("cb3014b1") == "Ferro"

    out = scrub_hex8(raw, mapping)
    assert "fea03f4a" not in out.lower()
    assert HEX8_RE.findall(out) == []
    assert "room:QStack" in out
    assert "room:Ferro" in out
    assert "[room-id]" in out  # aaaaaaaa


def test_scrub_helper_default_map_alone() -> None:
    out = scrub_hex8("keep fea03f4a and deadbeef", None)
    assert "fea03f4a" not in out
    assert "room:QStack" in out
    assert "deadbeef" not in out
    assert "[room-id]" in out


def test_serialize_fixture_zero_hex8() -> None:
    """Serialize against a tiny FLEET_DIR fixture; pack fleetDocs have zero hex8."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        fleet = td_path / "fleet"
        fleet.mkdir()
        (fleet / "rooms-map.md").write_text(FIXTURE_ROOMS.read_text())
        dist = td_path / "dist"
        env = os.environ.copy()
        env["FLEET_DIR"] = str(fleet)
        env["FLEET_DIST_DIR"] = str(dist)
        # Empty / missing agent surfaces → empty agents/skills/rules is OK
        env["FLEET_AGENTS_DIR"] = str(td_path / "no-agents")
        env["FLEET_WORKFLOWS_DIR"] = str(td_path / "no-workflows")
        env["FLEET_RULES_DIR"] = str(td_path / "no-rules")
        env["FLEET_PLUGINS_CACHE"] = str(td_path / "no-plugins")
        proc = subprocess.run(
            [sys.executable, str(SERIALIZE)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(ROOT),
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        out_json = dist / "fleet-config.v1.json"
        assert out_json.is_file(), proc.stdout
        pack = json.loads(out_json.read_text())
        rooms_docs = [
            d for d in pack.get("fleetDocs") or [] if d.get("path") == "rooms-map.md"
        ]
        assert rooms_docs, pack.get("fleetDocs")
        content = rooms_docs[0]["content"]
        hits = HEX8_RE.findall(content)
        assert hits == [], hits
        assert "fea03f4a" not in content
        assert "room:QStack" in content


def test_idempotent_fleetdocs_scrub() -> None:
    raw = FIXTURE_ROOMS.read_text()
    mapping = extract_hex8_room_names(raw)
    once = scrub_hex8(raw, mapping)
    twice = scrub_hex8(once, mapping)
    assert once == twice
    assert HEX8_RE.findall(twice) == []


def main() -> int:
    tests = [
        test_scrub_helper_maps_known_and_strips_unknown,
        test_scrub_helper_default_map_alone,
        test_serialize_fixture_zero_hex8,
        test_idempotent_fleetdocs_scrub,
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
