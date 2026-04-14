# Repository Guidelines

## Project Structure & Module Organization
`config/` contains Django project settings, URL routing, and ASGI/WSGI entrypoints. `analyzer/` is the main app for models, serializers, views, admin wiring, migrations, and service-layer orchestration in `analyzer/services/`. `legacy_core/` holds the original Jira analysis pipeline and utility modules reused by the web layer. Templates live in `templates/`, MySQL bootstrap SQL lives in `sql/`, and runtime outputs such as generated images or logs are written under `comment/`.

## Build, Test, and Development Commands
Create an environment and install dependencies with `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Run migrations with `python manage.py migrate` or `python manage.py migrate --fake-initial` after loading `sql/init_mysql.sql` into an existing MySQL database. Start the dev server with `python manage.py runserver 0.0.0.0:8000`. Use `bash init_mysql_tables.sh` to initialize the default MySQL schema, or set `DB_ENGINE=sqlite3` for local SQLite fallback.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and descriptive snake_case for functions, variables, and module names. Keep Django models singular and class-based views/serializers in PascalCase. Put HTTP orchestration in `analyzer/views.py` and heavier business logic in `analyzer/services/` or `legacy_core/`, not inline in views. No formatter or linter config is checked in, so keep imports tidy and prefer small, focused functions.

## Testing Guidelines
There is no committed `tests/` package yet; add Django tests close to the app they cover, for example `analyzer/tests/test_views.py`. Use `python manage.py test` as the default test command. For database-facing changes, cover both migration behavior and API flow, especially task creation, result retrieval, and Jira comment backfill paths.

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so use short imperative commit subjects such as `Add result comment retry handling`. Keep commits scoped to one change. PRs should describe the user-visible impact, list config or schema changes, and include example API requests or screenshots when `templates/index.html` or response payloads change.

## Security & Configuration Tips
Do not commit real Jira credentials or production `config.yaml` values. Prefer environment variables for `MYSQL_*`, `DJANGO_SECRET_KEY`, and debug settings. Treat `comment/` as generated output and review it before sharing because it may contain issue data or exported images.
