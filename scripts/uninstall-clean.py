#!/usr/bin/env python3
"""Remove every trace of a Hermes plugin that `hermes plugins remove` leaves behind.

Why this exists
---------------
`hermes plugins remove <id>` deletes the plugin tree and its config/grants, then
stops. It does not touch:

  * the dependency environments (``installs/*/environments/*/venv``) that
    ``plugins install --yes-deps`` created, each holding an *editable* install of
    ``hermes-<id>``;
  * the source snapshots those builds came from (``workspace/plugin-sources/<id>-*``),
    which is why a later reinstall can silently build from stale code;
  * ``plugin-data/<id>`` — run history, kept on purpose by the plugin (correct for
    user data, wrong when you want a truly clean machine);
  * stale update locks and uv build-cache entries named after the plugin.

Usage
-----
    python3 scripts/uninstall-clean.py <plugin-id> [--keep-data] [--dry-run]

Run it **after** ``hermes plugins remove <id>``. It prints every path it touches
and ends with a proof line: the number of remaining paths matching the id under
``$HERMES_HOME``. That number must be 0.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        p = Path(env).expanduser()
        return p.parent.parent if p.parent.name == "profiles" else p
    return Path.home() / ".hermes"


def find_matches(root: Path, needle: str) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in list(dirnames) + list(filenames):
            if needle in name.lower():
                out.append(Path(dirpath) / name)
    return out


def uninstall_from_venvs(matches: list[Path], package: str, dry: bool) -> int:
    """pip-uninstall the editable package from every venv that has it."""
    venvs: set[Path] = set()
    for m in matches:
        if "site-packages" in m.parts:
            head = Path(*m.parts[: m.parts.index("site-packages")])
            while head != head.parent and head.name not in ("venv", ".venv"):
                head = head.parent
            venvs.add(head / "bin" / "python")
    done = 0
    for py in sorted(venvs):
        if not py.exists():
            continue
        if dry:
            print(f"  would uninstall {package} from {py}")
            done += 1
            continue
        # these uv-built envs often ship without pip — try it, then uv, then fall
        # back to deleting the editable files directly (done in delete_paths).
        attempts = [
            [str(py), "-m", "pip", "uninstall", "-y", package],
            ["uv", "pip", "uninstall", "--python", str(py), package],
        ]
        for cmd in attempts:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if res.returncode == 0:
                print(f"  uninstalled {package} from {py.parent.parent}")
                done += 1
                break
        else:
            print(f"  no pip/uv in {py.parent.parent} — its editable files are removed directly")
    return done


def delete_paths(matches: list[Path], keep_data: bool, data_dir: Path, dry: bool) -> int:
    """Delete deepest-first so a parent is never removed twice."""
    ordered = sorted(matches, key=lambda p: len(p.parts), reverse=True)
    deleted = 0
    for p in ordered:
        if keep_data and (p == data_dir or data_dir in p.parents):
            print(f"  keeping user data: {p}")
            continue
        if not p.exists() and not p.is_symlink():
            continue
        if dry:
            print(f"  would delete {p}")
            deleted += 1
            continue
        try:
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            else:
                p.unlink()
            deleted += 1
            # tidy up any cache directory we just emptied
            parent = p.parent
            while parent != parent.parent and (root := parent).name and root.is_dir():
                try:
                    if any(root.iterdir()):
                        break
                    if "cache" not in root.parts:
                        break
                    root.rmdir()
                    parent = root.parent
                except OSError:
                    break
        except OSError as exc:
            print(f"  could not delete {p}: {exc}", file=sys.stderr)
    return deleted


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plugin_id", help="plugin id, e.g. upfront (the folder name)")
    ap.add_argument("--keep-data", action="store_true",
                    help="keep plugin-data/<id> (run history)")
    ap.add_argument("--dry-run", action="store_true", help="print, change nothing")
    args = ap.parse_args()

    needle = args.plugin_id.strip().lower()
    root = hermes_home()
    data_dir = root / "plugin-data" / args.plugin_id
    pkg = f"hermes-{args.plugin_id}"

    print(f"Hermes home: {root}")
    print(f"Purging: {needle}{' (keeping run history)' if args.keep_data else ''}")
    if args.dry_run:
        print("DRY RUN — nothing will change\n")

    matches = find_matches(root, needle)
    print(f"  {len(matches)} path(s) named '{needle}' under {root}")

    n_venv = uninstall_from_venvs(matches, pkg, args.dry_run)
    # re-scan: pip uninstall removes some of what we listed
    matches = find_matches(root, needle) if not args.dry_run else matches
    n_del = delete_paths(matches, args.keep_data, data_dir, args.dry_run)

    print(f"\n  venvs cleaned: {n_venv}   paths deleted: {n_del}")
    if args.dry_run:
        return 0

    left = find_matches(root, needle)
    print(f"\nProof: find {root} -iname '*{needle}*' -> {len(left)} path(s)")
    for p in left:
        print(f"  {p}")
    if left and not args.keep_data:
        print("\nFAILED: something survived. Do not ship on this result.", file=sys.stderr)
        return 1
    print("\nOK: the machine has no trace of the plugin." if not left
          else "\nOK: only the run history remains (--keep-data).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
