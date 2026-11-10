# Uninstalling Upfront Prediction (completely)

`hermes plugins remove upfront` removes the plugin, its config, its aliases and its
OAuth grants. It does **not** remove everything the plugin created. This is a Hermes
gap, not a plugin choice, and it is why a reinstall can silently run old code.

## What survives `plugins remove`

| Left behind | Why |
|---|---|
| `~/.hermes/installs/*/environments/*/venv/**` — an **editable** `hermes-upfront` install per dependency environment | `plugins install --yes-deps` builds a venv per environment and installs the package editable; `remove` never revisits them |
| `~/.hermes/installs/*/environments/*/workspace/plugin-sources/upfront-*` | the source snapshot those builds came from — **a reinstall can build from this stale code** |
| `~/.hermes/plugin-data/upfront/` | run history. Kept on purpose: it is your data, and it survives `update`/`remove` |
| `~/.hermes/cache/plugin-update-locks/upfront.lock` | a stale update lock |
| `~/.hermes/cache/uv/**` entries named `hermes_upfront-*` | uv build-cache artifacts |

Measured on a real machine: **18 paths** survive the built-in remove.

## The complete drill

```bash
# 1. built-in removal (plugin, config, grants)
hermes plugins remove upfront

# 2. the rest — preview first, it changes nothing
python3 scripts/uninstall-clean.py upfront --dry-run

# 3. do it
python3 scripts/uninstall-clean.py upfront

# 4. proof: must print 0
find ~/.hermes -iname '*upfront*' | wc -l
```

`--keep-data` keeps `plugin-data/upfront` (your run history) if you want to reinstall
later and keep the ledger.

The script ends with the proof line itself — it re-scans after deleting and exits
non-zero if anything survived.

## If you installed through the desktop app

The app's **Uninstall** button removes the plugin tree; it does not run step 2. Follow
the same drill afterwards, with the same proof.

## Why this matters before a reinstall

`plugin-sources/upfront-*` holds a **copy of the code**. A reinstall that reuses that
snapshot can start from the code of an earlier commit — which is exactly how a "I
updated it but the UI never changed" bug happens. Purging between installs removes the
possibility.
