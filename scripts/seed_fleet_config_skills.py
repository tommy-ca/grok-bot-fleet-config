#!/usr/bin/env python3
"""Extract fleet-config-{export,import,bootstrap} skills from a pack into a workflows dir.

Usage:
  python3 scripts/seed_fleet_config_skills.py --pack path/to/fleet-config.v1.json
  python3 scripts/seed_fleet_config_skills.py --pack ... --out /tmp/workflows --dry-run
  python3 scripts/seed_fleet_config_skills.py --pack ... --force

Idempotent: skips existing SKILL.md unless --force.
Env: FLEET_WORKFLOWS_DIR overrides default out dir.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_scrub import SEED_SKILL_SLUGS  # noqa: E402

DEFAULT_OUT = Path(
    os.environ.get("FLEET_WORKFLOWS_DIR", "/home/box/agent-data/workflows")
)


def load_pack(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"pack missing: {path}")
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        raise SystemExit(f"pack is not valid JSON: {path} ({e})") from e
    if not isinstance(data, dict):
        raise SystemExit(f"pack root must be object: {path}")
    return data


def skills_by_slug(pack: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for item in pack.get("skills") or []:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if isinstance(slug, str) and slug:
            out[slug] = item
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--pack",
        required=True,
        type=Path,
        help="Path to fleet-config.v1.json",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Workflows dir (default: {DEFAULT_OUT})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="List actions only; do not write",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing SKILL.md",
    )
    args = p.parse_args(argv)

    pack = load_pack(args.pack.resolve())
    by_slug = skills_by_slug(pack)
    out_root: Path = args.out

    missing = [s for s in SEED_SKILL_SLUGS if s not in by_slug]
    if missing:
        print(f"ERROR: pack missing required seed slugs: {missing}", file=sys.stderr)
        return 1

    print(f"seed pack: {args.pack.resolve()}")
    print(f"seed out:  {out_root}  dry_run={args.dry_run} force={args.force}")

    wrote = 0
    skipped = 0
    for slug in SEED_SKILL_SLUGS:
        skill = by_slug[slug]
        body = skill.get("body")
        if not isinstance(body, str) or not body.strip():
            print(f"ERROR: skill {slug!r} missing body", file=sys.stderr)
            return 1
        dest_dir = out_root / slug
        dest = dest_dir / "SKILL.md"
        exists = dest.is_file()
        if exists and not args.force:
            print(f"SKIP  {slug} (exists: {dest})")
            skipped += 1
            continue
        action = "OVERWRITE" if exists else "WRITE"
        print(f"{action} {slug} -> {dest}")
        if not args.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest.write_text(body if body.endswith("\n") else body + "\n")
        wrote += 1

    print(f"DONE seed: wrote={wrote} skipped={skipped} slugs={list(SEED_SKILL_SLUGS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
