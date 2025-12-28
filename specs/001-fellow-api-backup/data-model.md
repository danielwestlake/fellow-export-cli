# Data Model: Fellow.app Notes-Only Backup

**Feature**: 001-fellow-api-backup  
**Date**: 2025-12-28

## Overview

This document defines the simplified data model for backing up only notes from Fellow.app to MySQL. The model preserves note content, author information, and timestamps with a single-table design.

---

## Entity Definitions

### Note

Content from Fellow.app including text, author, and metadata.

**Attributes**:
- `id` (string, PK): Unique identifier from Fellow.app
- `content` (text, required): Note text content
- `author_name` (string, nullable): Name of note author
- `author_id` (string, nullable): Author's user ID from Fellow.app
- `fellow_created_at` (datetime, nullable): Original creation time in Fellow.app
- `fellow_updated_at` (datetime, nullable): Last update time in Fellow.app
- `created_at` (datetime, required): Backup system record creation time
- `updated_at` (datetime, required): Backup system record update time

**Validation Rules**:
- `id` must be unique and non-empty
- `content` must be non-empty (TEXT type for large content)
- `author_name` max 500 characters if provided
- `author_id` max 255 characters if provided
- Special characters and formatting preserved without corruption (FR-015)
- `fellow_updated_at` used for incremental sync detection

**Relationships**: None (single table design)

**State Transitions**: N/A (content may be updated but no explicit state)

---

## Entity Relationship Diagram

```
┌──────────┐
│   Note   │  (Single table, no relationships)
└──────────┘
```

---

## Database Schema (MySQL)

### Table: `notes`

```sql
CREATE TABLE notes (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT NOT NULL,
    author_name VARCHAR(500),
    author_id VARCHAR(255),
    fellow_created_at DATETIME,
    fellow_updated_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_author_id (author_id),
    INDEX idx_fellow_updated (fellow_updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Table: `backup_metadata` (tracking sync state)

```sql
CREATE TABLE backup_metadata (
    key_name VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Store last successful sync timestamp
-- Example: INSERT INTO backup_metadata (key_name, value, updated_at) 
--          VALUES ('last_sync_timestamp', '2025-12-28T12:00:00Z', NOW())
--          ON DUPLICATE KEY UPDATE value=VALUES(value), updated_at=NOW();
```

---

## Incremental Update Strategy

**Challenge**: FR-008 requires identifying and updating existing records rather than creating duplicates.

**Solution**: Use `fellow_updated_at` timestamps and upsert operations.

### Algorithm:

1. **First Backup (Full Sync)**:
   - Fetch all notes from Fellow.app using POST /api/v1/notes
   - Insert all notes into database
   - Record sync timestamp in `backup_metadata` table

2. **Subsequent Backups (Incremental)**:
   - Retrieve `last_sync_timestamp` from metadata table
   - Query Fellow.app API for notes updated since last sync
   - Use MySQL `INSERT ... ON DUPLICATE KEY UPDATE` for upsert
   - Update sync timestamp on success

### Upsert Example:

```sql
INSERT INTO notes (
    id, content, author_name, author_id,
    fellow_created_at, fellow_updated_at, created_at, updated_at
) VALUES (
    %s, %s, %s, %s, %s, %s, NOW(), NOW()
) ON DUPLICATE KEY UPDATE
    content = VALUES(content),
    author_name = VALUES(author_name),
    author_id = VALUES(author_id),
    fellow_updated_at = VALUES(fellow_updated_at),
    updated_at = NOW();
```

---

## Data Integrity Constraints

**Unique Constraints**:
- Primary key on `id` prevents duplicate records

**Indexes**:
- `author_id` indexed for queries filtering by author
- `fellow_updated_at` indexed for incremental sync queries

**Character Encoding**:
- UTF-8 (utf8mb4) supports all Unicode characters including emojis
- `utf8mb4_unicode_ci` collation for proper sorting

---

## Timestamp Strategy (FR-014)

**Approach**: Store all timestamps in UTC.

**Fields**:
- `fellow_created_at`, `fellow_updated_at`: Preserve original Fellow.app timestamps (converted to UTC if not already)
- `created_at`, `updated_at`: Backup system timestamps in UTC

**Rationale**:
- UTC eliminates DST and timezone conversion issues
- Fellow.app API likely returns ISO 8601 timestamps with timezone info
- Python's `datetime` with timezone-aware objects ensures correct conversion

---

## Edge Case Handling

### Deleted Notes in Fellow.app
- **Challenge**: How to handle notes deleted from Fellow.app in subsequent backups?
- **Solution**: Backups are append-only; deletions not synced. Add `is_deleted` flag if soft-delete tracking needed.

### Large Content
- **Challenge**: Very large notes with extensive content
- **Solution**: TEXT type supports up to 65KB; MEDIUMTEXT (16MB) or LONGTEXT (4GB) if needed

### API Rate Limiting
- **Challenge**: Fellow.app may throttle requests
- **Solution**: Exponential backoff with retry; batch size configurable

### Concurrent Backups
- **Challenge**: Multiple backup processes running simultaneously
- **Solution**: Not supported in v1; add advisory locks if needed later

---

## Success Metrics Mapping

| Success Criterion | Data Model Support |
|-------------------|--------------------|
| SC-001: 100% data integrity | Primary key, NOT NULL constraint, UTF-8 encoding |
| SC-002: 1000 notes < 10min | Indexed queries, batch inserts, async API client |
| SC-003: Incremental 30% faster | `fellow_updated_at` index, upsert operations |
| SC-005: Zero corruption | UTF-8 encoding, TEXT type, parameterized queries |
| SC-007: Query < 2 seconds | Indexes on author_id, fellow_updated_at |

---

## Migration Path

**Initial Setup**:
1. Run schema creation SQL scripts: notes table → backup_metadata table
2. Idempotent: Use `CREATE TABLE IF NOT EXISTS` for safety

**Schema Versioning** (future consideration):
- Add `schema_version` to backup_metadata table
- Use migration scripts for schema changes

---

## Next Steps

With data model complete, proceed to:
- Define API contracts in `contracts/` directory
- Create quickstart guide in `quickstart.md`
- Update agent context with technology choices
