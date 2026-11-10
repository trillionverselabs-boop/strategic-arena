# Security Policy

## Reporting

Please report security issues privately. Do not open a public GitHub issue for a
vulnerability.

**Open a private advisory via GitHub** — Security → Advisories → "Report a
vulnerability" on this repository. That is the only channel: it is private, it
carries the report to the maintainer, and it threads the fix. (No email address is
published on purpose — a security mailbox that nobody monitors is worse than none.)

## Scope

Strategic Arena (`upfront`) runs locally and stores every run under the plugin's
own data directory — `~/.hermes/plugin-data/upfront/runs/<run_id>/` on a single
profile, or the same path under `~/.hermes/profiles/<profile>/` under multiplexing.
It does not store credentials: model access goes through Hermes' host-owned
`ctx.llm`, and the plugin never reads `.env`, `auth.json`, a vendor CLI token or a
keychain. URL fetching is capped (http/https only, size and length limits, hard
timeout, no redirect to a non-http scheme).

**In scope:** the plugin's own code — prompt construction, the extraction and
friction paths, the `/api/plugins/upfront/` routes, the desktop UI file, and the
run data on disk.

**Out of scope:** the model's output (a wrong answer is a product limitation, not a
vulnerability — see `CREDITS.md` for what we claim and what we do not), Hermes core
itself (report to `NousResearch/hermes-agent`), and anything requiring an attacker
who already has your shell.

## Supported versions

Only the latest release on `main` is supported.
