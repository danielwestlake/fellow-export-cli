# Implementation Plan: Fellow.app Notes-Only Backup

**Branch**: `002-notes-only-backup` | **Date**: 2025-12-28 | **Spec**: [specs/002-notes-only-backup/spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-notes-only-backup/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Simplify the Fellow.app backup feature to exclusively backup notes using the POST /api/v1/notes endpoint. Remove all dependencies on meetings, workspaces, action items, and streams. Store notes with complete metadata (author information, timestamps) in a simplified MySQL schema with support for incremental updates based on fellow_updated_at timestamps.

## Technical Context

**Language/Version**: Python 3.11+ (current environment: Python 3.13.7)  
**Primary Dependencies**: httpx (async HTTP), mysql-connector-python (MySQL driver), click (CLI framework), structlog (structured logging), python-dotenv (configuration)  
**Storage**: MySQL 5.7+ or 8.0+ with utf8mb4 character set for full Unicode support  
**Testing**: pytest with pytest-asyncio and pytest-mock for unit/integration/contract tests  
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows) - server/workstation environments  
**Project Type**: Single project (CLI tool with library components)  
**Performance Goals**: Process 1000 notes in under 10 minutes; incremental backup in <30% of full backup time  
**Constraints**: API rate limiting compliance with exponential backoff; UTF-8 data integrity; transactional database operations  
**Scale/Scope**: Typical workload ~1000-5000 notes; support for large note content (multi-megabyte text); idempotent operations for safe re-runs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Data Integrity First
✅ **PASS**: Notes schema includes all required fields (id, content, author_name, author_id, fellow_created_at, fellow_updated_at, created_at, updated_at). Simplified design removes foreign key dependencies while maintaining data completeness. UTF-8 (utf8mb4) encoding specified for content preservation. Transactional operations required in database service.

### II. Idempotent Operations
✅ **PASS**: Notes table uses id as primary key (stable identifier from Fellow.app API). INSERT ... ON DUPLICATE KEY UPDATE pattern will be used for upsert. Incremental backup uses fellow_updated_at comparison. No cascading deletes since there are no dependent entities.

### III. Observable & Verifiable
✅ **PASS**: Existing structlog infrastructure provides structured logging. Summary report requirement in spec (FR-018) covers counts and error details. Progress indicators required (FR-017). All API requests/responses logged (FR-015).

### IV. Resilient by Design
✅ **PASS**: Rate limiting with exponential backoff required (FR-014). Individual note failures must not block others (FR-016). API error handling with continuation (FR-016). Configuration validation before execution implied by existing CLI structure.

### V. CLI-First Interface
✅ **PASS**: Existing Click-based CLI maintained. Credentials from environment variables (existing .env pattern). Structured logging to stderr, progress to stdout. Exit codes and --dry-run, --verbose flags already established in codebase.

**Overall Status**: ✅ ALL GATES PASSED - Feature aligns with constitution principles. Simplification from full backup to notes-only reduces complexity while maintaining all integrity, resilience, and observability standards.

## Project Structure

### Documentation (this feature)

```text
specs/002-notes-only-backup/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Single project structure (existing)
src/
├── models/
│   └── __init__.py          # Note dataclass (simplified - remove Meeting, Workspace, ActionItem, Participant)
├── services/
│   ├── fellow_api.py        # Modify: remove all endpoints except POST /api/v1/notes
│   ├── database.py          # Modify: remove tables except notes and backup_metadata
│   └── backup.py            # Modify: simplify to notes-only orchestration
├── cli/
│   └── main.py              # Modify: remove meeting/workspace commands, keep notes backup commands
└── lib/                      # Utility functions (logging, config, retry logic)

tests/
├── contract/                 # API contract tests for POST /api/v1/notes endpoint
├── integration/              # Database integration tests for notes table
└── unit/                     # Service and model unit tests

config/
└── database/
    └── schema.sql           # Modify: simplify to notes + backup_metadata tables only
```

**Structure Decision**: Maintaining existing single-project structure (src/, tests/, config/). This is a simplification feature that removes code rather than adding new projects. The existing CLI/service/model separation remains appropriate for a focused notes-only backup tool. All modifications are subtractive (removing unused entity types) except for adjusting the notes table schema to store author_name directly rather than via foreign key.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations identified.** This is a simplification feature that reduces complexity by removing entities and relationships while maintaining all constitutional principles.

---

## Phase 1 Design Artifacts ✅

**Status**: COMPLETED  
**Date**: 2025-12-28

### Generated Artifacts

1. ✅ **research.md** - Technical decisions documented (Fellow.app API, schema simplification, incremental backup strategy, service refactoring)
2. ✅ **data-model.md** - Database schema defined (standalone notes table with author_name, backup_metadata table)
3. ✅ **contracts/fellow-api.md** - API contract specified (POST /api/v1/notes with pagination, authentication, rate limiting)
4. ✅ **quickstart.md** - User guide created (installation, usage, querying, troubleshooting)
5. ✅ **Agent context updated** - GitHub Copilot instructions updated with Python 3.11+, httpx, MySQL dependencies

### Post-Phase 1 Constitution Re-Check

**Re-evaluation after detailed design**:

#### I. Data Integrity First
✅ **CONFIRMED**: 
- data-model.md specifies utf8mb4 encoding for all text fields
- Upsert pattern documented with ON DUPLICATE KEY UPDATE
- Validation rules defined (non-empty id, content; datetime parsing)
- Migration strategy documented to preserve existing data

#### II. Idempotent Operations
✅ **CONFIRMED**:
- Upsert SQL explicitly documented in data-model.md
- Incremental backup uses MAX(fellow_updated_at) query
- No deletion operations (historical preservation)
- Primary key on id prevents duplicates

#### III. Observable & Verifiable
✅ **CONFIRMED**:
- quickstart.md documents logging patterns and output formats
- Summary report structure defined in contracts/fellow-api.md
- Query patterns provided for verification in data-model.md
- Dry-run mode documented in quickstart.md

#### IV. Resilient by Design
✅ **CONFIRMED**:
- Rate limiting with exponential backoff specified in contracts/fellow-api.md
- Per-note error isolation documented in research.md
- Error categories and handling strategies defined
- Retry logic with jitter and max attempts specified

#### V. CLI-First Interface
✅ **CONFIRMED**:
- Click-based CLI documented in quickstart.md
- Environment variable configuration (.env pattern)
- Command options: --full, --dry-run, --verbose, --quiet, --json
- Exit codes and help text specified

**Final Status**: ✅ ALL CONSTITUTION GATES PASSED POST-DESIGN

Design artifacts maintain all constitutional principles. Ready for Phase 2 (task breakdown).

---

## Next Steps

Phase 2 (Task Generation) should be initiated with `/speckit.tasks` command. The implementation plan, research, data model, API contracts, and quickstart guide provide complete context for generating executable task breakdown in tasks.md.
