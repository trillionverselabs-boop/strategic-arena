# Desktop updates — how a UI change reaches the window

**The finding (2026-11-10).** The plugin has two halves, and they can live on
different machines. The app loads `desktop/plugin.js` **from the machine the
desktop app runs on**; it cannot copy a desktop half out of a remote backend.
`hermes plugins update upfront` on the server updates the engine and the
server-side half — it never reaches a window on another machine.

Symptom: the window keeps showing an old `build` number forever, and the new
`Reload UI` button never appears, no matter how many times the server is updated.

## The two halves

| Half | File | Runs where | Updated by |
|---|---|---|---|
| Agent half | `plugin.yaml`, `*.py`, `dashboard/plugin_api.py` | lisacore (the backend) | `hermes plugins update upfront` |
| Desktop half | `desktop/plugin.js` | **the machine running the desktop app** | the app's own install/reload path |

In the normal case (app and Hermes on the same machine) the app copies the
desktop half into `~/.hermes/desktop-plugins/<id>/` and refreshes it from that
local copy. Against a **remote backend** the remote `~/.hermes/plugins` is not a
filesystem the window can see, so that copy has to come from an install that
targets the desktop.

## The supported path (per the SDK guide, *One package, both SDKs*)

> For a remote backend the install dialog clones the desktop half separately
> into `desktop-plugins/`, the same as a desktop-only repo. A package whose
> agent half was installed on the remote host without that clone shows its
> Desktop half as **unavailable (remote backend)** on the Plugins page.

So, on the machine running the app:

1. **Capabilities → Plugins → Install from Git** → `trillionverselabs-boop/upfront-test`.
2. Tick the **Desktop** target (leave the backend target to the server install).
3. Install → then **⌘K → "Reload desktop plugins"**.

The Plugins page will also offer **Update** on the entry once the pin moves; that
pulls the new desktop half the same way.

## How to tell which build the window is actually on

The page header prints a `build <version> · ui<N>` pill, and the backend exposes
`GET /api/plugins/upfront/ui?build=…` which compares it to the installed copy.

| Header reads | Meaning |
|---|---|
| `build 0.5.0 · ui12` | the window is running the installed file. Done. |
| `build 0.5.0 · ui12 → 0.5.0 · ui12 installed` | in sync (the arrow form appears when they differ). |
| anything older | the window is stale — click **Reload UI**, then ⌘K if that fails. |

**Reload UI** does two things: it asks the backend to re-publish the installed
copy (`POST /ui/refresh`, which re-reads the repo's `desktop/plugin.js` into
`~/.hermes/desktop-plugins/upfront/`), then reloads the page. It is the button
that exists only from build 0.4.6 onward — its absence is itself the diagnosis.

## Known core behaviour to remember

- **Toggling a desktop plugin off/on does not re-read `plugin.js`.** The module
  is cached; use **⌘K → Reload desktop plugins**, or quit the app from the tray
  and reopen it.
- Old copies of the desktop half accumulate under
  `~/.hermes/installs/<env>/…/plugin-sources/upfront-*/desktop/plugin.js`. They
  are inert, but they make a "which build is live?" search confusing — always
  read the `BUILD` constant in the file the window actually loads
  (`~/.hermes/desktop-plugins/upfront/plugin.js`), not the newest one found.
- A headless backend has no window at all: verifying "the UI looks right"
  remotely requires the user's eyes, or a screenshot from their machine.

## Verification checklist for any UI change

1. `node --check desktop/plugin.js` (no build step; a syntax error is a blank page).
2. `pytest -q` — `tests/test_ui_presets.py` guards the copy and structure decisions.
3. Bump `BUILD` in `desktop/plugin.js` **and** `version` in `plugin.yaml`.
4. Publish: copy the repo's `desktop/plugin.js` to
   `~/.hermes/desktop-plugins/upfront/plugin.js` on the machine the app runs on
   (the app's own Install/Update path is the user-facing version of this).
5. Tell the user the expected `build …` string, and ask them to confirm the
   header shows it. Never report "the UI is updated" from the server side alone.
