# Vendored library: firebase/php-jwt

- Upstream: https://github.com/firebase/php-jwt
- License: BSD-3-Clause (copyright Neuman Vong / Firebase)
- Date recorded: 2026-08-01

## Vendoring note

Only `src/` was committed to this repo; the upstream `LICENSE` file was
missing (stripped during vendoring). It has been restored verbatim from
`https://raw.githubusercontent.com/firebase/php-jwt/main/LICENSE` as
`api/vendor/firebase/php-jwt/LICENSE`.

## Best-known version

No tagged release matches this snapshot exactly. Based on source comparison
against firebase/php-jwt's git history, the vendored `src/JWT.php` sits
**between the `v6.11.1` and `v7.0.0` tags** — i.e. an untagged snapshot of
`main` from roughly August-December 2025, not a numbered release.

Evidence:
- `src/` contains only `JWT.php`, `Key.php`, `BeforeValidException.php`,
  `ExpiredException.php`, `SignatureInvalidException.php`, and
  `JWTExceptionWithPayloadInterface.php` (no `JWK.php` / `CachedKeySet.php` —
  those are simply not vendored here, not a version signal).
- `JWTExceptionWithPayloadInterface.php` first appears upstream at `v6.9.0`
  (absent in `v6.8.0`), so the floor is `>= v6.9.0`.
- `JWT::decode`/`encode`/`sign`/`verify` use the `#[\SensitiveParameter]`
  attribute, added in PR #603 (merged 2025-08-07). Not present in `v6.11.1`.
- `ExpiredException` has `setTimestamp()`/`getTimestamp()`, added in PR #604
  (merged 2025-08-19, "store timestamp in ExpiredException"). Also absent in
  `v6.11.1`.
- `JWT::decode` validates that `iat`/`nbf`/`exp` are numeric, and the nbf/iat
  checks use `floor()` + `DateTime::ATOM` (not `DateTime::ISO8601`) — matches
  the `main` branch after PR #568 / commit `43d70ae8d` (April 2025).
- Crucially, the vendored `JWT.php` has **no** `RSA_KEY_MIN_LENGTH` constant
  and **no** `validateHmacKeyLength()`/`validateRsaKeyLength()` methods. Those
  were added by PRs #612/#613/#615 (merged 2025-12-15/16) and are present in
  every version from `v7.0.0` onward. Their absence rules out `v7.0.0+`.

So: newer than `v6.11.1`, older than `v7.0.0`, with no tag in between —
this is a pre-release/dev checkout of `main`, closest to the `v6.11.x` /
early `v7.0.0`-track code.
