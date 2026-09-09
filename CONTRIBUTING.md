# Contributing

This is a personal project, but the workflow is written down so that a change
made six months from now still lands the same way.

## Ground rules

- Work on a branch and open a pull request. `main` deploys to production on
  every push, so a commit straight to `main` is a deploy.
- Run the quality gate locally before pushing. CI runs the same checks, but
  finding a failure locally is minutes rather than a round trip.
- Add a regression test with any behaviour change.
- Update `AGENTS.md`, `PROJECT_MAP.md`, and `README.md` when commands,
  architecture, environment variables, or user-visible behaviour change.

## Python version

The codebase requires **Python 3.14** and is not merely tested on it. Several
modules use PEP 758 syntax (unparenthesised multiple exception types, as in
`except ValueError, AttributeError:`), which is a `SyntaxError` on 3.13 and
earlier. `requires-python`, the Dockerfiles, `.python-version`, the Ruff
`target-version`, and the CI matrix all say 3.14 and must move together.

## Setup

```bash
cp .env.example .env
docker compose up --build          # http://localhost:8000
npm ci                             # frontend toolchain
uv sync --locked --extra dev       # host-side tooling, for pre-commit
uv run pre-commit install          # hooks: ruff, djlint, hygiene, shellcheck
```

## The quality gate

Run Python commands in the `web` container, and always set `UV_CACHE_DIR` —
the development container user has no writable home directory.

```bash
alias dcw='docker compose exec -T -e UV_CACHE_DIR=/tmp/uv-cache web uv run'

dcw ruff check .
dcw ruff format --check .
dcw djlint core/templates blog/templates dashboard/templates --lint
dcw mypy .
dcw python manage.py check --settings=config.settings.test
dcw python manage.py check --deploy --settings=config.settings.production
dcw python manage.py test --settings=config.settings.test

npm run build:css && git diff --stat -- static/css/tailwind.css   # must be empty
```

All of these must be clean. During development the narrowest test label is
fine for fast feedback:

```bash
dcw python manage.py test dashboard.tests.GridTariffTests --settings=config.settings.test
```

Coverage, when you want it:

```bash
dcw coverage run manage.py test --settings=config.settings.test && dcw coverage report
```

## What the test settings do and do not cover

`config/settings/test.py` uses in-memory SQLite, disables app migrations, and
swaps Redis and Channels for in-memory backends. That makes the suite fast and
hermetic, but it does **not** exercise TimescaleDB hypertable SQL, continuous
aggregates, production proxy behaviour, or the deployment configuration.
Changes in those areas need validation against real PostgreSQL with TimescaleDB.

## Commit and PR conventions

- Conventional-commit prefixes: `feat:`, `fix:`, `docs:`, `ci:`, `deps:`,
  `refactor:`, `test:`, `chore:`.
- Keep a pull request to one concern. Say what changed and why, and name
  anything you deliberately did not do.
- Never commit `.env`, credentials, certificates, database dumps, or
  `node_modules`.

## Branch protection

`main` deploys on push, so the protection rule is what stops an accidental
direct push from becoming a deploy. Apply it once, authenticated as a repo
admin (`gh auth login`):

```bash
./scripts/setup-branch-protection.sh
```

The script is idempotent and prints the resulting rule. It is the source of
truth for what `main` requires — change the rule there, not in the web UI, so
the two cannot drift.

Two deliberate choices for a solo repository:

- `required_approving_review_count: 0` forces the pull-request flow without
  requiring an approval you cannot give yourself.
- `enforce_admins: false` leaves you an override for a genuine emergency. Set
  it to `true` in the script if you would rather not have that escape hatch.

The three required contexts are the `name:` values of the jobs in `ci.yml`.
Rename a job and the rule silently stops requiring it, so change both together.

If you would rather use the UI: **Settings → Branches → Add branch protection
rule**, branch name pattern `main`, then tick *Require a pull request before
merging* (0 approvals) and *Require status checks to pass before merging* →
*Require branches to be up to date*, and add the three checks. They only
appear in that search once they have run at least once, so open a throwaway
pull request first if the list is empty.
