#!/usr/bin/env bash
# Run the suite whatever the checkout folder is called.
#
# The repository is `strategic-arena`, and the plugin's Python package is `upfront`
# (a hyphen cannot be a package name). pytest resolves test modules by walking up
# through parent directories that contain `__init__.py` — so from a checkout named
# `strategic-arena` it tries to import the repository root as a module and dies on
# `from .llm_adapter import ...` with "no known parent package".
#
# The fix is not to rename the folder: it is to run pytest through a path whose
# package segment is a valid identifier. We make a temporary directory with
# `upfront -> <checkout>` and point pytest at that.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/arena-tests.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
# A copy, not a symlink: pytest resolves the real path, and a symlink would put it
# straight back on `strategic-arena`. Hard links keep the copy cheap.
mkdir -p "$tmp/upfront"
cp -al "$root"/. "$tmp/upfront/"

cd "$tmp/upfront"
# Pick the interpreter: PYTHON, then python3. Dev deps are pytest + fastapi +
# pydantic + httpx (`pip install -e ".[test]"`); set PYTHON to point at that env.
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" -m pytest "$@"
