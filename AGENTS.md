# AGENTS.md

## Project

Personal developer showcase built with Django 6, Python 3.14, PostgreSQL 18 with
TimescaleDB, Redis, Celery, HTMX, and Tailwind CSS v4. Production runs Uvicorn
behind Nginx; images are published to GHCR and deployed to a Hetzner VM.

## Local development

```bash
cp .env.example .env
docker compose up --build
```

The Django application is available at `http://localhost:8000`. The project
directory is mounted into the `web` container. Do not expose new ports unless
the feature requires it.

## Commands

Run Python commands in the `web` container. `UV_CACHE_DIR` is required there
because the container user has no writable home directory.

```bash
# Lint, format check, type check, and Django checks
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run ruff check .
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run ruff format --check .
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run mypy .
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py check --settings=config.settings.test

# Tests
docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run python manage.py test --settings=config.settings.test

# Rebuild generated Tailwind output after changing templates, Tailwind source, or design-system classes
npm run build:css

# Validate deployment Compose syntax without real secrets
REDIS_PASSWORD=validation-only POSTGRES_PASSWORD=validation-only docker compose -f docker-compose.prod.yml config --quiet
```

Use the smallest command that covers the change. Run the applicable validation
before finishing and always run `git diff --check` after edits.

## Architecture and code

- Keep views thin: parse HTTP input, perform basic validation, call a service,
  and return a response. Put business logic, non-trivial queries, algorithms,
  and external calls in `services/` without depending on `HttpRequest`.
- Keep models, migrations, serializers, tasks, and templates in their
  respective Django app. Create and apply migrations for schema changes; never
  hand-edit generated migration files after they are shared.
- Use explicit type hints for new public functions, methods, and non-obvious
  variables. Follow Ruff and existing naming patterns.
- Use `getattr(request, "htmx", False)` when a view must select a partial for
  an HTMX request versus a full page response.
- Preserve the design system and Tailwind utilities. Avoid Bootstrap classes:
  Bootstrap CSS is not shipped. Rebuild `static/css/tailwind.css` rather than
  editing the generated file by hand.
- Treat all server- or user-supplied data as untrusted. Prefer Django escaping,
  `json_script`, and DOM APIs over `|safe`, string-built JavaScript, or
  `innerHTML`.

## Dependencies and generated files

- Manage Python dependencies only through `pyproject.toml` and `uv.lock`.
  Use `uv add`/`uv remove` and commit the lockfile update. Do not add
  `requirements.txt`, `Pipfile`, or manually edit `uv.lock`.
- Manage frontend dependencies with `package.json` and the committed npm lock
  file. Do not add a bundler or frontend framework without an explicit need.
- Never commit `.env`, credentials, certificates, database dumps, generated
  `*.egg-info`, or runtime-collected staticfiles/media output.

## Security and deployment

- Never log, print, commit, or copy secrets. Use `.env.example` for documented
  placeholders only.
- Keep GitHub Actions actions pinned to immutable commit SHAs. Preserve
  least-privilege job permissions, locked dependency installation, SBOM, and
  provenance in `.github/workflows/deploy.yml`.
- Production deploys immutable commit-SHA image tags. Changes to
  `docker-compose.prod.yml`, `deploy.sh`, `rollback.sh`, or `nginx/` must
  retain health checks and rollback behavior and should be validated with the
  production Compose command above.
- The public visitor map must remain privacy-preserving: no exact locations or
  live per-visitor data; only rounded groups meeting the minimum anonymity
  threshold may be exposed.

## Change discipline

- Read nearby code and tests before modifying behavior. Keep changes focused;
  do not revert unrelated working-tree changes.
- Update documentation when commands, architecture, environment variables, or
  user-visible behavior change.
- Do not commit, push, rewrite history, or run destructive Git commands unless
  explicitly requested.
