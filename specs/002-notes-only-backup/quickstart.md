# Quickstart: Fellow.app Notes-Only Backup

**Feature**: Notes-Only Backup  
**Branch**: `002-notes-only-backup`  
**Date**: 2025-12-28

## Overview

This guide provides step-by-step instructions for setting up and running the simplified Fellow.app notes-only backup tool.

## Prerequisites

- **Python**: 3.11 or higher (tested with 3.13.7)
- **MySQL**: 5.7+ or 8.0+
- **Fellow.app API Token**: Obtain from Fellow.app account settings
- **Operating System**: Linux, macOS, or Windows

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd cursor-fellow-export
git checkout 002-notes-only-backup
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies**:
- httpx (async HTTP client)
- mysql-connector-python (MySQL driver)
- click (CLI framework)
- structlog (structured logging)
- python-dotenv (environment configuration)

### 4. Configure Environment

Create `.env` file in project root:

```bash
# Fellow.app API Configuration
FELLOW_API_TOKEN=your_api_token_here
FELLOW_API_BASE_URL=https://api.fellow.app

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fellow_backup
DB_USER=backup_user
DB_PASSWORD=your_secure_password

# Optional: Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/backup.log
```

**Security Notes**:
- Never commit `.env` file to version control
- Use strong database passwords
- Rotate API tokens regularly
- Consider using encrypted configuration for production

### 5. Set Up Database

**Create Database**:

```sql
CREATE DATABASE fellow_backup
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

**Create Database User** (optional but recommended):

```sql
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT SELECT, INSERT, UPDATE ON fellow_backup.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;
```

**Initialize Schema**:

```bash
mysql -h localhost -u backup_user -p fellow_backup < config/database/schema.sql
```

**Verify Tables Created**:

```sql
USE fellow_backup;
SHOW TABLES;
-- Expected: notes, backup_metadata
```

## Usage

### Basic Commands

**Full Backup** (first run or complete refresh):

```bash
python -m src.cli.main backup --full
```

**Incremental Backup** (only updated notes):

```bash
python -m src.cli.main backup
```

**Dry Run** (preview without writing to database):

```bash
python -m src.cli.main backup --dry-run
```

**Verbose Logging**:

```bash
python -m src.cli.main backup --verbose
```

**Quiet Mode** (errors only):

```bash
python -m src.cli.main backup --quiet
```

**JSON Output** (for scripting):

```bash
python -m src.cli.main backup --json > backup-summary.json
```

### Command Options

```
Usage: python -m src.cli.main backup [OPTIONS]

  Backup notes from Fellow.app to MySQL database.

Options:
  --full              Force full backup (ignore incremental timestamps)
  --dry-run           Preview changes without writing to database
  --verbose           Enable detailed debug logging
  --quiet             Suppress progress output (errors only)
  --json              Output summary report in JSON format
  --help              Show this message and exit
```

## Workflow Examples

### Initial Setup and First Backup

```bash
# 1. Verify configuration
cat .env | grep -v PASSWORD

# 2. Test database connection
mysql -h localhost -u backup_user -p -e "SELECT 1"

# 3. Run dry-run to verify API access
python -m src.cli.main backup --dry-run

# 4. Execute full backup
python -m src.cli.main backup --full --verbose

# 5. Verify data in database
mysql -h localhost -u backup_user -p fellow_backup \
  -e "SELECT COUNT(*) as total_notes FROM notes"
```

**Expected Output**:
```
[INFO] Starting Fellow.app notes backup
[INFO] Authenticating with Fellow.app API
[INFO] Fetching notes (page 1/13)
[INFO] Processing 100 notes...
[INFO] Fetching notes (page 2/13)
...
[INFO] Backup completed successfully
[INFO] Summary: 1234 total notes, 1234 new, 0 updated, 0 errors
[INFO] Duration: 2m 34s
```

### Daily Incremental Backup

```bash
# Run as cron job or scheduled task
python -m src.cli.main backup

# With error logging to file
python -m src.cli.main backup 2>> logs/backup-errors.log
```

**Expected Output**:
```
[INFO] Starting Fellow.app notes backup (incremental)
[INFO] Last backup: 2025-12-27T09:00:00Z
[INFO] Fetching notes updated after 2025-12-27T09:00:00Z
[INFO] Fetching notes (page 1/1)
[INFO] Processing 23 notes...
[INFO] Backup completed successfully
[INFO] Summary: 23 total notes, 5 new, 18 updated, 0 errors
[INFO] Duration: 8s
```

### Automated Backup Script

Create `scripts/daily-backup.sh`:

```bash
#!/bin/bash
set -e

# Load environment
cd /path/to/cursor-fellow-export
source .venv/bin/activate

# Run backup with logging
python -m src.cli.main backup \
  --json \
  > logs/backup-$(date +%Y%m%d-%H%M%S).json \
  2>> logs/backup-errors.log

# Check exit code
if [ $? -eq 0 ]; then
  echo "Backup succeeded at $(date)"
else
  echo "Backup failed at $(date)" >&2
  exit 1
fi
```

**Make executable and schedule**:

```bash
chmod +x scripts/daily-backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line: 0 2 * * * /path/to/scripts/daily-backup.sh
```

## Querying Backed-Up Data

### Common Queries

**Get all notes by author**:

```sql
SELECT id, LEFT(content, 100) as preview, fellow_created_at
FROM notes
WHERE author_name = 'John Doe'
ORDER BY fellow_created_at DESC
LIMIT 20;
```

**Search note content**:

```sql
SELECT id, author_name, LEFT(content, 100) as preview
FROM notes
WHERE content LIKE '%project alpha%'
ORDER BY fellow_updated_at DESC;
```

**Get summary statistics**:

```sql
SELECT 
  COUNT(*) as total_notes,
  COUNT(DISTINCT author_id) as unique_authors,
  MIN(fellow_created_at) as earliest_note,
  MAX(fellow_updated_at) as latest_update,
  AVG(LENGTH(content)) as avg_content_length
FROM notes;
```

**Notes updated in last 7 days**:

```sql
SELECT author_name, COUNT(*) as notes_updated
FROM notes
WHERE fellow_updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY author_name
ORDER BY notes_updated DESC;
```

### Exporting Data

**Export to CSV**:

```bash
mysql -h localhost -u backup_user -p fellow_backup \
  -e "SELECT * FROM notes" \
  | sed 's/\t/","/g;s/^/"/;s/$/"/;s/\n//g' \
  > notes-export.csv
```

**Export to JSON** (using Python):

```python
import mysql.connector
import json

conn = mysql.connector.connect(
    host='localhost',
    database='fellow_backup',
    user='backup_user',
    password='your_password'
)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM notes")

with open('notes-export.json', 'w', encoding='utf-8') as f:
    json.dump(cursor.fetchall(), f, indent=2, default=str)

cursor.close()
conn.close()
```

## Troubleshooting

### API Authentication Errors

**Error**: `401 Unauthorized - Invalid or expired API token`

**Solutions**:
1. Verify `FELLOW_API_TOKEN` in `.env` is correct
2. Check token hasn't expired in Fellow.app
3. Regenerate token in Fellow.app account settings

### Database Connection Errors

**Error**: `Can't connect to MySQL server on 'localhost'`

**Solutions**:
1. Verify MySQL is running: `systemctl status mysql` (Linux) or `brew services list` (macOS)
2. Check DB_HOST, DB_PORT in `.env`
3. Test connection: `mysql -h localhost -u backup_user -p`
4. Verify user has correct permissions

### Rate Limiting

**Error**: `429 Rate Limit Exceeded`

**Solutions**:
1. Wait for retry_after duration (shown in error message)
2. Backup will automatically retry with exponential backoff
3. If persistent, contact Fellow.app support to increase limits

### UTF-8 Encoding Issues

**Error**: Content appears garbled or contains `?` characters

**Solutions**:
1. Verify database uses utf8mb4: `SHOW CREATE TABLE notes;`
2. Check MySQL connection uses utf8mb4: add `charset=utf8mb4` to connection
3. Re-create database with correct character set

### Large Content Issues

**Error**: Content truncated or `Data too long for column` error

**Solutions**:
1. Verify note content size: `SELECT id, LENGTH(content) FROM notes ORDER BY LENGTH(content) DESC LIMIT 10;`
2. If >65KB, migrate column to MEDIUMTEXT: `ALTER TABLE notes MODIFY content MEDIUMTEXT;`

### Performance Issues

**Symptom**: Backup takes longer than expected

**Solutions**:
1. Check database indexes: `SHOW INDEX FROM notes;`
2. Verify network latency to Fellow.app API
3. Enable verbose logging to identify bottleneck: `--verbose`
4. Consider running during off-peak hours

## Monitoring and Maintenance

### Check Last Backup Status

```sql
SELECT key_name, value, updated_at
FROM backup_metadata
WHERE key_name IN ('last_backup_timestamp', 'last_backup_summary');
```

### Monitor Database Growth

```sql
SELECT 
  COUNT(*) as total_notes,
  ROUND(SUM(LENGTH(content)) / 1024 / 1024, 2) as content_mb,
  DATE(MAX(fellow_updated_at)) as latest_note_date
FROM notes;
```

### Verify Data Integrity

```bash
# Sample audit: compare count in database vs API
python -m src.cli.main backup --dry-run --json | jq '.pagination.total_count'
mysql -h localhost -u backup_user -p fellow_backup -e "SELECT COUNT(*) FROM notes"
```

### Backup Database

```bash
# Dump database to SQL file
mysqldump -h localhost -u backup_user -p fellow_backup > backups/fellow-backup-$(date +%Y%m%d).sql

# Compress
gzip backups/fellow-backup-$(date +%Y%m%d).sql
```

## Next Steps

After successful setup:

1. **Schedule automated backups**: Set up cron job or scheduled task
2. **Monitor backup logs**: Review logs regularly for errors
3. **Test restoration**: Practice querying and exporting data
4. **Document custom queries**: Save frequently-used queries
5. **Set up alerts**: Configure notifications for backup failures

## Support

- **Repository Issues**: Report bugs or feature requests on GitHub
- **Documentation**: See `docs/` directory for detailed guides
- **Logs**: Check `logs/backup.log` for detailed error information

## Related Documentation

- [Data Model](./data-model.md) - Database schema and entity definitions
- [API Contracts](./contracts/fellow-api.md) - Fellow.app API specifications
- [Implementation Plan](./plan.md) - Technical architecture and design
