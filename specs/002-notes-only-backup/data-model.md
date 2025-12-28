# Data Model: Fellow.app Notes-Only Backup

**Feature**: Notes-Only Backup  
**Branch**: `002-notes-only-backup`  
**Date**: 2025-12-28

## Overview

This document defines the data model for the simplified notes-only backup feature. The design eliminates all entity relationships and stores notes as standalone records with embedded author information.

## Entities

### Note

**Purpose**: Represents a single note from Fellow.app with complete metadata for standalone storage.

**Fields**:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| id | string | Yes | Unique identifier from Fellow.app API | Primary key; VARCHAR(255) |
| content | string | Yes | Full text content of the note | TEXT (utf8mb4); not null |
| author_name | string | No | Display name of note author | VARCHAR(500); nullable |
| author_id | string | No | Fellow.app user ID of author | VARCHAR(255); nullable |
| fellow_created_at | datetime | No | Creation timestamp from Fellow.app | DATETIME; nullable |
| fellow_updated_at | datetime | No | Last update timestamp from Fellow.app | DATETIME; nullable; indexed |
| created_at | datetime | Yes | Local database creation timestamp | DATETIME; not null; auto-generated |
| updated_at | datetime | Yes | Local database update timestamp | DATETIME; not null; auto-updated |

**Validation Rules**:
- id must be non-empty string matching Fellow.app's ID format
- content must be non-empty after trimming whitespace
- Timestamps must be valid datetime objects or None
- UTF-8 encoding required for content field (supports emojis, non-Latin scripts)

**State Transitions**:
- New note: INSERT with all fields
- Updated note: UPDATE content, author_name, fellow_updated_at, updated_at based on fellow_updated_at comparison
- No deletion state (notes are preserved for historical record)

**Relationships**: None (standalone entity)

## Database Schema

### notes Table

```sql
CREATE TABLE notes (
    -- Primary identifier
    id VARCHAR(255) PRIMARY KEY COMMENT 'Fellow.app note ID',
    
    -- Content
    content TEXT NOT NULL COMMENT 'Note text content with full Unicode support',
    
    -- Author information (denormalized)
    author_name VARCHAR(500) COMMENT 'Author display name from Fellow.app',
    author_id VARCHAR(255) COMMENT 'Fellow.app user/author ID',
    
    -- Fellow.app timestamps (preserved exactly as received)
    fellow_created_at DATETIME COMMENT 'Creation timestamp from Fellow.app',
    fellow_updated_at DATETIME COMMENT 'Last update timestamp from Fellow.app',
    
    -- Local tracking timestamps
    created_at DATETIME NOT NULL COMMENT 'Local record creation timestamp',
    updated_at DATETIME NOT NULL COMMENT 'Local record update timestamp',
    
    -- Indexes for query performance
    INDEX idx_fellow_updated (fellow_updated_at) COMMENT 'Incremental backup queries',
    INDEX idx_author_id (author_id) COMMENT 'Author-based queries'
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fellow.app notes backup - standalone note records';
```

**Storage Considerations**:
- TEXT column supports up to 65,535 bytes (sufficient for typical notes)
- utf8mb4 character set: 4 bytes per character worst case = ~16,000 characters
- For larger notes, can migrate to MEDIUMTEXT if needed (16MB)
- InnoDB engine provides transaction support for data integrity

### backup_metadata Table

```sql
CREATE TABLE backup_metadata (
    key_name VARCHAR(255) PRIMARY KEY COMMENT 'Metadata key identifier',
    value TEXT NOT NULL COMMENT 'Metadata value (JSON or string)',
    updated_at DATETIME NOT NULL COMMENT 'Last update timestamp'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Backup process metadata and sync state tracking';
```

**Usage**:
- Store last successful backup timestamp
- Track API version or configuration
- Record summary statistics from last run

**Example Records**:
```
key_name: 'last_backup_timestamp'
value: '2025-12-28T09:00:00Z'

key_name: 'last_backup_summary'
value: '{"total": 1234, "new": 45, "updated": 23, "errors": 0}'
```

## Data Flow

### 1. API Response to Model

Fellow.app POST /api/v1/notes response structure (inferred):

```json
{
  "notes": [
    {
      "id": "note_abc123",
      "content": "Meeting notes content here...",
      "author": {
        "id": "user_xyz789",
        "name": "John Doe"
      },
      "created_at": "2025-12-20T14:30:00Z",
      "updated_at": "2025-12-27T10:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total": 1234
  }
}
```

Mapping to Note model:

```python
Note(
    id=api_response["id"],
    content=api_response["content"],
    author_name=api_response["author"]["name"],
    author_id=api_response["author"]["id"],
    fellow_created_at=parse_datetime(api_response["created_at"]),
    fellow_updated_at=parse_datetime(api_response["updated_at"]),
    created_at=None,  # Set by database
    updated_at=None   # Set by database
)
```

### 2. Model to Database

Upsert operation (handles both insert and update):

```sql
INSERT INTO notes (
    id, content, author_name, author_id,
    fellow_created_at, fellow_updated_at,
    created_at, updated_at
) VALUES (
    ?, ?, ?, ?,
    ?, ?,
    NOW(), NOW()
)
ON DUPLICATE KEY UPDATE
    content = VALUES(content),
    author_name = VALUES(author_name),
    author_id = VALUES(author_id),
    fellow_updated_at = VALUES(fellow_updated_at),
    updated_at = NOW();
```

**Logic**:
- If id doesn't exist: INSERT new record with all fields
- If id exists: UPDATE content, author info, fellow_updated_at, and local updated_at
- fellow_created_at and created_at are immutable after initial insert

### 3. Incremental Backup Query

```sql
-- Get last backup point
SELECT MAX(fellow_updated_at) FROM notes;

-- In API call, filter notes updated after this timestamp
-- (implementation depends on Fellow.app API filter capabilities)
```

If API doesn't support filtering by updated_at:
- Fetch all notes
- Compare fellow_updated_at in application code
- Only upsert notes with newer fellow_updated_at than local database

## Validation and Constraints

### Application-Level Validation

**Before Insert/Update**:
1. Validate id is non-empty string
2. Validate content is non-empty after strip()
3. Ensure author_name and author_id are strings or None
4. Parse and validate datetime strings from API
5. Sanitize content for SQL injection (use parameterized queries)

**Error Handling**:
- Invalid datetime: Log warning, set field to None, continue
- Missing required field: Log error with note ID, skip note
- UTF-8 encoding errors: Log error with note ID, attempt recovery or skip

### Database-Level Constraints

**Enforced by Schema**:
- PRIMARY KEY on id: Prevents duplicate notes
- NOT NULL on content: Ensures note has actual content
- NOT NULL on created_at, updated_at: Ensures tracking timestamps
- utf8mb4 character set: Prevents encoding errors

**Indexed for Performance**:
- idx_fellow_updated: Fast incremental backup queries
- idx_author_id: Fast author-based queries and reports

## Migration from Current Schema

### Changes Required

**Existing Schema** (to be replaced):
- meetings table: REMOVE
- participants table: REMOVE
- meeting_participants table: REMOVE
- action_items table: REMOVE
- workspaces table: REMOVE
- notes table: MODIFY (remove meeting_id foreign key, add author_name)

**Migration Strategy**:
1. Create backup of existing database
2. Export existing notes data with author info resolved via joins
3. Drop old schema
4. Create new simplified schema
5. Import notes with author_name/author_id populated
6. Verify data integrity (count, sample content checks)

**Data Preservation**:
- Existing note content, timestamps preserved
- Author information resolved from participants table before migration
- No data loss for notes entity

## Query Patterns

### Common Queries

**Get all notes for an author**:
```sql
SELECT * FROM notes
WHERE author_id = ?
ORDER BY fellow_created_at DESC;
```

**Get recently updated notes**:
```sql
SELECT * FROM notes
WHERE fellow_updated_at >= ?
ORDER BY fellow_updated_at DESC
LIMIT 100;
```

**Full-text search in content**:
```sql
SELECT * FROM notes
WHERE content LIKE ?
ORDER BY fellow_updated_at DESC;
```

**Summary statistics**:
```sql
SELECT 
    COUNT(*) as total_notes,
    COUNT(DISTINCT author_id) as unique_authors,
    MIN(fellow_created_at) as earliest_note,
    MAX(fellow_updated_at) as latest_update
FROM notes;
```

## Performance Considerations

**Index Usage**:
- idx_fellow_updated: Enables fast incremental backup queries (<10ms for typical workload)
- idx_author_id: Enables fast author filtering (<50ms for typical workload)
- Primary key on id: O(log n) lookup for upsert operations

**Expected Performance**:
- 1000 notes insert: ~30 seconds (including network I/O)
- Incremental backup (100 updated notes): ~5 seconds
- Full-text search query: ~500ms for 10,000 notes (unindexed)

**Optimization Opportunities**:
- Add FULLTEXT index on content for faster search (if needed)
- Batch insert statements for better throughput
- Connection pooling for concurrent operations

## Compliance with Requirements

**Functional Requirements Coverage**:
- FR-004: ✅ id field stores note ID
- FR-005: ✅ content field with utf8mb4 encoding
- FR-006: ✅ author_name field
- FR-007: ✅ author_id field
- FR-008: ✅ fellow_created_at field
- FR-009: ✅ fellow_updated_at field with index
- FR-010: ✅ Complete schema matches requirement
- FR-011: ✅ idx_fellow_updated supports timestamp queries
- FR-012: ✅ ON DUPLICATE KEY UPDATE handles updates
- FR-013: ✅ PRIMARY KEY prevents duplicates
- FR-019: ✅ DATETIME fields preserve original timestamps

**Success Criteria Coverage**:
- SC-001: ✅ Schema captures all note data
- SC-005: ✅ utf8mb4 encoding preserves special characters
- SC-007: ✅ Indexed queries support <2s response time
