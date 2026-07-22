# AGENTS.md

## Project

Personal developer showcase built with Django 6, PostgreSQL 18 with
TimescaleDB, Redis, Celery, Channels, HTMX, and Tailwind CSS v4. Containers and
CI run Python 3.14; `pyproject.toml` defines the supported Python range.
Production runs Uvicorn behind Nginx, publishes images to GHCR, and deploys to a
Hetzner VM.

Treat manifests, settings, Compose files, and the code as the source of truth.
`PROJECT_MAP.md` is the concise repository map and should be updated when
responsibilities or important paths move.

## Local development

Create `.env` from `.env.example`, then run:

```bash
docker compose up --build
```

The application is available at `http://localhost:8000`. The repository is
mounted at `/app` in the Python containers. Do not expose additional host ports
unless the feature requires them. Rebuild the relevant images after changing
Python or system dependencies.

## Commands

Run Python commands in the `web` container. Always set `UV_CACHE_DIR` because
the development container user has no writable home directory.

```bash
# Targeted test: prefer the narrowest app, class, or method label
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py test core.tests.RequestLifecycleTests --settings=config.settings.test

# Full automated test suite
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py test --settings=config.settings.test

# Lint, format check, type check, and Django checks
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run ruff check .
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run ruff format --check .
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run mypy .
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py check --settings=config.settings.test
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py check --deploy --settings=config.settings.production

# Ordinary schema changes
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py makemigrations <app>
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py migrate

# Generated Tailwind output
npm run build:css

# Production Compose validation in PowerShell
$env:REDIS_PASSWORD="validation-only"; $env:POSTGRES_PASSWORD="validation-only"; docker compose -f docker-compose.prod.yml config --quiet

# Production Compose validation in POSIX shells
REDIS_PASSWORD=validation-only POSTGRES_PASSWORD=validation-only docker compose -f docker-compose.prod.yml config --quiet
```

Use `npm ci` on a fresh checkout or after frontend dependency changes. Use the
smallest validation that covers the change, escalate when shared behavior is
affected, and always run `git diff --check` after edits. The test settings use
SQLite in memory, disable app migrations, replace Redis/Channels with in-memory
backends, and omit visitor middleware; they do not validate TimescaleDB SQL,
production proxy behavior, or deployment configuration.

## Application boundaries

- `core/`: shared pages, health and metrics endpoints, system/GitHub services,
  Channels consumers, and the request-lifecycle demonstration.
- `blog/`: posts, Markdown rendering, public blog views, and blog templates.
- `dashboard/`: Energinet ingestion, electricity-price calculations,
  TimescaleDB models, Celery jobs, and dashboard HTMX partials.
- `showcase/`: public DRF demonstration endpoints and their service logic.
- `visitors/`: privacy-preserving visitor middleware, GeoIP processing,
  persistence, and background tasks.
- `config/`: settings, root URL routing, ASGI/Channels routing, and Celery
  configuration.

Keep views thin: parse HTTP input, perform basic validation, call services, and
return responses. Put business logic, non-trivial queries, calculations, and
external calls in the owning app's `services/` package without depending on
`HttpRequest`. Keep models, migrations, tasks, tests, and templates in their
owning app. The shared page shell is `core/templates/core/base.html`.

For DRF endpoints, preserve throttling and update `extend_schema` metadata when
request parameters, responses, or behavior change. External HTTP calls must
have explicit timeouts and testable failure behavior; mock them in unit tests.

## Data, time, and background work

- Store and query timestamps as timezone-aware UTC. Convert to
  `Europe/Copenhagen` only for Danish calendar boundaries, tariffs, and display.
  Cover DST-sensitive behavior when changing energy calculations.
- `dashboard.SpotPrice` is a TimescaleDB hypertable uniquely keyed by
  `(timestamp, price_area)`. Ingestion must remain idempotent for both DK1 and
  DK2.
- The hourly, daily, monthly, and yearly spot-price models map read-only
  continuous aggregates and must remain `managed = False`.
- Use generated migrations for ordinary Django schema changes. TimescaleDB
  hypertables, compression, policies, and continuous aggregates require
  explicit reversible SQL migrations and validation against PostgreSQL with
  TimescaleDB. Never rewrite an already-applied migration.
- Redis databases are intentionally separated: Celery broker `0`, result
  backend `1`, Django cache `2`, and Channels `3`. Coordinate any change across
  settings, workers, and deployment.
- Celery tasks should be bounded, idempotent where practical, and explicit
  about retries and time limits. Do not pass secrets or unnecessary visitor
  data in task payloads.
- Async Channels consumers must not call synchronous ORM or blocking I/O
  directly; use `database_sync_to_async` or `sync_to_async` at the boundary.
  Keep WebSocket routes in `config/ws_routing.py` and preserve production
  origin validation.

## Frontend

- Use `getattr(request, "htmx", False)` when selecting an HTMX partial versus a
  full page. Return app-owned partial templates for fragment requests.
- Preserve the existing `ds-*` design-system classes and Tailwind utilities.
  Bootstrap is not shipped. DaisyUI is a dependency, but do not replace the
  established design system with generic component classes.
- Edit `tailwind/tailwind.src.css`, templates, or source CSS as appropriate,
  then rebuild and commit `static/css/tailwind.css`; never hand-edit the
  generated Tailwind file.
- Prefer static JavaScript files for non-trivial behavior. When adding external
  browser resources or WebSocket endpoints, use explicit versions and update
  the Nginx Content Security Policy deliberately.
- Treat all server- and user-supplied values as untrusted. Prefer Django
  escaping, `json_script`, `textContent`, and DOM APIs. The blog Markdown
  pipeline must remain sanitized with `nh3`; do not use `mark_safe`, `|safe`,
  string-built HTML, or `innerHTML` for unsanitized values.

## Privacy and security invariants

- Never log, print, commit, or copy secrets. Document placeholders only in
  `.env.example`.
- Visitor analytics may use the direct proxy address from `X-Real-IP`, but must
  never trust client-supplied forwarding headers or persist/log raw IP
  addresses. Raw addresses are converted to daily salted hashes in the
  background GeoIP task.
- Keep bot, static/media, health, analytics API, non-success, and HTMX requests
  excluded from visitor tracking.
- The public visitor map must remain k-anonymous and approximate: group by
  coordinates rounded to one decimal degree, count distinct hashed visitors,
  expose only groups with at least three visitors, and never expose city,
  exact-location, raw-IP, or live per-visitor data.
- Keep API validation, CSRF protection, authentication boundaries, rate
  limits, allowed-host/origin checks, security headers, and Nginx's unknown-host
  rejection intact unless a requirement explicitly changes them.

## Dependencies and generated files

- Manage Python dependencies only through `pyproject.toml` and `uv.lock`. Use
  `uv add`/`uv remove`; do not add `requirements.txt`, `Pipfile`, or manually
  edit `uv.lock`.
- Manage frontend dependencies through `package.json` and `package-lock.json`.
  Do not add a bundler or frontend framework without an explicit need.
- Do not commit `.env`, credentials, certificates, database dumps,
  `*.egg-info`, `__pycache__`, local caches, Celery schedule files,
  `node_modules`, or runtime-collected static/media directories.

## Deployment and change discipline

- Keep GitHub Actions pinned to immutable commit SHAs. Preserve least-privilege
  permissions, locked installs, build cache, SBOM, and provenance generation.
- Production uses immutable commit-SHA image tags. Changes to
  `Dockerfile.prod`, `docker-compose.prod.yml`, `.github/workflows/deploy.yml`,
  `deploy.sh`, `rollback.sh`, `setup_hetzner.sh`, or `nginx/` must preserve
  health checks, WebSocket proxying, static/media mounts, migrations, and
  rollback behavior. Validate the production Compose file after such changes.
- Read nearby code and tests before modifying behavior. Add regression tests
  for behavior changes, keep edits focused, and do not revert unrelated
  working-tree changes.
- Update documentation when commands, architecture, environment variables, or
  user-visible behavior change.
- Do not commit, push, rewrite history, or run destructive Git commands unless
  explicitly requested.
