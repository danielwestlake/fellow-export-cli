# Research: Fellow.app API Backup

**Date**: 2025-12-24  
**Feature**: 001-fellow-api-backup

## Research Tasks

This document consolidates findings for technical decisions identified as "NEEDS CLARIFICATION" in the Technical Context section of the implementation plan.

---

## 1. Language/Runtime Selection

### Decision: Python 3.11+

### Rationale:
- **API Integration**: Python has mature HTTP libraries (requests, httpx) with excellent support for REST APIs, authentication, and error handling
- **MySQL Support**: Native MySQL connectors (mysql-connector-python, PyMySQL) are well-maintained and performant
- **CLI Development**: argparse/click provide robust CLI argument parsing; easy to create user-friendly command-line tools
- **Error Handling**: Python's exception handling is intuitive for managing API failures, network issues, and database errors
- **Development Speed**: Rapid prototyping and iteration for a one-time/occasional-use backup tool
- **Cross-platform**: Works on Linux, macOS, and Windows without modification
- **JSON Handling**: Native JSON support essential for parsing Fellow.app API responses

### Alternatives Considered:
- **Node.js/TypeScript**: Strong for API integration but adds complexity with type definitions; overkill for this use case
- **Go**: Excellent performance and compiled binary, but longer development time for a utility script; better suited for production services
- **Ruby**: Good for scripting but smaller ecosystem for this specific use case compared to Python
- **Bash/Shell**: Too limited for complex API interactions, JSON parsing, and database operations

---

## 2. Primary Dependencies

### Decision: 
- **HTTP Client**: `httpx` (async-capable HTTP client with connection pooling)
- **Database**: `mysql-connector-python` (official MySQL driver)
- **CLI**: `click` (intuitive CLI framework with decorators)
- **Logging**: `structlog` (structured logging for observability)
- **Configuration**: `python-dotenv` (environment variable management)
- **Testing**: `pytest` with `pytest-asyncio` for async test support

### Rationale:

**httpx over requests**:
- Async/await support for efficient API pagination
- Built-in connection pooling and retry mechanisms
- HTTP/2 support if needed
- Modern API design
- Compatible with synchronous code if async not needed initially

**mysql-connector-python**:
- Official Oracle MySQL driver with strong community support
- Pure Python implementation (no C dependencies for easier deployment)
- Supports parameterized queries for SQL injection prevention
- Good documentation and examples

**click over argparse**:
- Cleaner syntax with decorators
- Automatic help text generation
- Built-in parameter validation
- Easier to test CLI commands
- Better user experience with colors and formatting

**structlog**:
- Structured logging enables easier debugging and auditing
- Machine-readable logs for potential log aggregation
- Context binding (attach request IDs, meeting IDs to log entries)
- Required for FR-011 (log all API requests/responses)

### Alternatives Considered:
- **requests**: Simpler but synchronous only; httpx provides future-proofing
- **PyMySQL**: Pure Python but less maintained than official connector
- **SQLAlchemy**: ORM would be overkill for straightforward data storage
- **argparse**: Standard library but more verbose than click
- **logging**: Standard but less structured than structlog

---

## 3. Testing Framework Selection

### Decision: pytest with coverage and async support

### Rationale:
- **Industry Standard**: pytest is the de facto testing framework for Python
- **Fixtures**: Reusable test fixtures for database connections, API mocks
- **Parametrization**: Easy to test multiple scenarios with `@pytest.mark.parametrize`
- **Async Support**: pytest-asyncio for testing async API client code
- **Mocking**: Works well with `pytest-mock` for mocking Fellow.app API responses
- **Coverage**: pytest-cov integration for code coverage reports
- **Assertion Introspection**: Better error messages than unittest

**Additional Testing Tools**:
- `pytest-mock`: Simplified mocking/patching
- `responses` or `httpx-mock`: HTTP request mocking for contract tests
- `pytest-docker`: Spin up MySQL container for integration tests
- `faker`: Generate test data for meetings, participants, notes

### Test Structure:
```
tests/
├── contract/
│   └── test_fellow_api_schema.py    # Validate API response schemas
├── integration/
│   ├── test_database_operations.py  # MySQL CRUD operations
│   └── test_backup_workflow.py      # End-to-end backup scenarios
└── unit/
    ├── test_api_client.py           # API client pagination, rate limiting
    ├── test_models.py               # Data model validation
    └── test_database_service.py     # Database service logic
```

### Alternatives Considered:
- **unittest**: Standard library but more verbose, less feature-rich
- **nose2**: Less actively maintained than pytest
- **Robot Framework**: Overkill for this project size

---

## 4. Target Platform

### Decision: Cross-platform CLI (Linux/macOS primary, Windows compatible)

### Rationale:
- **Unix-First**: Likely to be run by DevOps/admins on Linux/macOS systems
- **Python Portability**: Python 3.11+ runs identically on all major platforms
- **Docker Option**: Can be containerized for consistent execution environment
- **No GUI Required**: Command-line tool aligns with admin/scripting workflows
- **Environment Variables**: Cross-platform configuration via .env files
- **Path Handling**: Use `pathlib` for cross-platform file operations if needed

**Deployment Options**:
1. **Direct Python**: `pip install` with requirements.txt
2. **Docker**: Dockerfile for containerized execution with MySQL connection
3. **Standalone Binary**: PyInstaller for single-file executable (if needed)

### Platform-Specific Considerations:
- **Credentials Storage**: Environment variables (.env file) cross-platform
- **Log Files**: Use platform-agnostic paths or stdout/stderr only
- **MySQL Connection**: TCP connection works identically across platforms
- **Timezone Handling**: Use UTC internally, leverage Python's `zoneinfo` (Python 3.9+)

### Alternatives Considered:
- **Web Application**: Overkill for a backup tool; adds unnecessary complexity
- **Cloud Function**: Limited execution time might not suffice for large backups
- **Scheduled Service**: Could be added later, but CLI-first provides flexibility

---

## 5. Fellow.app API Integration Best Practices

### Research Findings:

**Authentication**:
- Fellow.app likely uses API key or OAuth 2.0 bearer tokens
- Store credentials in environment variables, never hardcode
- Implement token refresh if using OAuth

**Rate Limiting**:
- Implement exponential backoff for rate limit errors (HTTP 429)
- Use `Retry-After` header if provided
- Default conservative rate: 10-20 requests/minute until limits confirmed
- Add configurable rate limit via CLI flag

**Pagination**:
- Fellow.app API likely uses offset/limit or cursor-based pagination
- Fetch page size: Start with 50-100 items per page, tune based on API docs
- Handle incomplete pages (last page might be partial)

**Error Handling**:
- Network errors: Retry with exponential backoff (max 3-5 retries)
- 401/403: Invalid credentials, halt immediately with clear error
- 404: Resource not found, log and continue with next item
- 500/502/503: Server error, retry with backoff
- Timeout: Set reasonable timeout (30-60 seconds per request)

**API Discovery**:
- Review Fellow.app API documentation (if available)
- Common endpoints likely include:
  - `/api/v1/meetings` - List meetings
  - `/api/v1/meetings/{id}` - Get meeting details
  - `/api/v1/meetings/{id}/notes` - Get meeting notes
  - `/api/v1/meetings/{id}/action-items` - Get action items
  - `/api/v1/users` - Get participants/users

**Data Extraction Strategy**:
1. Fetch all meeting IDs with pagination
2. For each meeting, fetch details + relationships in parallel (rate-limited)
3. Store in database transactionally
4. Track last sync timestamp for incremental updates

---

## 6. MySQL Schema Design Best Practices

### Research Findings:

**Schema Principles**:
- Normalize to 3NF to avoid data duplication
- Use foreign keys for referential integrity
- Add indexes on frequently queried columns
- Use appropriate data types (DATETIME for timestamps, TEXT for content)
- Add `created_at` and `updated_at` timestamps to all tables

**Recommended Schema**:

```sql
-- Workspaces table
CREATE TABLE workspaces (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_name (name)
);

-- Meetings table
CREATE TABLE meetings (
    id VARCHAR(255) PRIMARY KEY,
    workspace_id VARCHAR(255) NOT NULL,
    title VARCHAR(1000) NOT NULL,
    meeting_date DATETIME NOT NULL,
    duration_minutes INT,
    status VARCHAR(50),
    fellow_created_at DATETIME,
    fellow_updated_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    INDEX idx_meeting_date (meeting_date),
    INDEX idx_workspace (workspace_id)
);

-- Participants table (persons who can attend meetings)
CREATE TABLE participants (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    email VARCHAR(500),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE INDEX idx_email (email),
    INDEX idx_name (name)
);

-- Meeting participants (many-to-many)
CREATE TABLE meeting_participants (
    meeting_id VARCHAR(255) NOT NULL,
    participant_id VARCHAR(255) NOT NULL,
    role VARCHAR(100),  -- organizer, attendee, optional
    created_at DATETIME NOT NULL,
    PRIMARY KEY (meeting_id, participant_id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
);

-- Notes table
CREATE TABLE notes (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id VARCHAR(255),
    note_order INT,  -- preserve order of notes in meeting
    fellow_created_at DATETIME,
    fellow_updated_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES participants(id) ON DELETE SET NULL,
    INDEX idx_meeting (meeting_id)
);

-- Action items table
CREATE TABLE action_items (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    assignee_id VARCHAR(255),
    due_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME,
    fellow_created_at DATETIME,
    fellow_updated_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES participants(id) ON DELETE SET NULL,
    INDEX idx_meeting (meeting_id),
    INDEX idx_assignee (assignee_id),
    INDEX idx_due_date (due_date),
    INDEX idx_completed (completed)
);
```

**Incremental Update Strategy**:
- Use `fellow_updated_at` timestamp to identify changed records
- Store last successful sync timestamp in a metadata table
- Use `INSERT ... ON DUPLICATE KEY UPDATE` for upsert operations
- Maintain separate `created_at`/`updated_at` for backup system tracking

**Data Integrity**:
- Foreign keys enforce relationships
- CASCADE deletes maintain consistency
- NOT NULL on required fields prevents incomplete data
- VARCHAR(255) for IDs accommodates various ID formats
- TEXT type for potentially long content

---

## 7. Progress Reporting & Observability

### Decision: Structured logging with progress indicators

### Approach:

**Structured Logging** (via structlog):
```python
log.info("backup_started", workspace_id=ws_id, total_meetings=count)
log.info("meeting_processed", meeting_id=m_id, notes_count=n, actions_count=a)
log.error("api_request_failed", endpoint=url, status_code=code, retry_count=n)
log.info("backup_completed", duration_seconds=dur, meetings_backed_up=count)
```

**Progress Indicators** (via tqdm or rich):
- Real-time progress bar showing % completion
- ETA based on current processing rate
- Counts: meetings processed, notes saved, action items saved
- CLI flag to disable for non-interactive environments

**Summary Report** (FR-015):
```
Backup Summary
==============
Workspace: Engineering Team (ws_abc123)
Duration: 8m 32s
Status: SUCCESS

Statistics:
  - Meetings backed up: 247
  - Notes extracted: 1,842
  - Action items saved: 356
  - Participants recorded: 18

Errors:
  - Failed meetings: 2 (API timeout)
    - meeting_id_123: Connection timeout
    - meeting_id_456: 500 Server Error
```

**Observability Requirements**:
- All HTTP requests logged with timestamp, endpoint, status code
- Database operations logged (inserts, updates, errors)
- Error context captured (meeting ID, participant ID, etc.)
- Log level configurable via CLI (--verbose, --quiet flags)

### Alternatives Considered:
- **Database-only logging**: Less real-time visibility
- **File-based reports**: Less flexible than stdout/stderr
- **Email notifications**: Over-engineered for initial version

---

## Summary of Resolved Clarifications

| Technical Context Item | Resolution |
|------------------------|------------|
| Language/Version | Python 3.11+ |
| Primary Dependencies | httpx, mysql-connector-python, click, structlog |
| Testing | pytest with pytest-asyncio, pytest-mock, httpx-mock |
| Target Platform | Cross-platform CLI (Linux/macOS primary) |
| HTTP Client Strategy | httpx with async support, exponential backoff, rate limiting |
| Database Schema | Normalized tables with foreign keys, indexes, timestamps |
| Progress Reporting | structlog + progress bars + summary report |

## Next Steps

With all clarifications resolved, proceed to:
- **Phase 1**: Data model design (`data-model.md`)
- **Phase 1**: API contracts definition (`contracts/`)
- **Phase 1**: Quickstart guide (`quickstart.md`)
