# Quickstart Guide: Fellow.app API Backup

**Feature**: 001-fellow-api-backup  
**Date**: 2025-12-24

## Overview

This guide helps you quickly set up and run the Fellow.app backup tool to export your meeting data to MySQL.

---

## Prerequisites

### System Requirements
- Python 3.11 or higher
- MySQL 5.7+ or MySQL 8.0+
- Network access to Fellow.app API
- 500MB+ free disk space (varies with data size)

### Required Information
- Fellow.app API credentials (API key or OAuth token)
- MySQL connection details:
  - Host and port
  - Database name
  - Username and password

---

## Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
# Clone repository (if applicable) or navigate to project directory
cd fellow-backup

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

**requirements.txt contents**:
```
httpx>=0.25.0
mysql-connector-python>=8.2.0
click>=8.1.0
structlog>=23.2.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
httpx-mock>=0.10.0
```

### Step 2: Configure Database

```bash
# Connect to MySQL
mysql -u root -p

# Create database and user
CREATE DATABASE fellow_backup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fellow_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON fellow_backup.* TO 'fellow_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Run schema setup (creates all tables)
mysql -u fellow_user -p fellow_backup < config/database/schema.sql
```

### Step 3: Configure Credentials

Create `.env` file in project root:

```bash
# Fellow.app API Configuration
FELLOW_API_TOKEN=your_api_token_here
FELLOW_API_BASE_URL=https://api.fellow.app  # Optional, defaults to this

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=fellow_backup
MYSQL_USER=fellow_user
MYSQL_PASSWORD=secure_password

# Optional: Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

**Security Note**: Never commit `.env` file to version control. Add to `.gitignore`.

### Step 4: Run Initial Backup

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run full backup
python -m src.cli backup --workspace-id ws_your_workspace_id

# Or let the tool discover workspaces automatically
python -m src.cli backup --all-workspaces
```

---

## Usage Examples

### Basic Backup

```bash
# Backup specific workspace
python -m src.cli backup --workspace-id ws_abc123

# Backup with verbose logging
python -m src.cli backup --workspace-id ws_abc123 --verbose

# Quiet mode (errors only)
python -m src.cli backup --workspace-id ws_abc123 --quiet
```

### Incremental Backup

```bash
# Run incremental backup (only fetch updates since last run)
python -m src.cli backup --workspace-id ws_abc123 --incremental

# Force full backup even if previous sync exists
python -m src.cli backup --workspace-id ws_abc123 --full
```

### List Workspaces

```bash
# Discover available workspaces
python -m src.cli list-workspaces

# Output in JSON format
python -m src.cli list-workspaces --json
```

### Verification

```bash
# Generate summary report of backed-up data
python -m src.cli report --workspace-id ws_abc123

# Verify specific meeting backup
python -m src.cli verify --meeting-id mtg_xyz789
```

---

## Expected Output

### Successful Backup

```
Fellow.app Backup Tool v1.0.0
==============================

Authenticating with Fellow.app API... ✓
Connecting to MySQL database... ✓

Workspace: Engineering Team (ws_abc123)
Fetching meetings... [████████████████████] 100% (247/247)

Processing meetings:
  ├─ Sprint Planning Q1 (mtg_001)... ✓ (8 notes, 3 action items)
  ├─ Weekly Standup 2025-12-23 (mtg_002)... ✓ (5 notes, 1 action item)
  ├─ Architecture Review (mtg_003)... ✓ (12 notes, 7 action items)
  └─ ... (244 more meetings)

Backup Complete! ✓

Summary Report
==============
Duration: 8m 32s
Status: SUCCESS

Statistics:
  - Meetings backed up: 247
  - Notes extracted: 1,842
  - Action items saved: 356
  - Participants recorded: 18

Errors: None

Last sync timestamp saved: 2025-12-24T12:00:00Z
```

### Incremental Backup

```
Fellow.app Backup Tool v1.0.0
==============================

Mode: Incremental (since 2025-12-23T10:00:00Z)

Authenticating with Fellow.app API... ✓
Connecting to MySQL database... ✓

Workspace: Engineering Team (ws_abc123)
Fetching updated meetings... [████████████████████] 100% (5/5)

Processing meetings:
  ├─ Sprint Planning Q1 (mtg_001)... ✓ Updated (2 new notes)
  ├─ Weekly Standup 2025-12-24 (mtg_248)... ✓ New meeting (3 notes)
  └─ ... (3 more meetings)

Backup Complete! ✓

Summary Report
==============
Duration: 1m 15s
Status: SUCCESS

Statistics:
  - Meetings processed: 5 (3 new, 2 updated)
  - Notes extracted: 23 (18 new, 5 updated)
  - Action items saved: 7 (6 new, 1 updated)
  - Participants recorded: 2 (new)

Errors: None

Last sync timestamp updated: 2025-12-24T12:00:00Z
```

---

## Troubleshooting

### Authentication Failed (401 Unauthorized)

**Problem**: Invalid API token

**Solution**:
1. Verify token in `.env` file
2. Check Fellow.app account for valid API keys
3. Ensure token has required permissions (read access to meetings, notes, action items)

```bash
# Test API connection
python -m src.cli test-connection
```

### Database Connection Failed

**Problem**: Cannot connect to MySQL

**Solution**:
1. Verify MySQL is running: `systemctl status mysql` or `brew services list`
2. Check credentials in `.env` file
3. Test connection: `mysql -h localhost -u fellow_user -p fellow_backup`
4. Verify firewall/network settings if using remote database

### Rate Limit Exceeded (429)

**Problem**: Too many API requests

**Solution**: Tool automatically handles rate limiting with exponential backoff. If persistent:
1. Use `--rate-limit` flag to reduce request rate: `python -m src.cli backup --workspace-id ws_abc123 --rate-limit 5`
2. Wait a few minutes before retrying
3. Run backup during off-peak hours

### Incomplete Backup

**Problem**: Backup stops mid-process

**Solution**:
1. Check logs for error details: Look in `logs/` directory or stdout
2. Verify network stability
3. Resume with same command (tool skips already-backed-up items)
4. Use `--verbose` flag for detailed logging

### Special Characters Display Incorrectly

**Problem**: Emojis or non-ASCII characters corrupted

**Solution**:
1. Verify MySQL database uses `utf8mb4` charset: `SHOW CREATE DATABASE fellow_backup;`
2. Verify tables use `utf8mb4_unicode_ci` collation
3. Re-run schema setup if needed

---

## Data Access

### Query Backed-Up Data

```sql
-- List all meetings
SELECT id, title, meeting_date, status
FROM meetings
ORDER BY meeting_date DESC
LIMIT 10;

-- Find meetings with specific keyword in title
SELECT id, title, meeting_date
FROM meetings
WHERE title LIKE '%Sprint%'
ORDER BY meeting_date DESC;

-- Get all notes from a specific meeting
SELECT n.id, n.content, p.name AS author, n.fellow_created_at
FROM notes n
LEFT JOIN participants p ON n.author_id = p.id
WHERE n.meeting_id = 'mtg_xyz789'
ORDER BY n.note_order;

-- Find incomplete action items assigned to someone
SELECT 
    ai.description,
    ai.due_date,
    p.name AS assignee,
    m.title AS meeting
FROM action_items ai
JOIN participants p ON ai.assignee_id = p.id
JOIN meetings m ON ai.meeting_id = m.id
WHERE ai.completed = FALSE
ORDER BY ai.due_date;

-- Count meetings by month
SELECT 
    DATE_FORMAT(meeting_date, '%Y-%m') AS month,
    COUNT(*) AS meeting_count
FROM meetings
GROUP BY month
ORDER BY month DESC;
```

### Export to CSV

```bash
# Export meetings to CSV
mysql -u fellow_user -p fellow_backup -e \
  "SELECT id, title, meeting_date, status FROM meetings" \
  --batch --skip-column-names \
  > meetings_export.csv

# Export action items to CSV
mysql -u fellow_user -p fellow_backup -e \
  "SELECT ai.description, p.name as assignee, ai.due_date, ai.completed 
   FROM action_items ai 
   LEFT JOIN participants p ON ai.assignee_id = p.id" \
  --batch --skip-column-names \
  > action_items_export.csv
```

---

## Scheduling Automatic Backups

### Using Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/fellow-backup && source venv/bin/activate && python -m src.cli backup --workspace-id ws_abc123 --incremental >> /var/log/fellow-backup.log 2>&1

# Add weekly full backup on Sundays at 3 AM
0 3 * * 0 cd /path/to/fellow-backup && source venv/bin/activate && python -m src.cli backup --workspace-id ws_abc123 --full >> /var/log/fellow-backup.log 2>&1
```

### Using systemd Timer (Linux)

Create `/etc/systemd/system/fellow-backup.service`:
```ini
[Unit]
Description=Fellow.app Backup Service

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/fellow-backup
ExecStart=/path/to/fellow-backup/venv/bin/python -m src.cli backup --workspace-id ws_abc123 --incremental
```

Create `/etc/systemd/system/fellow-backup.timer`:
```ini
[Unit]
Description=Fellow.app Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fellow-backup.timer
sudo systemctl start fellow-backup.timer
```

### Using Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task: "Fellow Backup"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
   - Program: `C:\path\to\fellow-backup\venv\Scripts\python.exe`
   - Arguments: `-m src.cli backup --workspace-id ws_abc123 --incremental`
   - Start in: `C:\path\to\fellow-backup`

---

## Best Practices

### Before Discontinuing Fellow.app

1. **Run full backup**: Ensure all data captured before access is lost
   ```bash
   python -m src.cli backup --all-workspaces --full
   ```

2. **Verify backup**: Check record counts match Fellow.app dashboard
   ```bash
   python -m src.cli report --workspace-id ws_abc123 --verify
   ```

3. **Export to files**: Create CSV/JSON exports as additional backup
   ```bash
   python -m src.cli export --workspace-id ws_abc123 --format json --output fellow_export.json
   ```

4. **Document access**: Save database connection details and schema documentation

### Ongoing Usage

1. **Run incremental backups**: Daily or weekly to keep data current
2. **Monitor logs**: Check for API errors or failed items
3. **Test restore**: Periodically verify you can query backed-up data
4. **Keep credentials secure**: Rotate API tokens periodically
5. **Backup the backup**: Export MySQL database dumps regularly
   ```bash
   mysqldump -u fellow_user -p fellow_backup > fellow_backup_$(date +%Y%m%d).sql
   ```

---

## Performance Tips

### Large Workspaces (1000+ meetings)

- **Increase page size**: Use `--page-size 100` to reduce API calls
- **Parallel processing**: Use `--workers 5` to process meetings concurrently (if supported)
- **Run during off-hours**: Minimize network latency and API contention
- **Use incremental mode**: Significantly faster for subsequent backups

### Database Optimization

```sql
-- Add custom indexes for frequent queries
CREATE INDEX idx_meeting_title ON meetings(title(100));
CREATE INDEX idx_note_content ON notes(content(100));
CREATE INDEX idx_action_description ON action_items(description(100));

-- Analyze tables for query optimization
ANALYZE TABLE meetings, notes, action_items, participants;
```

---

## Getting Help

### Check Logs

```bash
# View recent logs
tail -f logs/fellow-backup.log

# Search for errors
grep ERROR logs/fellow-backup.log
```

### Verbose Mode

```bash
# Enable detailed logging
python -m src.cli backup --workspace-id ws_abc123 --verbose
```

### Test Mode

```bash
# Dry run (no database writes)
python -m src.cli backup --workspace-id ws_abc123 --dry-run
```

---

## Next Steps

- Review `data-model.md` for database schema details
- Read `contracts/fellow-api.md` for API integration details
- Check `plan.md` for implementation roadmap
- Run tests: `pytest tests/` to verify installation

**Ready to start?** Run your first backup:
```bash
python -m src.cli backup --workspace-id ws_abc123
```
