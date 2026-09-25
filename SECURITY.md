# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

Until 1.0, security fixes are released on the latest minor version only.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Report privately through either channel:

- GitHub → **Security** tab → *Report a vulnerability* (private advisory), or
- email **security@novagios.com**

Please include a description of the issue, steps to reproduce, and the affected version.

We aim to acknowledge a report within 5 business days, and to ship a fix or provide a
timeline within 30 days. We will credit you in the advisory unless you prefer otherwise.

## What this library does and does not do

`glpi-rest` is a thin HTTP client. It:

- communicates **only** with the GLPI server URL you supply,
- collects no telemetry and contacts no third-party service,
- writes nothing to disk and caches no credentials,
- holds the session token in memory for the lifetime of the client object only.

## Security defaults

These are enabled by default and should not be disabled in production:

| Default | Why |
|---|---|
| `verify_ssl=True` | Prevents man-in-the-middle interception of your tokens. |
| `timeout=30.0` | An unresponsive server cannot hang your application indefinitely. |
| Credentials in headers | Query strings are recorded in server, proxy and browser logs. |
| Session closed on context exit | An abandoned session token stays valid server-side. |
| Single reconnect attempt | Prevents a credential failure turning into a request flood. |
| Masked `__repr__` | Tokens are not exposed by debuggers, log dumps or crash reporters. |
| Truncated error details | Limits how much of a server response can leak into your logs. |

## Recommendations for users

- **Use a dedicated GLPI account** with the minimum profile your automation needs — not a
  super-admin account. A leaked token then grants only what that profile allows.
- **Prefer a user token over username and password.** A token can be revoked from the GLPI
  interface without changing a person's credentials.
- **Pass secrets via environment variables**, never hard-coded and never committed.
- **Rotate the App token and user tokens** if a machine holding them is decommissioned or
  compromised.
- **Serve GLPI over HTTPS.** The API sends tokens on every request; over plain HTTP they
  are readable by anyone on the network path.
