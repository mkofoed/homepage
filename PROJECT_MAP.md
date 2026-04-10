# PROJECT MAP — Homepage Repo

Root: `C:\Users\Mikke\Code\homepage`

## Apps

### blog/
- `models.py` — Blog post model
- `views.py` — Blog views
- `urls.py` — Blog URL routes
- `admin.py` — Blog admin config
- `templates/blog/index.html` — Blog index page
- `templates/blog/detail.html` — Blog post detail
- `templates/blog/post_list.html` — Post list page
- `templates/blog/partials/post_list_items.html` — HTMX post list partial
- `templatetags/markdown_extras.py` — Custom template tags
- `management/commands/populate_blog.py` — Blog data seeder

### core/
- `views.py` — Homepage, about, architecture, dashboard views
- `urls.py` — Core URL routes
- `models.py` — Core models
- `context_processors.py` — Template context processors
- `services/github_service.py` — GitHub API service
- `services/system_metrics.py` — System metrics service
- `templates/base.html` — **ROOT BASE TEMPLATE** (all pages extend this)
- `templates/core/base.html` — Core base template
- `templates/core/home.html` — Homepage
- `templates/core/about.html` — About page
- `templates/core/architecture.html` — Architecture page
- `templates/core/dashboard.html` — Core dashboard
- `templates/core/partials/github_stats.html` — GitHub stats partial
- `templates/registration/login.html` — Login page
- `templates/registration/logged_out.html` — Logout page

### dashboard/
- `models.py` — SpotPrice model (TimescaleDB hypertable)
- `views.py` — Dashboard views (energy price dashboard)
- `urls.py` — Dashboard URL routes
- `tasks.py` — Celery tasks
- `services/energinet.py` — Energinet API service
- `services/current_price.py` — Current price service
- `services/price_chart.py` — Price chart service
- `templates/dashboard/index.html` — Dashboard page
- `templates/dashboard/partials/chart_data.html` — Chart data HTMX partial
- `templates/dashboard/partials/hero_card.html` — Hero card HTMX partial
- `management/commands/poll_spot_prices.py` — Celery beat price poller
- `management/commands/backfill_prices.py` — Price backfill command
- `management/commands/backfill_spot_prices.py` — Spot price backfill

### showcase/
- `views.py` — API showcase views
- `urls.py` — Showcase URL routes
- `services/algorithms.py` — Algorithm showcase service
- `services/content.py` — Content service

### visitors/
- `models.py` — Visitor tracking model
- `middleware.py` — Visitor tracking middleware
- `tasks.py` — Visitor processing Celery tasks
- `services/geoip.py` — GeoIP lookup service

## Config
- `config/settings/base.py` — Base Django settings
- `config/settings/development.py` — Dev settings
- `config/settings/production.py` — Prod settings
- `config/urls.py` — Root URL config
- `config/celery.py` — Celery config

## Infrastructure
- `Dockerfile` — Dev Docker image
- `Dockerfile.prod` — Production Docker image
- `docker-compose.yml` — Dev compose
- `docker-compose.prod.yml` — Prod compose
- `nginx/homepage.conf` — Nginx config
- `nginx/rate-limit.conf` — Nginx rate limiting
- `deploy.sh` — Deployment script
- `setup_hetzner.sh` — Server setup script
- `.github/workflows/deploy.yml` — CI/CD deploy workflow
- `.github/workflows/lint.yml` — CI lint workflow

## Static
- `static/css/variables.css` — CSS variables/tokens
- `static/css/design-system.css` — Design system
- `static/css/base.css` — Base styles
- `static/css/layout.css` — Layout styles
- `static/css/components.css` — Component styles
- `static/css/animations.css` — Animations
- `static/css/style.css` — Main stylesheet

## Key Files
- `pyproject.toml` — Project config, dependencies
- `AGENTS.md` — Coding conventions (READ THIS)
- `manage.py` — Django management
- `.env` — Environment variables
- `.env.example` — Env template
