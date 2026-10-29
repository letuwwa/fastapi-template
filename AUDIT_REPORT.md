# Codebase audit and stabilization report

Date: 2026-10-29

## 1. Project overview

Inspected all tracked application modules, database models, three Alembic revisions,
migration environment, tests, dependency manifests, documentation, Docker files,
and environment examples. The starting working tree was clean; no AGENTS.md files
were found in the project or its parent project directory.

This is a Python 3.14 FastAPI authentication starter. Synchronous routes use
SQLAlchemy sessions and PostgreSQL. Pydantic validates request bodies and settings;
pwdlib/Argon2 verifies passwords; PyJWT signs access/refresh tokens. Both tokens
share a session identifier. Refresh and logout insert a unique blocklist entry,
revoking the pair; refresh creates a new pair. Authorization reads the user's
current active status and role from the database. Alembic manages the schema.
Docker starts migrations before serving the API as a non-root user.

The existing test suite already covered most authentication paths. SQLite tests
isolate HTTP behavior; explicitly invoked PostgreSQL tests validate schema
alignment, migration reversibility, and competing registration/refresh writes.
The baseline was 79 passing default tests, approximately 95% application line and
branch coverage, and three passing PostgreSQL checks.

## 2. Issues discovered

Locations below refer to the final files.

| Severity | Location | Problem and impact | Status |
| --- | --- | --- | --- |
| Medium | `app/core/security.py:30` | pwdlib raises `UnknownHashError` for empty, damaged, or unsupported stored hashes. Both login routes propagated the exception as a server failure instead of rejecting credentials. | Fixed; six HTTP regression cases cover both routes and three invalid hash forms. |
| Medium | `app/core/settings.py:59` | Positive refresh lifetimes could exceed timedelta or datetime limits. Settings accepted them, but token creation raised `OverflowError`; registration could commit an account before failing to return tokens. | Fixed; startup validation rejects unrepresentable lifetimes, with three regression cases covering timedelta and calendar overflow. |
| Low | `pyproject.toml:19` | Coverage tooling and a repeatable minimum threshold were absent despite existing tests. Security and resource-cleanup failure paths had coverage gaps. | Fixed; pytest-cov is locked as a development dependency, with branch measurement and an 85% application coverage gate when coverage is requested. |

No additional confirmed correctness defects were established during this review.
Existing deployment boundaries below remain recommendations, rather than claims
that every possible production or dependency vulnerability has been ruled out.

## 3. Changes implemented

- Password verification catches only the documented unknown-hash exception,
  emits a warning without password/hash data, performs dummy password verification,
  and returns false. Existing login handling returns the usual 401 Bearer challenge.
  This preserves denial of access and comparable password-verification work.
  Unsupported account data still requires operator repair; hashes are never rewritten.
- Token settings validate that the refresh expiry can be represented at startup.
  The existing requirement that access lifetime cannot exceed refresh lifetime
  ensures the shorter access lifetime also fits. No arbitrary business lifetime
  limit was introduced.
- Added focused unit and HTTP tests for required JWT claims, wrong signatures,
  expired/future-dated tokens, invalid/deleted subjects, database-session closure
  after success and failure, independent-login revocation, each duplicate identifier,
  the root response, and offline migration SQL in both directions.
- Added credential-free warning assertions to hash regression tests.
- Added pytest-cov and its coverage dependency without updating existing dependency
  versions. Coverage artifacts are excluded from Git and Docker build context.
- Documented coverage commands, configuration validation, and malformed-hash handling.

Public routes, schemas, roles, token contracts, and normal authentication behavior
are preserved. No migrations, database schemas, production infrastructure, or new
product features were added. Broader restructuring was unnecessary for this codebase.

## 4. Testing and validation

### Executed results

| Check | Result |
| --- | --- |
| Default pytest suite, warnings treated as errors | 108 passed |
| Complete suite including explicit PostgreSQL checks | 111 passed in 6.58 seconds |
| Default suite application line + branch coverage | 97.26% |
| Complete suite application line + branch coverage | 98.90% |
| Complete suite application + local migration line + branch coverage | 97.52% |
| Application + migration statement coverage | 392/399 statements, 98.25% |
| Application + migration branch coverage | 40/44 branches, 90.91% |
| Ruff lint | Passed |
| Ruff format check | Passed |
| uv lock consistency, offline | Passed |
| Docker Compose configuration, temporary test signing key | Passed |
| Entrypoint shell syntax | Passed |
| Final whitespace/error diff check | Passed |

Added 29 default test cases; the existing three PostgreSQL checks remain intact.
Tests ran with Python 3.14.3 and PostgreSQL 18.6. PostgreSQL checks used a disposable
cluster under `/tmp`, with unique per-test schemas; no configured application
database was accessed. The cluster was stopped after validation.

The new bug regressions were executed before production fixes: all three lifetime
cases failed because settings accepted invalid values, and the first login hash
case raised `UnknownHashError`. All nine targeted cases passed after the fixes.

Reproduce the default checks:

```bash
uv run pytest --cov -W error
uv run ruff check .
uv run ruff format --check .
uv lock --check
```

Reproduce the complete suite against an isolated PostgreSQL test database:

```bash
TEST_POSTGRES_URL='postgresql+psycopg2://user:password@localhost:5432/test_db' \
  uv run pytest tests/test_*.py tests/postgres_checks.py \
  --cov=app --cov=./alembic -W error
```

Use explicit filenames when combining these suites: in the installed pytest,
passing the parent `tests` directory alongside the nonstandard PostgreSQL filename
omitted that module through collection deduplication. Use `./alembic` as a coverage
filesystem path to avoid ambiguity with the installed library of the same name.
Both behaviors were identified during validation and the corrected command above
was executed successfully.

### Remaining coverage gaps and limits

- `app/api/v1/auth.py:132` and `:148` are defensive guards after token decoding
  already rejects those invalid claims. They were retained and not bypassed merely
  to raise coverage.
- `alembic/env.py:57` through the engine-disposal path is not covered: integration
  tests deliberately inject connections bound to isolated schemas. Offline SQL,
  injected-connection migrations, every revision's upgrade/downgrade, schema
  alignment, and race handling were exercised. The no-configuration-file logging
  branch also remains uncovered.
- Initial HTTP runs stalled in the socket-restricted sandbox; successful validation
  used execution with the required local socket permissions. No tests were weakened
  to accommodate that environment restriction.
- Compose configuration and shell syntax were validated. Docker image building and
  a complete container deployment were not executed. No static type checker is
  configured. Dependency locking was verified; no CVE/database security scan was run.

## 5. Remaining recommendations

These are future work, not implemented changes:

1. Run both SQLite/HTTP coverage and the explicit PostgreSQL checks in CI, using
   the documented filenames so migration and concurrency checks cannot be missed.
2. Before public deployment, implement the already documented gateway limits,
   HTTPS, trusted proxy configuration, and shared authentication rate limits.
   These depend on deployment requirements and were outside this stabilization task.
3. Use persistent database storage and backups for environments requiring durable
   data; Compose currently documents disposable anonymous-volume storage.
4. Consider database connection/statement timeouts and operational handling of
   unavailable PostgreSQL based on deployment latency requirements. Those requirements
   were not inferred or introduced here.
5. Add container smoke tests, connection-owning Alembic execution tests, and a
   dependency vulnerability scan to deployment validation. These complement the
   successful migration and API behavior checks performed here.
