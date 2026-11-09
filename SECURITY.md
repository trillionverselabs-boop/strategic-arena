# Security Policy

## Reporting

Please report security issues privately. Do not open a public GitHub issue for a
vulnerability.

Email: camel.ai.team@gmail.com (or open a private advisory via GitHub).

## Scope

Upfront runs locally and stores data under `~/.hermes/upfront/`. It does not
store credentials; model access goes through Hermes' host-owned `ctx.llm`. URL
fetching is capped (http/https only, size and length limits, hard timeout).

## Supported versions

Only the latest release on `main` is supported.
