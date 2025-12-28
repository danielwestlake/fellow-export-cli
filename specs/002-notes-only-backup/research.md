# Research: Fellow.app Notes-Only Backup

**Feature**: Notes-Only Backup  
**Branch**: `002-notes-only-backup`  
**Date**: 2025-12-28

## Overview

This document consolidates technical research and design decisions for simplifying the Fellow.app backup tool to exclusively handle notes via the POST /api/v1/notes endpoint. All technical context is well-defined from the existing codebase, so this research focuses on design decisions for the simplification.

## Research Tasks

### 1. Fellow.app POST /api/v1/notes Endpoint Behavior

**Decision**: Use POST /api/v1/notes with pagination support for retrieving all notes.

**Rationale**: 
- The spec explicitly mandates using only the POST /api/v1/notes endpoint (FR-002)
- Existing codebase in `src/services/fellow_api.py` already implements POST request handling with httpx
- Pagination is required per FR-003 to handle large note collections
- API response includes note id, content, author information (author_name, author_id), and timestamps (fellow_created_at, fellow_updated_at)

**Implementation Details**:
- Endpoint accepts pagination parameters (likely `page` and `per_page` or `offset`/`limit`)
- Response includes notes array and pagination metadata
- Rate limiting must be respected (existing exponential backoff in fellow_api.py)
- Authentication via API token in headers (existing pattern in codebase)

**Alternatives Considered**:
- GET /api/v1/notes: Not mentioned in spec; POST is explicitly required
- Streaming API: Fellow.app doesn't provide streaming endpoints
- GraphQL: Fellow.app uses REST API

### 2. Database Schema Simplification

**Decision**: Create standalone notes table without foreign key dependencies; store author_name directly.

**Rationale**:
- Removes complexity of managing meetings, workspaces, and participants tables
- Author information (author_name, author_id) is embedded in note response - no separate lookup needed
- Eliminates cascading delete concerns and join queries
- Maintains data integrity by storing complete note records atomically
- Simpler backup/restore operations with single-table design

**Schema Design**:
```sql
CREATE TABLE notes (
    id VARCHAR(255) PRIMARY KEY,           -- Fellow.app note ID
    content TEXT NOT NULL,                  -- Note text content
    author_name VARCHAR(500),               -- Author's display name
    author_id VARCHAR(255),                 -- Fellow.app author/user ID
    fellow_created_at DATETIME,             -- Creation timestamp from Fellow.app
    fellow_updated_at DATETIME,             -- Last update timestamp from Fellow.app
    created_at DATETIME NOT NULL,           -- Local DB creation timestamp
    updated_at DATETIME NOT NULL,           -- Local DB update timestamp
    INDEX idx_fellow_updated (fellow_updated_at),
    INDEX idx_author_id (author_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Alternatives Considered**:
- Keep foreign key to participants table: Rejected - adds unnecessary complexity for notes-only feature
- Store author data in JSON column: Rejected - less queryable and doesn't simplify schema significantly
- Use MEDIUMTEXT or LONGTEXT for content: Rejected - TEXT (65KB) is sufficient for typical notes; can revisit if needed

### 3. Incremental Backup Strategy

**Decision**: Use fellow_updated_at timestamp comparison for incremental updates.

**Rationale**:
- Fellow.app provides fellow_updated_at timestamp for each note (FR-009)
- Query database for MAX(fellow_updated_at) to find last backup point
- Filter API requests to only retrieve notes modified since that timestamp
- Reduces API load and processing time for subsequent backups (target: <30% of full backup time per SC-003)
- Upsert pattern (INSERT ... ON DUPLICATE KEY UPDATE) handles both new and updated notes

**Implementation**:
```sql
-- Get last backup timestamp
SELECT MAX(fellow_updated_at) FROM notes;

-- Update logic in database service
INSERT INTO notes (id, content, author_name, author_id, fellow_created_at, fellow_updated_at, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    content = VALUES(content),
    author_name = VALUES(author_name),
    fellow_updated_at = VALUES(fellow_updated_at),
    updated_at = NOW();
```

**Alternatives Considered**:
- Track deleted notes: Rejected - Fellow.app API doesn't provide deletion events; notes-only backup is for historical preservation
- Use batch timestamps in backup_metadata: Considered but MAX(fellow_updated_at) query is simpler and equally effective
- Version history: Rejected - out of scope; only latest version needed

### 4. Data Model Simplification

**Decision**: Remove all entity models except Note; simplify Note model to remove meeting_id.

**Rationale**:
- Spec explicitly requires removing meetings, workspaces, action items, and streams
- Note entity becomes standalone - no relationships to manage
- Simplified dataclass with 8 fields matching database schema
- Type safety maintained with Python dataclasses and Optional typing

**Model Definition**:
```python
@dataclass
class Note:
    """Standalone note model for Fellow.app backup."""
    id: str
    content: str
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    fellow_created_at: Optional[datetime] = None
    fellow_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**Alternatives Considered**:
- Keep Meeting model with nullable fields: Rejected - violates spec requirement to remove meeting references
- Use dict instead of dataclass: Rejected - loses type safety and IDE support
- Pydantic models: Rejected - unnecessary dependency; dataclasses sufficient for internal models

### 5. Service Layer Refactoring

**Decision**: Simplify backup.py orchestration to single notes-only workflow; remove multi-entity coordination.

**Rationale**:
- Current backup.py orchestrates meetings → participants → notes → action items sequence
- Simplified version: authenticate → fetch notes (with pagination) → store notes → report
- Remove workspace and meeting retrieval logic
- Single entity type eliminates ordering concerns and dependency management

**Service Flow**:
1. Authenticate with Fellow.app API (existing)
2. Determine incremental backup start point (MAX(fellow_updated_at) or None for full backup)
3. Fetch notes from POST /api/v1/notes with pagination
4. For each note: parse response → create Note model → upsert to database
5. Handle failures gracefully (log and continue)
6. Generate summary report (counts, errors)

**Alternatives Considered**:
- Keep existing orchestration structure: Rejected - unnecessary abstraction for single entity
- Async batch processing: Considered but synchronous pagination simpler; can optimize later if needed
- Parallel API requests: Rejected initially - respect rate limits; optimize if performance inadequate

### 6. CLI Command Simplification

**Decision**: Retain single `backup` command; remove meeting/workspace-specific options.

**Rationale**:
- Current CLI has commands for different entity types and workspaces
- Simplified CLI: `fellow-backup backup` (existing command) with options for --full, --incremental, --dry-run
- Remove workspace selection since notes are fetched globally
- Maintain existing logging and progress indicator patterns

**Command Structure**:
```bash
fellow-backup backup [OPTIONS]

Options:
  --full            Force full backup (ignore incremental timestamps)
  --dry-run         Show what would be backed up without writing to database
  --verbose         Enable detailed logging
  --quiet           Suppress progress output (errors only)
  --json            Output summary report in JSON format
  --help            Show this message and exit
```

**Alternatives Considered**:
- Separate `backup-notes` command: Rejected - since notes are the only entity, generic `backup` is clearer
- Remove --full flag: Rejected - useful for testing and re-syncing

### 7. Error Handling and Resilience

**Decision**: Continue using existing httpx retry logic with exponential backoff; add per-note error isolation.

**Rationale**:
- Fellow.app API rate limiting requires retry logic (FR-014)
- Existing fellow_api.py implements retry with exponential backoff
- Individual note failures must not stop entire backup (FR-016)
- Try/except around each note processing; log error with note ID and continue

**Error Categories**:
- API errors (4xx, 5xx): Retry with backoff; log and skip after max retries
- Rate limiting (429): Exponential backoff with jitter; automatic retry
- Database errors: Rollback transaction; log error; retry note or continue
- Parsing errors: Log note ID and raw response; continue to next note

**Alternatives Considered**:
- Stop on first error: Rejected - violates FR-016 and resilience principle
- Dead letter queue: Considered but overkill for one-time backup; error log sufficient
- Checkpointing every N notes: Considered but database transactions provide adequate safety

### 8. Testing Strategy

**Decision**: Contract tests for POST /api/v1/notes endpoint; integration tests for simplified schema; unit tests for note parsing.

**Rationale**:
- Contract tests verify API endpoint behavior and response structure
- Integration tests validate database upsert logic and incremental backup queries
- Unit tests for Note model creation from API response
- Simplified feature reduces test matrix (no cross-entity validation needed)

**Test Coverage**:
- Contract: POST /api/v1/notes with pagination, rate limiting, error responses
- Integration: notes table CRUD, incremental backup timestamp logic, UTF-8 content handling
- Unit: Note model instantiation, timestamp parsing, upsert SQL generation
- E2E: Full backup → verify counts → incremental backup → verify only new/updated notes

**Alternatives Considered**:
- Mock all API calls: Rejected for contract tests - need real endpoint verification
- Test against production API: Rejected - use test/sandbox environment or recorded responses

## Summary

All technical decisions are straightforward simplifications of the existing codebase. No new technologies or patterns required. The main work is **removing code** for unused entities while preserving the core backup orchestration, API client, and database service patterns. The notes-only design eliminates foreign key complexity and multi-entity coordination, resulting in a simpler, more focused tool.

## Open Questions

None. All technical context is well-defined. Implementation can proceed to Phase 1 (design artifacts).
