# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python CLI tool for importing historic knowledge data into a MySQL database. Currently supports Fellow.app as a data source, with the infrastructure designed to support additional sources (e.g., Confluence). Fellow data is fetched via the Fellow.app API (POST /api/v1/notes) and stored in MySQL with upsert semantics. Supports full and incremental backups using cursor-based pagination.

## Commands

```bash
# Setup
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the CLI
python -m src.cli.main backup --full       # Full backup
python -m src.cli.main backup              # Incremental (since last run)
python -m src.cli.main backup --dry-run    # Preview without DB writes
python -m src.cli.main report              # Show backup statistics
python -m src.cli.main test-connection     # Verify API + DB connectivity

# Tests
pytest                                     # All tests
pytest tests/unit/test_models.py           # Single file
pytest --cov=src --cov-report=html         # With coverage
```

## Architecture

The app follows a three-layer pattern: **CLI -> Services -> Data**

- **CLI** (`src/cli/main.py`): Click-based entry point. All commands go through here. Run via `python -m src.cli.main`.
- **Services**: Business logic layer.
  - `fellow_api.py`: HTTP client using httpx. Authenticates via `X-API-KEY` header. Uses POST (not GET) for `/api/v1/notes`. Has built-in rate limiting and 429 retry.
  - `database.py`: MySQL operations via mysql-connector-python. Uses `transaction()` context manager for all DB work. Upserts notes via `INSERT ... ON DUPLICATE KEY UPDATE`.
  - `backup.py`: Orchestrates fetch-then-save. Handles pagination, incremental timestamp detection, and produces `BackupReport` dataclass with statistics.
- **Models** (`src/models/__init__.py`): Single `Note` dataclass with embedded author fields (no separate author table). Event attendees stored as email list in the model, normalized to `fellow_event_attendees` table in MySQL.
- **Lib** (`src/lib/`): Rate limiter, retry logic, structured logging via structlog.

## Key Design Decisions

- **Table namespacing**: All Fellow-specific tables are prefixed with `fellow_` (`fellow_notes`, `fellow_event_attendees`, `fellow_backup_metadata`, `fellow_client_domains`) to support multiple data sources in the same database.
- **Notes-only schema**: No workspaces, meetings, or participants tables. Notes are standalone with embedded author info (`author_name`, `author_id` columns).
- **Incremental backup**: Uses `MAX(fellow_updated_at)` from the `fellow_notes` table as the watermark — no separate sync cursor.
- **All config via environment**: `.env` file loaded by python-dotenv. Required vars: `FELLOW_API_TOKEN`, `FELLOW_SUBDOMAIN`, `MYSQL_HOST`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`.
- **API uses POST for reads**: Fellow.app's notes endpoint is `POST /api/v1/notes` with a JSON body containing pagination and filters.

## Testing

Tests are split into `tests/unit/`, `tests/integration/`, and `tests/contract/`. The conftest.py fixtures reference old models (Workspace, Meeting, etc.) that no longer exist in the codebase — they need updating if used. Integration tests require a running MySQL instance and valid API credentials.
