# Fellow.app API Backup - Detailed Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Guide](#setup-guide)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

## Overview

The Fellow.app API Backup tool is a Python CLI application that exports all meeting data from Fellow.app to a MySQL database. It supports:

- **Full Backups**: Complete data extraction
- **Incremental Updates**: Only sync changed data
- **Verification Reporting**: Detailed summary after each backup
- **Rate Limiting**: Automatic API throttling
- **Error Recovery**: Continues processing on partial failures

## Architecture

### Components

```
┌─────────────┐
│ CLI Layer   │ - Command-line interface (Click)
└──────┬──────┘
       │
┌──────▼──────┐
│ Services    │ - Backup orchestration
│             │ - API client (httpx)
│             │ - Database operations (MySQL)
└──────┬──────┘
       │
┌──────▼──────┐
│ Models      │ - Data structures (dataclasses)
└─────────────┘
┌─────────────┐
│ Utilities   │ - Logging (structlog)
│             │ - Rate limiting
│             │ - Retry logic
└─────────────┘
```

### Data Flow

1. **CLI** receives user command
2. **API Client** fetches data from Fellow.app with rate limiting
3. **Backup Service** orchestrates the workflow
4. **Database Service** stores data in MySQL with transactions
5. **Report** generated and displayed to user

## Setup Guide

### Prerequisites

- Python 3.11 or higher
- MySQL 5.7+ or 8.0+
- Fellow.app API credentials
- 500MB+ free disk space

### Step 1: Environment Setup

```bash
# Clone or extract project
cd cursor-fellow-export

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

```bash
# Connect to MySQL as root
mysql -u root -p

# Create database
CREATE DATABASE fellow_backup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user
CREATE USER 'fellow_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON fellow_backup.* TO 'fellow_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Import schema
mysql -u fellow_user -p fellow_backup < config/database/schema.sql
```

### Step 3: Configuration

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env`:

```
# Fellow.app API
FELLOW_API_TOKEN=your_api_token_here
FELLOW_API_BASE_URL=https://api.fellow.app

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=fellow_backup
MYSQL_USER=fellow_user
MYSQL_PASSWORD=your_secure_password

# Logging
LOG_LEVEL=INFO
```

### Step 4: Test Connection

```bash
python -m src.cli test-connection
```

## Usage

### Basic Commands

#### List Workspaces

```bash
# Human-readable format
python -m src.cli list-workspaces

# JSON format
python -m src.cli list-workspaces --json
```

#### Backup Single Workspace

```bash
# Full backup
python -m src.cli backup --workspace-id ws_abc123

# Incremental backup
python -m src.cli backup --workspace-id ws_abc123 --incremental

# Dry run (preview without changes)
python -m src.cli backup --workspace-id ws_abc123 --dry-run
```

#### Backup All Workspaces

```bash
python -m src.cli backup --all-workspaces
```

#### Generate Report

```bash
# Human-readable
python -m src.cli report --workspace-id ws_abc123

# JSON format
python -m src.cli report --workspace-id ws_abc123 --json
```

#### Verify Meeting

```bash
python -m src.cli verify --meeting-id mtg_xyz789
```

### Advanced Options

#### Logging Levels

```bash
# Verbose (DEBUG)
python -m src.cli backup --workspace-id ws_abc123 --verbose

# Quiet (ERROR only)
python -m src.cli backup --workspace-id ws_abc123 --quiet
```

#### Force Full Backup

```bash
# Override incremental mode
python -m src.cli backup --workspace-id ws_abc123 --full
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FELLOW_API_TOKEN` | Yes | - | API authentication token |
| `FELLOW_API_BASE_URL` | No | `https://api.fellow.app` | API base URL |
| `MYSQL_HOST` | No | `localhost` | MySQL server host |
| `MYSQL_PORT` | No | `3306` | MySQL server port |
| `MYSQL_DATABASE` | No | `fellow_backup` | Database name |
| `MYSQL_USER` | No | `fellow_user` | Database user |
| `MYSQL_PASSWORD` | Yes | - | Database password |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Rate Limiting

Default: 10 requests/second

The tool automatically handles API rate limits with exponential backoff. If you encounter 429 errors, the tool will:

1. Wait for the `Retry-After` period
2. Use exponential backoff (2s, 4s, 8s, 16s, 32s, max 60s)
3. Retry up to 5 times

## Troubleshooting

### Authentication Errors (401)

**Problem**: Invalid API token

**Solution**:
1. Verify `FELLOW_API_TOKEN` in `.env`
2. Check token hasn't expired
3. Ensure token has read permissions

### Database Connection Errors

**Problem**: Cannot connect to MySQL

**Solutions**:
1. Verify MySQL is running: `systemctl status mysql`
2. Test connection: `mysql -h localhost -u fellow_user -p`
3. Check firewall rules
4. Verify credentials in `.env`

### Rate Limit Errors (429)

**Problem**: Too many API requests

**Solution**: Tool handles automatically, but you can:
- Run during off-peak hours
- Wait before retrying
- Contact Fellow.app support for increased limits

### Incomplete Backups

**Problem**: Backup stops mid-process

**Solutions**:
1. Check logs for specific errors
2. Verify network stability
3. Re-run with same command (skips completed items)
4. Use `--verbose` for detailed logging

### Character Encoding Issues

**Problem**: Special characters corrupted

**Solutions**:
1. Verify database charset: `SHOW CREATE DATABASE fellow_backup;`
2. Should be `utf8mb4` with `utf8mb4_unicode_ci`
3. Re-run schema setup if needed

## API Reference

### Database Schema

See `config/database/schema.sql` for complete schema.

**Tables**:
- `workspaces` - Workspace records
- `meetings` - Meeting metadata
- `participants` - User/participant records
- `meeting_participants` - Meeting-participant relationships
- `notes` - Meeting notes content
- `action_items` - Meeting action items
- `backup_metadata` - Sync state tracking

### Data Models

See `src/models/__init__.py` for model definitions.

### Services

#### FellowAPIClient

```python
from src.services.fellow_api import FellowAPIClient

client = FellowAPIClient(rate_limit=10.0)
workspaces = client.list_workspaces()
meetings = client.list_meetings(workspace_id)
notes = client.list_notes(meeting_id)
action_items = client.list_action_items(meeting_id)
```

#### DatabaseService

```python
from src.services.database import DatabaseService

db = DatabaseService()
db.connect()
db.save_workspace(workspace)
db.save_meeting(meeting)
db.disconnect()
```

#### BackupService

```python
from src.services.backup import BackupService

backup = BackupService(api_client, db_service)
report = backup.backup_workspace(workspace_id, incremental=True)
print(report.format_summary())
```

## Best Practices

### Before Discontinuing Fellow.app

1. Run full backup of all workspaces
2. Verify backup completeness
3. Export to CSV/JSON as additional backup
4. Document database access details

### Ongoing Maintenance

1. Schedule regular incremental backups (daily/weekly)
2. Monitor logs for errors
3. Test data access periodically
4. Backup MySQL database regularly
5. Rotate API tokens periodically

### Performance Tips

- Use `--incremental` for regular backups (much faster)
- Run during off-peak hours for large datasets
- Use `--dry-run` to preview operations
- Monitor database disk space

## Support

For issues or questions:

1. Check logs: `logs/fellow-backup.log`
2. Review error messages with `--verbose`
3. Verify configuration with `test-connection`
4. Consult specification docs in `specs/001-fellow-api-backup/`

## License

See LICENSE file for details.
