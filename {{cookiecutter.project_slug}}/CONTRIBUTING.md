# Contributing to Login Plans

Thanks for considering a contribution. This is a DDD-strict codebase — the
rules below exist to keep it that way. Read `AGENTS.md` first; it is the
canon of the system.

## Setup

```bash
git clone <repo>
cd {{cookiecutter.project_name}}
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/macOS
```

## The rules that will fail your CI

### Architecture boundaries (enforced by `tests/architecture/`)

- `app/domain/` imports **only** `app.domain.*` — no frameworks, no SQLAlchemy
- `app/application/` imports **only** `app.application` and `app.domain`
- `app/api/` never imports `app.infrastructure` or `app.database`
- `app/infrastructure/` never imports `app.api`

### Invariants

- Credentials and tokens are **never** persisted in plain text — hashes only
- Token comparison uses `secrets.compare_digest`
- Clock is injected — no `datetime.now()` in domain/application
- Domain events go through `unit_of_work.collect_event()` — never call the
  dispatcher directly
- No comments added or removed unless asked

## Workflow

```bash
git checkout -b feature/your-feature

# Make changes, add tests

# Required gates (all must pass):
pytest -q
pytest -n auto -q
mypy app
ruff check .
ruff format --check .

git commit -m "feat: short description"
git push origin feature/your-feature
# Open a Pull Request
```

## Commit conventions

`feat:` / `fix:` / `docs:` / `refactor:` / `test:` — concise, why-focused.

## Testing

- Domain tests: pure, no I/O
- Application tests: fakes for ports
- Infrastructure tests: real test database
- API tests: httpx client via `tests/conftest.py` fixtures
- Tests run against `{{cookiecutter.project_slug}}_test` database (Postgres via docker compose)

## Reporting bugs

Open an issue with: reproduction steps, expected vs actual behavior,
`pytest -q` output, and environment (OS, Python version).

## Questions

Open a GitHub Discussion or an issue labeled `question`.
