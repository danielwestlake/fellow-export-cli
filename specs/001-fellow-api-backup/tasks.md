---

description: "Task list for Fellow.app API Backup feature implementation"
---

# Tasks: Fellow.app API Backup

**Input**: Design documents from `/specs/001-fellow-api-backup/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Per constitution requirements, test coverage of 80% for critical paths is mandatory. Test tasks are included in Phase 6 after implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `config/` at repository root
- Paths assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure with src/, config/, docs/ folders
- [X] T002 Initialize Python project with requirements.txt (httpx>=0.25.0, mysql-connector-python>=8.2.0, click>=8.1.0, structlog>=23.2.0, python-dotenv>=1.0.0)
- [X] T003 [P] Create .env.example file with FELLOW_API_TOKEN, FELLOW_API_BASE_URL, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD, LOG_LEVEL placeholders
- [X] T004 [P] Create .gitignore file to exclude .env, venv/, __pycache__/, logs/
- [X] T005 [P] Create README.md with setup and usage instructions based on quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create MySQL database schema in config/database/schema.sql with workspaces, meetings, participants, meeting_participants, notes, action_items, backup_metadata tables per data-model.md
- [X] T007 [P] Create base data models in src/models/__init__.py with Workspace, Meeting, Participant, Note, ActionItem classes
- [X] T008 [P] Implement structured logging utility in src/lib/logger.py using structlog with JSON output
- [X] T009 [P] Implement rate limiter utility in src/lib/rate_limiter.py with exponential backoff and configurable request rate
- [X] T010 [P] Implement retry logic utility in src/lib/retry.py with exponential backoff for network errors and 5xx responses
- [X] T011 Create database service base in src/services/database.py with MySQL connection management and transaction support
- [X] T012 Create Fellow.app API client base in src/services/fellow_api.py with authentication, headers, and base URL configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Complete Data Export (Priority: P1) 🎯 MVP

**Goal**: Extract all meeting notes, action items, and metadata from Fellow.app and store them in MySQL database

**Independent Test**: Connect to Fellow.app API, retrieve a sample of meetings, verify data is stored correctly in MySQL with complete meeting details, notes, action items, and participants

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement Workspace model with id, name, created_at, updated_at in src/models/workspace.py
- [X] T014 [P] [US1] Implement Meeting model with id, workspace_id, title, meeting_date, duration_minutes, status, fellow_created_at, fellow_updated_at, created_at, updated_at in src/models/meeting.py
- [X] T015 [P] [US1] Implement Participant model with id, name, email, created_at, updated_at in src/models/participant.py
- [X] T016 [P] [US1] Implement Note model with id, meeting_id, content, author_id, note_order, fellow_created_at, fellow_updated_at, created_at, updated_at in src/models/note.py
- [X] T017 [P] [US1] Implement ActionItem model with id, meeting_id, description, assignee_id, due_date, completed, completed_at, fellow_created_at, fellow_updated_at, created_at, updated_at in src/models/action_item.py
- [X] T018 [US1] Implement list_workspaces API method in src/services/fellow_api.py with pagination support per contracts/fellow-api.md
- [X] T019 [US1] Implement list_meetings API method in src/services/fellow_api.py with workspace_id, pagination, and updated_since query parameters per contracts/fellow-api.md
- [X] T020 [US1] Implement get_meeting_details API method in src/services/fellow_api.py with meeting_id parameter per contracts/fellow-api.md
- [X] T021 [US1] Implement list_notes API method in src/services/fellow_api.py with meeting_id and pagination parameters per contracts/fellow-api.md
- [X] T022 [US1] Implement list_action_items API method in src/services/fellow_api.py with meeting_id and pagination parameters per contracts/fellow-api.md
- [X] T023 [US1] Implement list_users API method in src/services/fellow_api.py with workspace_id and pagination parameters per contracts/fellow-api.md
- [X] T024 [US1] Add rate limiting integration to fellow_api.py using rate_limiter.py to respect API limits per contracts/fellow-api.md
- [X] T025 [US1] Add retry logic integration to fellow_api.py using retry.py for 429, 5xx responses per contracts/fellow-api.md
- [X] T025a [US1] Add structured logging to fellow_api.py to log all API requests and responses (method, URL, status code, response time) per FR-011
- [X] T026 [US1] Implement save_workspace method in src/services/database.py with INSERT ... ON DUPLICATE KEY UPDATE for upsert
- [X] T027 [US1] Implement save_meeting method in src/services/database.py with INSERT ... ON DUPLICATE KEY UPDATE for upsert
- [X] T028 [US1] Implement save_participant method in src/services/database.py with INSERT ... ON DUPLICATE KEY UPDATE for upsert
- [X] T029 [US1] Implement save_meeting_participant method in src/services/database.py for meeting-participant relationships
- [X] T030 [US1] Implement save_note method in src/services/database.py with INSERT ... ON DUPLICATE KEY UPDATE for upsert
- [X] T031 [US1] Implement save_action_item method in src/services/database.py with INSERT ... ON DUPLICATE KEY UPDATE for upsert
- [X] T032 [US1] Create backup orchestration service in src/services/backup.py with full backup workflow
- [X] T033 [US1] Implement full backup workflow in src/services/backup.py: fetch workspaces → fetch meetings → fetch details → fetch notes/action items → save to database
- [X] T034 [US1] Add transaction support to backup.py to ensure data integrity during backup operations
- [X] T035 [US1] Implement CLI entry point in src/cli/main.py using click with backup command and --workspace-id flag
- [X] T036 [US1] Add --all-workspaces flag to CLI main.py to backup all workspaces
- [X] T037 [US1] Add --verbose and --quiet flags to CLI main.py for log level control
- [X] T038 [US1] Implement error handling in backup.py for API failures (continue processing remaining items per FR-012)
- [X] T039 [US1] Add UTF-8 encoding support in database.py to preserve special characters per FR-017
- [X] T040 [US1] Add structured logging throughout backup.py for backup workflow progress, errors, and summary statistics per FR-011, FR-014, FR-015

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - full backup of Fellow.app data to MySQL database works end-to-end

---

## Phase 4: User Story 2 - Incremental Updates (Priority: P2)

**Goal**: Run backup process multiple times to capture new or updated meetings, ensuring backup stays current without duplicating existing records

**Independent Test**: Run initial backup, add/modify meetings in Fellow.app, run backup again and verify only new/changed data is processed without duplicating existing records

### Implementation for User Story 2

- [X] T041 [P] [US2] Create backup_metadata table operations in src/services/database.py for storing/retrieving last_sync_timestamp
- [X] T042 [US2] Implement get_last_sync_timestamp method in src/services/database.py
- [X] T043 [US2] Implement save_sync_timestamp method in src/services/database.py
- [X] T044 [US2] Add incremental backup workflow to src/services/backup.py using updated_since parameter
- [X] T045 [US2] Implement incremental backup logic in backup.py: retrieve last_sync_timestamp → query API with updated_since → upsert changed records → update timestamp
- [X] T046 [US2] Add --incremental flag to CLI main.py to trigger incremental backup mode
- [X] T047 [US2] Add --full flag to CLI main.py to force full backup even if last sync exists
- [X] T048 [US2] Add detection logic in backup.py to auto-select incremental mode if last_sync_timestamp exists
- [X] T049 [US2] Update structured logging in backup.py to indicate incremental vs full backup mode

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - incremental backups efficiently process only changed data

---

## Phase 5: User Story 3 - Data Verification Report (Priority: P3)

**Goal**: Receive a summary report after each backup showing what data was retrieved and any errors encountered

**Independent Test**: Run backup process and verify that a summary report is generated showing counts of meetings, notes, action items, and any failures with error details

### Implementation for User Story 3

- [X] T050 [P] [US3] Create backup report model in src/models/backup_report.py with counts, duration, errors list
- [X] T051 [US3] Implement report tracking in src/services/backup.py to collect statistics during backup execution
- [X] T052 [US3] Implement error collection in backup.py to capture failed items with meeting_id and error reason
- [X] T053 [US3] Implement report formatting utility in src/lib/report_formatter.py to generate human-readable summary
- [X] T054 [US3] Add report generation at end of backup workflow in backup.py with total counts, duration, error summary
- [X] T055 [US3] Implement report CLI command in src/cli/main.py to generate summary of backed-up data for a workspace
- [X] T056 [US3] Add --json flag to report command in main.py for machine-readable output
- [X] T057 [US3] Update backup.py to output summary report to stdout after backup completion per FR-015
- [X] T058 [US3] Add progress indicators in backup.py using tqdm or rich library per FR-014

**Checkpoint**: All user stories should now be independently functional - complete backup system with incremental updates and comprehensive reporting

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T059 [P] Add list-workspaces CLI command in src/cli/main.py to discover available workspaces
- [X] T060 [P] Add verify CLI command in src/cli/main.py to check specific meeting backup with --meeting-id flag
- [X] T061 [P] Add test-connection CLI command in src/cli/main.py to validate API credentials and database connection
- [X] T061a Add --dry-run flag to CLI main.py backup command to preview operations without database commits per Constitution Principle III
- [X] T062 [P] Create detailed documentation in docs/README.md covering setup, usage, troubleshooting based on quickstart.md
- [X] T063 Code review and refactoring for error handling consistency across all services
- [X] T064 Add timezone handling in models to ensure all timestamps stored in UTC per FR-016
- [ ] T065 Performance optimization: implement concurrent API requests in backup.py within rate limits
- [ ] T066 Add database connection pooling in database.py for improved performance
- [X] T067 Validate implementation against quickstart.md scenarios
- [X] T068 Final security review: ensure no credentials logged, parameterized queries used

---

## Phase 7: Testing (Constitution Requirement)

**Purpose**: Achieve 80% test coverage for critical paths per constitution quality standards

- [X] T069 [P] Create contract tests in tests/contract/fellow_api_test.py to verify API integration behavior per contracts/fellow-api.md
- [X] T070 [P] Create database integration tests in tests/integration/database_test.py to validate schema, transactions, and constraints
- [X] T071 [P] Create unit tests in tests/unit/models_test.py for all model validation logic
- [ ] T072 [P] Create unit tests in tests/unit/services/fellow_api_test.py for API client with mocked responses
- [ ] T073 [P] Create unit tests in tests/unit/services/database_test.py for database operations with test database
- [ ] T074 [P] Create unit tests in tests/unit/services/backup_test.py for backup orchestration logic
- [X] T075 [P] Create unit tests in tests/unit/lib_test.py for rate limiter, retry logic, and logger utilities
- [X] T076 Create end-to-end test in tests/integration/backup_e2e_test.py that executes full backup against test data and verifies output
- [ ] T077 Create end-to-end test for incremental backup mode verifying only changed data is updated
- [ ] T078 Create end-to-end test for dry-run mode verifying no database changes occur
- [ ] T079 Run pytest coverage report and verify 80% coverage on src/services/, src/models/, src/lib/
- [ ] T080 Add CI configuration (if applicable) to run tests automatically

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1) can start after Foundational
  - User Story 2 (P2) depends on User Story 1 completion (needs backup system to exist)
  - User Story 3 (P3) can run in parallel with US2, or after US1 (only depends on backup workflow existing)
- **Polish (Phase 6)**: Depends on all user stories being complete
- **Testing (Phase 7)**: Can start in parallel with implementation or after Phase 6 - constitution requires 80% coverage

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Builds complete backup system.
- **User Story 2 (P2)**: Depends on User Story 1 - Extends backup system with incremental mode
- **User Story 3 (P3)**: Depends on User Story 1 - Adds reporting to backup system. Can be parallel with US2 if staffed.

### Within Each User Story

- Models can be created in parallel (all marked [P])
- API client methods can be built in parallel after models exist
- Database service methods can be built in parallel after models exist
- Backup orchestration requires API client and database methods to be complete
- CLI commands built after backup service is functional

### Parallel Opportunities

- Phase 1: All tasks marked [P] can run in parallel (T003, T004, T005)
- Phase 2: All tasks marked [P] can run in parallel (T007, T008, T009, T010) after T006 completes
- User Story 1: All model tasks (T013-T017) can run in parallel
- User Story 1: All API client methods (T018-T023) can run in parallel after models
- User Story 1: All database methods (T026-T031) can run in parallel after models
- User Story 2: T041 and T042 can run in parallel
- User Story 3: T050 and T053 can run in parallel
- Phase 6: All tasks marked [P] can run in parallel (T059-T062)
- Phase 7: All test tasks marked [P] can run in parallel (T069-T075) after implementation complete

---

## Parallel Example: User Story 1

```bash
# Launch all model creation together:
Task: "Implement Workspace model in src/models/workspace.py"
Task: "Implement Meeting model in src/models/meeting.py"
Task: "Implement Participant model in src/models/participant.py"
Task: "Implement Note model in src/models/note.py"
Task: "Implement ActionItem model in src/models/action_item.py"

# Once models complete, launch all API methods together:
Task: "Implement list_workspaces API method in src/services/fellow_api.py"
Task: "Implement list_meetings API method in src/services/fellow_api.py"
Task: "Implement get_meeting_details API method in src/services/fellow_api.py"
Task: "Implement list_notes API method in src/services/fellow_api.py"
Task: "Implement list_action_items API method in src/services/fellow_api.py"
Task: "Implement list_users API method in src/services/fellow_api.py"

# Simultaneously, launch all database methods:
Task: "Implement save_workspace method in src/services/database.py"
Task: "Implement save_meeting method in src/services/database.py"
Task: "Implement save_participant method in src/services/database.py"
Task: "Implement save_note method in src/services/database.py"
Task: "Implement save_action_item method in src/services/database.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently by running full backup and verifying data in MySQL
5. Deploy/demo if ready - team has working backup solution

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Complete backup system)
3. Add User Story 2 → Test independently → Deploy/Demo (Incremental updates added)
4. Add User Story 3 → Test independently → Deploy/Demo (Reporting added)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (full backup implementation)
   - Developer B: Can start on User Story 3 models/utilities (runs parallel, integrates after US1)
3. After User Story 1 complete:
   - Developer A: User Story 2 (incremental backup)
   - Developer B: User Story 3 (reporting integration)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests not included as not explicitly requested in specification
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Database schema (T006) is foundational - all other work depends on it
- API client and database services are foundational - user stories depend on them
- FR-010 (avoid duplicates) addressed through upsert operations in all save methods
- FR-011 (logging) addressed through structured logging in T008, T040
- FR-012 (graceful error handling) addressed in T038
- FR-013 (rate limiting) addressed in T009, T024
- FR-014 (progress indicators) addressed in T058
- FR-015 (summary report) addressed in User Story 3
- FR-016 (timezone handling) addressed in T064
- FR-017 (special characters) addressed in T039

---

## Summary

- **Total Tasks**: 68
- **Setup Phase**: 5 tasks
- **Foundational Phase**: 7 tasks (CRITICAL - blocks everything)
- **User Story 1 (P1)**: 28 tasks - Complete data export (MVP)
- **User Story 2 (P2)**: 9 tasks - Incremental updates
- **User Story 3 (P3)**: 9 tasks - Data verification reporting
- **Polish Phase**: 10 tasks
- **Parallel Opportunities**: 24 tasks marked [P]
- **MVP Scope**: Phase 1 + Phase 2 + Phase 3 (40 tasks total for working backup system)
- **Independent Test Criteria**: Each user story has clear test scenario in phase header
