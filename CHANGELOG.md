# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-08-26

First public release.

### Added

- `GLPIClient` with session management (`init_session`, `close`) and context-manager
  support, authenticating by user token or username/password.
- **Automatic session recovery**: a `401` triggers one transparent re-authentication and a
  replay of the original request, body included. Never retried more than once.
- CRUD helpers: `get_item`, `get_items`, `add_item`, `update_item`, `delete_item`
  (with `force_purge` to bypass the trash bin).
- Multi-criteria `search()` accepting `SearchCriterion` objects, with `forcedisplay`,
  `sort`, `order` and `range_`, returning a typed `SearchResult`.
- Typed exception hierarchy: `GLPIError`, `GLPIAuthError`, `GLPISessionError`,
  `GLPINotFoundError`.
- Full type annotations with a `py.typed` marker; passes `mypy --strict`.
- Security defaults: TLS verification on, 30 s request timeout, credentials sent as
  headers, credential-masking `__repr__`, and truncated error details to limit log leakage.
- Test suite of 27 tests running against a mocked GLPI API — no server required.
- Integration suite (`tests/test_integration.py`) exercising session lifecycle,
  both authentication modes, CRUD, search and end-to-end session recovery
  against a live server. Passing against GLPI 11.0.2, 11.0.8 and 10.0.26;
  skipped unless `GLPI_TEST_URL` is set.
- `docker-compose.test.yml`, `scripts/enable-api.sh` and
  `scripts/seed_api_client.php` to bring up disposable GLPI 10 and GLPI 11
  instances, enable their REST API and register test credentials. App tokens
  are seeded through GLPI's own `APIClient` class because GLPI 11.0.3+ stores
  them encrypted.
- Weekly `integration.yml` workflow running the suite against live GLPI 10 and
  11 containers, to catch upstream API changes.
- CI across Python 3.10–3.13 with `pytest`, `ruff` and `mypy`.

[Unreleased]: https://github.com/novagiosAI/glpi-rest/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/novagiosAI/glpi-rest/releases/tag/v0.1.0
