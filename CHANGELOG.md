# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-04-22

### Added
- Initial public release of `emergentintegrations` as a lightweight async LLM chat client.
- `LlmChat`, `UserMessage`, `ImageContent`, `FileContentWithMimeType`, `ChatError` classes.
- Automatic routing for `sk-emergent-*` API keys through `${INTEGRATION_PROXY_URL:-https://integrations.emergentagent.com}/llm`.
- `X-App-ID` header injection from `APP_URL` / `REACT_APP_BACKEND_URL` environment variables.
- Backwards-compatible import paths matching the historic CDN-published SDK: `emergentintegrations`, `emergentintegrations.llm.chat`, `emergentintegrations.llm.openai`, `emergentintegrations.llm.utils`.
- GitHub Actions CI workflow: ruff lint + format check + pytest across Python 3.10–3.14.
- GitHub Actions release workflow: OIDC trusted publishing to PyPI via `pypa/gh-action-pypi-publish`.

[Unreleased]: https://github.com/emergentbase/emergentintegrations/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/emergentbase/emergentintegrations/releases/tag/v0.1.1
