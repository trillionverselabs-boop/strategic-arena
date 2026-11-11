# Desktop updates — how a UI change reaches the window

**The finding (2026-11-10, corrected the same day).** The plugin has two halves
and they can live on different machines. The app loads `desktop/plugin.js`
**from the machine the window runs on** — which, in this setup, is the user's
computer, not the lisacore backend. `hermes plugins update strategic-arena` on the
server updates the engine; it never reaches that window.

**The second finding, the one that matters day to day:** *reloading the page
cannot fix a stale window.* The Reload button only reloads the page; the file it
would need to change is on another machine. The old UI said "press Reload UI" —
that was a lie, and it is why the button looked broken.

## What each thing actually does

| Action | What it really does | Fixes a stale window? |
|---|---|---|
| **Reload page** (the header button) | reloads this page in the renderer | **No** — the file is on the window's machine |
| **⌘K → Reload desktop plugins** | re-reads every known plugin file from disk | **Only if the file there is already new** |
| **Install from Git with the Desktop target** (on the window's machine) | the app clones the desktop half into its own folder | **Yes** — the app copies it and reloads |
| **App → Plugins → Update** | the app re-clones the pinned commit | **Yes** |
| **Save the new `plugin.js` over the copy** | replaces one file | **Yes** — the app watches that file and hot-reloads it in place |

## The two fixes that work — neither needs a restart

**1. Update in the app** (preferred; the app does the copying)

On the machine running the app: **Capabilities → Plugins → Install from Git** →
`trillionverselabs-boop/strategic-arena` → tick **Desktop** → Install. Then
⌘K → **Reload desktop plugins**. The app copies the file itself and reloads it.

**2. Save the file over the copy** (fallback, one file)

Save the new UI file to
`%USERPROFILE%\.hermes\desktop-plugins\strategic-arena\plugin.js` on the window's
machine, replacing the existing one. The app fs-watches that file, so it
hot-reloads the page **in place — no restart, no ⌘K**.

When the window's build is older than the installed build, the page says so and
offers **Open plugin settings** — a navigation into the app's own Plugins tab, so
the update follows the app's path.

**It deliberately does not update itself** (catalog admission rule 03): a listed
plugin may not fetch or replace its own files, because the pinned SHA is the
trust model. An earlier build of this page offered a "download the UI file"
button. It was manual and it only copied a local file, but it is the shape the
rule names, so it was removed — `tests/test_no_self_update.py` keeps it gone.

## The backend half has the same problem, and it is the one that bites

The backend (`dashboard/plugin_api.py`) is imported **once**, when the gateway
process starts, and cached in `sys.modules`. Editing the plugin on disk does not
change the code a running process serves. So after a backend fix:

| Symptom | Cause | Fix |
|---|---|---|
| the UI is new but the error text is old | the running gateway still has the previous `plugin_api.py` cached | restart the gateway (or reconnect the desktop, which spawns a fresh remote backend) |
| `/api/plugins/<id>/...` returns a 404 | the plugin wasn't enabled/mounted at that process's startup | enable it, then restart |

The desktop's own plugin REST goes to the gateway the window is connected to —
a remote `hermes serve` on the Hermes machine, spawned when the window connects.
Restart the **backend**, not the app, and the window reconnects to a fresh one.

## Why ⌘K alone felt like it did nothing

`Reload desktop plugins` re-reads the files it already knows about — it fetches
nothing. If the file on the window's machine is still the old one, the reload
faithfully shows the old build. It is not broken; there was nothing new to read.

Also worth knowing: toggling a desktop plugin off/on does **not** re-read
`plugin.js` (the module is cached) — use ⌘K, or quit the app from the tray.

## How to tell which build the window is on

The header prints `build <version> · ui<N>`. `GET /api/plugins/strategic-arena/ui`
compares it against the build the backend has installed and returns an honest
hint — it no longer says "reload the page".

| Header reads | Meaning |
|---|---|
| `build 0.5.0 · ui12` | this window is on the installed build. Done. |
| `build 0.5.0 · ui12 → 0.5.0 · ui12 installed` | the window is behind; the banner says how to fix it. |

## Known core behaviour to remember

- Old copies of the desktop half accumulate under
  `~/.hermes/installs/<env>/…/plugin-sources/strategic-arena-*/desktop/plugin.js`. They
  are inert, but they make a "which build is live?" search confusing — read the
  `BUILD` constant in the file the window actually loads
  (`~/.hermes/desktop-plugins/strategic-arena/plugin.js`), not the newest one found.
- A headless backend has no window at all: verifying "the UI looks right"
  remotely requires the user's eyes, or a screenshot from their machine.

## Verification checklist for any UI change

1. `node --check desktop/plugin.js` — no build step; a syntax error is a blank page.
2. `pytest -q` — `tests/test_ui_presets.py` and `tests/test_ui_download.py` guard
   the copy, the structure, and the download path.
3. Bump `BUILD` in `desktop/plugin.js` **and** `version` in `plugin.yaml`.
4. Publish: put the repo's `desktop/plugin.js` where the window can read it —
   the app's Install/Update path on that machine, or the file itself.
5. Tell the user the expected `build …` string and ask them to confirm the
   header. Never report "the UI is updated" from the server side alone.
