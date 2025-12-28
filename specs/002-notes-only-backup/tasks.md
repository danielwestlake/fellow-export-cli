# Tasks: Fellow.app Notes-Only Backup

**Input**: Design documents from `/specs/002-notes-only-backup/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, contracts/fellow-api.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Not explicitly requested in the feature specification - focusing on implementation tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `config/` at repository root
- This is a simplification feature - removing code for meetings, workspaces, action items

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema initialization and configuration updates

- [X] T001 Update database schema in config/database/schema.sql to remove meetings, participants, meeting_participants, action_items, and workspaces tables
- [X] T002 [P] Modify notes table schema in config/database/schema.sql to remove meeting_id foreign key and add author_name VARCHAR(500) field
- [X] T003 [P] Add backup_metadata table to config/database/schema.sql with key_name, value, and updated_at fields
- [X] T004 [P] Update requirements.txt to ensure httpx, mysql-connector-python, click, structlog, and python-dotenv are specified
- [X] T005 [P] Verify .env.example includes FELLOW_API_TOKEN, FELLOW_API_BASE_URL, and MySQL connection variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core service layer simplification that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Simplify Note model in src/models/__init__.py to remove meeting_id field and ensure all required fields are present (id, content, author_name, author_id, fellow_created_at, fellow_updated_at, created_at, updated_at)
- [X] T007 [P] Remove Meeting, Workspace, ActionItem, and Participant model classes from src/models/__init__.py
- [X] T008 Refactor fellow_api.py in src/services/fellow_api.py to remove all endpoints except POST /api/v1/notes
- [X] T009 Update fetch_notes method in src/services/fellow_api.py to accept page, per_page, and updated_after parameters matching API contract
- [X] T010 [P] Remove workspace and meeting-related methods from src/services/fellow_api.py
- [X] T011 Simplify database service in src/services/database.py to remove all table operations except notes and backup_metadata
- [X] T012 Update notes table operations in src/services/database.py to use upsert pattern (INSERT ... ON DUPLICATE KEY UPDATE)
- [X] T013 [P] Add backup_metadata table operations to src/services/database.py for storing last backup timestamp and summary
- [X] T014 Refactor backup orchestration in src/services/backup.py to remove multi-entity coordination and focus on notes-only workflow
- [X] T015 [P] Remove CLI commands for meetings and workspaces from src/cli/main.py, keeping only backup command with --full, --dry-run, --verbose, --quiet, --json options

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Initial Notes Backup (Priority: P1) 🎯 MVP

**Goal**: Extract all notes from Fellow.app using POST /api/v1/notes endpoint and store in MySQL with complete metadata

**Independent Test**: Connect to Fellow.app with valid credentials, call POST /api/v1/notes with pagination, verify all notes stored in MySQL with complete content, author info, and timestamps

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement pagination loop in src/services/backup.py to fetch all pages from POST /api/v1/notes endpoint
- [X] T017 [P] [US1] Add note parsing logic in src/services/backup.py to extract id, content, author.name, author.id, created_at, updated_at from API response
- [X] T018 [US1] Implement note-to-model mapping in src/services/backup.py to create Note objects from API response with proper datetime parsing
- [X] T019 [US1] Add batch upsert operation in src/services/backup.py to store notes in database using database service
- [X] T020 [US1] Implement progress indicator in src/services/backup.py showing count of notes processed during backup
- [X] T021 [US1] Add per-note error handling in src/services/backup.py to log failures and continue processing remaining notes
- [X] T022 [US1] Implement API rate limiting detection and retry logic with exponential backoff in src/services/fellow_api.py
- [X] T023 [US1] Add structured logging for all API requests and responses in src/services/fellow_api.py
- [X] T024 [US1] Update backup command in src/cli/main.py to execute full notes backup workflow with proper exit codes

**Checkpoint**: At this point, User Story 1 should be fully functional - complete initial backup working end-to-end

---

## Phase 4: User Story 2 - Incremental Updates (Priority: P2)

**Goal**: Enable efficient ongoing backups that only process notes with newer fellow_updated_at timestamps

**Independent Test**: Run initial backup, modify notes in Fellow.app, run backup again, verify only notes with newer fellow_updated_at are processed/updated

### Implementation for User Story 2

- [X] T025 [P] [US2] Add query for MAX(fellow_updated_at) in src/services/database.py to determine last backup timestamp
- [X] T026 [US2] Update backup orchestration in src/services/backup.py to check for last backup timestamp before fetching notes
- [X] T027 [US2] Implement updated_after parameter handling in src/services/backup.py to pass timestamp filter to API if available
- [X] T028 [US2] Add incremental mode detection in src/cli/main.py to distinguish between full and incremental backup in logging
- [X] T029 [US2] Update backup_metadata table operations in src/services/database.py to record last_backup_timestamp after successful backup
- [X] T030 [US2] Modify upsert logic in src/services/database.py to only update records where fellow_updated_at is newer than existing value
- [X] T031 [US2] Add logging to differentiate between new notes inserted and existing notes updated in src/services/backup.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - incremental backups functional

---

## Phase 5: User Story 3 - Backup Verification Report (Priority: P3)

**Goal**: Generate summary report after each backup showing counts and errors for verification

**Independent Test**: Run backup process and verify summary report shows accurate counts matching database queries

### Implementation for User Story 3

- [X] T032 [P] [US3] Add backup statistics tracking in src/services/backup.py to count total, new, updated, and error notes during processing
- [X] T033 [P] [US3] Create summary report generator in src/services/backup.py to format statistics with duration and error details
- [X] T034 [US3] Update backup_metadata operations in src/services/database.py to store last_backup_summary as JSON
- [X] T035 [US3] Implement report output in src/cli/main.py to display summary after backup completion
- [X] T036 [US3] Add JSON format option in src/cli/main.py to output summary as structured JSON when --json flag is used
- [X] T037 [US3] Add error detail collection in src/services/backup.py to track note IDs and error messages for failed notes
- [X] T038 [US3] Update logging in src/services/backup.py to include retry attempt counts when rate limiting is encountered

**Checkpoint**: All user stories should now be independently functional with comprehensive reporting

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final refinements

- [X] T039 [P] Update README.md to reflect notes-only functionality and remove references to meetings/workspaces
- [X] T040 [P] Verify quickstart.md examples work with actual CLI commands
- [X] T041 [P] Add UTF-8 encoding validation in src/services/database.py to ensure utf8mb4 connection charset
- [X] T042 [P] Add database connection error handling in src/services/database.py with clear error messages per FR-020
- [X] T043 Test backup workflow with dry-run mode to verify no database writes occur
- [X] T044 Validate schema.sql can be executed cleanly on fresh MySQL database
- [X] T045 [P] Add input validation for CLI arguments in src/cli/main.py
- [X] T046 Run full backup test with sample data to verify all requirements met and performance acceptable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 can proceed after Phase 2 - No dependencies on other stories
  - User Story 2 depends on User Story 1 completion (needs working backup to test incremental)
  - User Story 3 can start after User Story 1 (needs backup process to report on)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 completion - requires working backup to add incremental logic
- **User Story 3 (P3)**: Can start after User Story 1 completion - requires backup process to add reporting

### Within Each User Story

- User Story 1: Pagination → Parsing → Mapping → Upsert → Error handling → Rate limiting → Logging → CLI integration
- User Story 2: Database query → Backup orchestration → API parameter → CLI detection → Metadata storage → Upsert logic → Logging
- User Story 3: Statistics tracking → Report generator → Metadata storage → CLI output → JSON format → Error details → Logging

### Parallel Opportunities

- Phase 1: T002, T003, T004, T005 can run in parallel (different files)
- Phase 2: T007, T010, T013, T015 can run in parallel (different files, no dependencies)
- User Story 1: T016, T017 can run in parallel; T020, T021, T022, T023 can run in parallel after T018-T019
- User Story 2: T025 and T029 can run in parallel (database.py different methods)
- User Story 3: T032, T033 can run in parallel initially

---

## Parallel Example: User Story 1

```bash
# Launch initial parsing and pagination together:
Task: "Implement pagination loop in src/services/backup.py"
Task: "Add note parsing logic in src/services/backup.py"

# After core logic is complete, launch these together:
Task: "Implement progress indicator in src/services/backup.py" 
Task: "Add per-note error handling in src/services/backup.py"
Task: "Implement API rate limiting detection and retry logic in src/services/fellow_api.py"
Task: "Add structured logging for all API requests and responses in src/services/fellow_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup - Schema simplification
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) - Service layer refactoring
3. Complete Phase 3: User Story 1 - Initial backup functionality
4. **STOP and VALIDATE**: Run full backup test, verify notes in database
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (incremental backups)
4. Add User Story 3 → Test independently → Deploy/Demo (reporting)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (core backup functionality)
   - Developer B: Can prepare database queries for User Story 2
   - Developer C: Can prepare report structure for User Story 3
3. After User Story 1 complete:
   - Developer B: Complete User Story 2 (incremental)
   - Developer C: Complete User Story 3 (reporting)
   - Developer A: Polish tasks

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable
- Commit after each task or logical group
- This is primarily a **code removal** feature - simplifying by removing unused entities
- All tasks focus on implementation since tests were not requested in specification
- Verify at each checkpoint that backup works end-to-end before proceeding
- Stop at any checkpoint to validate story independently
