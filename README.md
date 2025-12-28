# Fellow.app Notes Backup Tool

A Python CLI tool to backup all notes from Fellow.app to a MySQL database.

## Features

- **Notes-Only Export**: Extract all notes with complete metadata (author info, timestamps)
- **Incremental Updates**: Efficiently sync only changed notes based on `fellow_updated_at`
- **Verification Reporting**: Summary reports after each backup with counts and errors
- **Rate Limiting**: Respects API limits with automatic retry logic and exponential backoff
- **Progress Tracking**: Real-time progress indicators and structured logging
- **Standalone Storage**: Notes stored independently without foreign key dependencies

## Quick Start

### Prerequisites

- Python 3.11 or higher
- MySQL 5.7+ or MySQL 8.0+
- Fellow.app API token

### Installation

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```
   FELLOW_API_TOKEN=your_api_token_here
   FELLOW_API_BASE_URL=https://api.fellow.app
   MYSQL_HOST=localhost
   MYSQL_DATABASE=fellow_backup
   MYSQL_USER=backup_user
   MYSQL_PASSWORD=your_password
   ```

3. Set up MySQL database:
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE fellow_backup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
   
   # Run schema setup
   mysql -u backup_user -p fellow_backup < config/database/schema.sql
   ```

### Usage

```bash
# Full backup (first run)
python -m src.cli.main backup --full

# Incremental backup (only changes since last run)
python -m src.cli.main backup

# Dry run (preview without database changes)
python -m src.cli.main backup --dry-run

# JSON output (for scripting)
python -m src.cli.main backup --json

# Generate backup report
python -m src.cli.main report

# Test connections
python -m src.cli.main test-connection
```

## Documentation

- See [specs/002-notes-only-backup/quickstart.md](specs/002-notes-only-backup/quickstart.md) for detailed usage
- See [specs/002-notes-only-backup/](specs/002-notes-only-backup/) for complete design documents

## Project Structure

```
src/
├── models/          # Data models (Note)
├── services/        # Business logic
│   ├── fellow_api.py    # Fellow.app API client (POST /api/v1/notes)
│   ├── database.py      # MySQL database service
│   └── backup.py        # Notes backup orchestration
├── cli/             # CLI interface
│   └── main.py          # Entry point
└── lib/             # Utilities
    ├── logger.py        # Structured logging
    ├── rate_limiter.py  # Rate limiting
    └── retry.py         # Retry logic

config/
└── database/
    └── schema.sql       # MySQL schema (notes + backup_metadata tables)

tests/
├── contract/        # API contract tests
├── integration/     # Integration tests
└── unit/           # Unit tests
```

## Database Schema

The simplified schema stores notes independently:

- **notes** table: Standalone note records with embedded author information
- **backup_metadata** table: Tracks last backup timestamp and summary statistics

No foreign keys or complex relationships - just notes with complete metadata.

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py
```

## License

See LICENSE file for details.
