# Project map

This is a navigation aid. The code, manifests, settings, and Compose files are
the source of truth.

## Django apps

### `core/`

- `views.py`: homepage, architecture, visitor map, health, metrics, and
  request-lifecycle endpoints.
- `consumers.py`: presence, electricity-price, and request-lifecycle WebSocket
  consumers.
- `tasks.py`: bounded Celery work for the request-lifecycle demonstration.
- `services/github_service.py`: cached GitHub API integration.
- `services/system_metrics.py`: database and host metrics.
- `services/request_lifecycle.py`: cache probe, rate-limit hashing, and
  Channels progress publishing.
- `templates/core/base.html`: shared base template extended by public pages.
- `templates/core/`: homepage, about, architecture, API playground, visitor
  map, dashboard, and partial templates.
- `templates/registration/`: authentication templates.

### `blog/`

- `models.py`: blog post model and publication state.
- `views.py` and `urls.py`: public index, paginated HTMX list, and detail
  routes.
- `templatetags/markdown_extras.py`: Markdown conversion followed by `nh3`
  sanitization.
- `templates/blog/`: full pages and HTMX list partial.
- `management/commands/populate_blog.py`: development content seeder.

### `dashboard/`

- `models.py`: the `SpotPrice` hypertable model and unmanaged read-only
  TimescaleDB continuous-aggregate models.
- `views.py` and `urls.py`: dashboard shell and HTMX chart/hero fragments.
- `services/energinet.py`: timeout-bounded Energi Data Service ingestion and
  idempotent DK1/DK2 upserts.
- `services/current_price.py`: current-price, comparison, and cache logic.
- `services/price_chart.py`: UTC/Copenhagen period handling, Danish tariffs,
  and chart series.
- `tasks.py`: scheduled ingestion and WebSocket price broadcasts.
- `migrations/`: Django schema plus TimescaleDB hypertable, compression,
  policy, and continuous-aggregate SQL.
- `management/commands/`: price polling and historical backfills.

### `showcase/`

- `views.py` and `urls.py`: public DRF showcase endpoints with
  drf-spectacular metadata.
- `services/algorithms.py` and `services/content.py`: endpoint-independent
  demonstration logic.

### `visitors/`

- `middleware.py`: filters eligible page views and queues processing using the
  direct proxy address.
- `services/geoip.py`: local MaxMind lookup and daily salted IP hashing.
- `tasks.py`: background GeoIP lookup and page-view persistence.
- `models.py`: approximate location, hashed visitor, path, and device data.

## Configuration

- `config/settings/base.py`: shared Django, Redis, Channels, DRF, logging,
  Sentry, Celery, and beat configuration.
- `config/settings/development.py`: local debug behavior.
- `config/settings/test.py`: in-memory SQLite/cache/channel layer with
  migrations and visitor middleware disabled.
- `config/settings/production.py`: HTTPS, cookies, HSTS, WhiteNoise, and JSON
  logging.
- `config/urls.py`: root HTTP routes, OpenAPI schema, and Swagger UI.
- `config/asgi.py`: HTTP and WebSocket protocol routing with production origin
  validation.
- `config/ws_routing.py`: WebSocket URL patterns.
- `config/celery.py`: Celery application bootstrap.

## Frontend

- `tailwind/tailwind.src.css`: Tailwind v4 input and `ds-*` design tokens and
  components.
- `static/css/tailwind.css`: generated, committed Tailwind output.
- `static/css/`: additional design-system and layout styles.
- `static/js/request-lifecycle.js`: request-lifecycle WebSocket/fetch client.

## Infrastructure

- `Dockerfile`: local development image with locked development dependencies.
- `Dockerfile.prod`: multi-stage runtime image, Tailwind build, and optional
  GeoLite2 database fetch.
- `docker-compose.yml`: local web, PostgreSQL/TimescaleDB, Redis, worker, and
  beat services.
- `docker-compose.prod.yml`: production networks, persistent volumes,
  health checks, and immutable application image selection.
- `nginx/`: TLS proxy, security headers, rate limiting, static/media serving,
  unknown-host rejection, and WebSocket upgrades.
- `deploy.sh`: database startup, TimescaleDB initialization, migration,
  static collection, rollout, health check, and rollback trigger.
- `rollback.sh`: previous-image rollback and health verification.
- `setup_hetzner.sh`: VM bootstrap.
- `.github/workflows/deploy.yml`: quality checks, GHCR image publication,
  SBOM/provenance, and VM deployment.

## Dependency and instruction files

- `pyproject.toml` and `uv.lock`: Python metadata and locked dependencies.
- `package.json` and `package-lock.json`: frontend scripts and locked
  dependencies.
- `.env.example`: documented configuration placeholders.
- `AGENTS.md`: repository-specific development and safety instructions.
