# Contributing to glpi-rest

Thanks for taking the time to contribute. Bug reports, documentation fixes and pull
requests are all welcome.

## Getting set up

```bash
git clone https://github.com/novagiosAI/glpi-rest.git
cd glpi-rest
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Before opening a pull request

All three must pass — they are the same checks CI runs:

```bash
pytest              # test suite
ruff check .        # linting
ruff format .       # formatting
mypy                # strict type checking
```

Tests run against a mocked GLPI API, so you do not need a GLPI server to contribute.

## Reporting a bug

Please open an issue including:

- your GLPI version (10.x / 11.x) and Python version,
- the smallest snippet that reproduces the problem,
- the full traceback.

**Never paste real tokens, hostnames or ticket contents into an issue.** Redact them
first — issues are public and permanently indexed.

## Pull requests

- One logical change per pull request.
- Add a test for any behaviour you fix or introduce. A bug fix without a regression test
  will likely be asked to add one.
- Update `README.md` if you change public behaviour, and add a `CHANGELOG.md` entry under
  *Unreleased*.
- Keep the public API typed; `mypy` runs in strict mode.

## Design principles

These guide what gets merged:

1. **Fail loudly, never silently.** Errors surface as typed exceptions with a clear
   message rather than `None` or an empty result.
2. **Safe defaults.** TLS verification stays on, requests keep a timeout, credentials
   never travel in URLs. A change that weakens a default needs a strong justification.
3. **Minimal dependencies.** `requests` is the only runtime dependency, and we intend to
   keep it that way.
4. **Support both GLPI 10 and 11.** Behaviour that differs between versions should be
   handled inside the client, not pushed onto the user.

## Security issues

Do not open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE).
