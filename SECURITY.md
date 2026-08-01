# Security Policy

## Supported Versions

Only the `main` branch is supported. There are no maintained release branches — always deploy from `main`.

## Reporting a Vulnerability

Please report security issues privately, not via public GitHub issues:

- Preferred: use [GitHub Security Advisories](../../security/advisories/new) for this repository.
- Alternative: email ciscodg@gmail.com.

Please include steps to reproduce and the potential impact. We'll acknowledge reports as soon as possible.

## Areas of Particular Interest

This app handles user authentication (passwords, JWTs, magic-link password reset) and exposes a
web-reachable exec shim (`worker/web_shim.php`) used to trigger backend jobs from the frontend.
Reports touching authentication, the PHP API, or `web_shim.php` are especially welcome.
