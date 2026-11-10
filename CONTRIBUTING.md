# Contributing to Strategic Arena

Thanks for your interest. Strategic Arena (`upfront`) is a small, local-first
plugin; contributions are welcome.

The plugin id, the folder name, the tool prefixes (`upfront_*`) and the data
directory are deliberately stable — they are what installs, the catalogue pin and
the desktop plugin loader depend on. A change to any of them is a breaking change
and needs an issue first.

## Ground rules

- **Be kind.** Treat everyone with respect. See [Code of Conduct](CODE_OF_CONDUCT.md).
- **Credit ideas.** If you borrow from a paper or project, cite it. Every source
  this project draws on is listed in [CREDITS.md](CREDITS.md) with an identifier and
  its licence status; we ask the same of contributors. **No AGPL code**: MiroFish is
  AGPL-3.0 and this repository is MIT, so a patch that copies from it cannot be
  merged — cite it instead.
- **No invented numbers in the UI.** If a figure cannot be computed, it does not go
  on the page. The tests enforce the two we had to delete.
- **Local-first stays.** Don't add cloud dependencies, telemetry, or credential
  storage. Model access goes through Hermes' `ctx.llm`.

## How to contribute

1. Fork and clone the repo.
2. Install dev deps: `pip install -e ".[test]"`.
3. Run tests: `python -m pytest tests/ -q`.
4. Validate the plugin: `hermes plugins validate .`.
5. Open a PR with a clear description of the change and why.

## What we'd love help with

- Better stakeholder extraction from messy documents.
- New bundled skills (launch, pricing, deprecation, open-weight, review).
- Translations of UI strings.
- Bug reports with reproduction steps.

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not open public issues for security bugs.

## License

By contributing, you agree your contributions are licensed under the MIT
License (see [LICENSE](LICENSE)).
