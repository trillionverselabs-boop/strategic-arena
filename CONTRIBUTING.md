# Contributing to Upfront

Thanks for your interest. Upfront is a small, local-first plugin; contributions are welcome.

## Ground rules

- **Be kind.** Treat everyone with respect. See [Code of Conduct](CODE_OF_CONDUCT.md).
- **Credit ideas.** If you borrow from a paper or project, cite it. Upfront credits
  GraphRAG, Generative Agents, OASIS, MASS, and CAMEL; we ask the same of
  contributors.
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
