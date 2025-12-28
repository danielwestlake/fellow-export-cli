# Feature Specification: Fellow.app Notes-Only Backup

**Feature Branch**: `002-notes-only-backup`  
**Created**: 2025-12-28  
**Status**: Draft  
**Input**: User description: "Simplify the Fellow.app backup feature to ONLY backup notes using the POST /api/v1/notes endpoint. Remove all references to meetings, workspaces, action items, and streams."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initial Notes Backup (Priority: P1)

As a team administrator, I need to extract all notes from Fellow.app using the POST /api/v1/notes endpoint and store them in a MySQL database so that we retain access to our historical notes data.

**Why this priority**: This is the core requirement - preserving all notes data is the primary value. Without this, there is no backup solution.

**Independent Test**: Can be fully tested by connecting to Fellow.app API with valid credentials, calling POST /api/v1/notes endpoint with pagination, and verifying all notes are stored in MySQL with complete content, author information, and timestamps. Delivers immediate value by creating a complete backup of all notes.

**Acceptance Scenarios**:

1. **Given** valid Fellow.app API credentials, **When** the backup process is initiated, **Then** all accessible notes are retrieved from the POST /api/v1/notes endpoint and stored in the MySQL notes table
2. **Given** notes exist in Fellow.app, **When** the backup completes, **Then** the database contains complete note records with id, content, author_name, author_id, fellow_created_at, fellow_updated_at, created_at, and updated_at fields
3. **Given** notes span multiple pages in the API response, **When** the backup runs, **Then** pagination is handled automatically and all pages of notes are retrieved
4. **Given** a backup has completed successfully, **When** querying the MySQL database, **Then** note content can be retrieved and displayed correctly with proper UTF-8 encoding

---

### User Story 2 - Incremental Updates (Priority: P2)

As a team administrator, I want to run the backup process multiple times to capture any new or updated notes based on the fellow_updated_at timestamp, so that the backup stays current without processing unchanged data.

**Why this priority**: Enables efficient ongoing backups during transition period. Less critical than initial backup but important for keeping data current without unnecessary API load.

**Independent Test**: Can be tested by running an initial backup, modifying notes in Fellow.app, then running the backup again and verifying only notes with fellow_updated_at timestamps newer than the last backup are processed or updated.

**Acceptance Scenarios**:

1. **Given** an existing backup in the database with known fellow_updated_at timestamps, **When** the incremental backup runs, **Then** only notes modified since the last backup are retrieved and updated in the database
2. **Given** a note has been updated in Fellow.app since the last backup, **When** the incremental backup completes, **Then** the database reflects the latest version with updated content and fellow_updated_at timestamp
3. **Given** no notes have changed since the last backup, **When** the incremental backup runs, **Then** no API calls are made beyond the initial check and the process completes quickly

---

### User Story 3 - Backup Verification Report (Priority: P3)

As a team administrator, I want to receive a summary report after each backup showing total notes processed, new notes added, existing notes updated, and any errors encountered, so that I can verify the backup completed successfully.

**Why this priority**: Provides confidence in backup integrity but the backup itself is valuable without detailed reporting. Can be added after core functionality is working.

**Independent Test**: Can be tested by running the backup process and verifying a summary report is generated showing accurate counts that match database queries of notes processed.

**Acceptance Scenarios**:

1. **Given** the backup process has completed, **When** reviewing the report, **Then** it shows total notes processed, count of new notes added, and count of existing notes updated
2. **Given** some notes failed to backup due to API errors, **When** reviewing the report, **Then** it lists which notes failed with their IDs and error messages
3. **Given** rate limiting was encountered during backup, **When** reviewing the report, **Then** it shows retry attempts and successful recovery from rate limit delays

---

### Edge Cases

- What happens when the Fellow.app API is temporarily unavailable or returns 5xx errors?
- How does the system handle rate limiting (429 status) from the Fellow.app API?
- What happens if database connection is lost during backup?
- How does the system handle notes with very large content (multi-megabyte text)?
- What happens if API credentials become invalid mid-backup?
- How are notes with special characters, emojis, or non-Latin scripts preserved?
- What happens if the same note is updated multiple times between backup runs?
- How does the system handle API timeout errors for individual requests?
- What happens if pagination parameters change between requests during a single backup run?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate with Fellow.app API using provided credentials
- **FR-002**: System MUST retrieve notes using only the POST /api/v1/notes endpoint
- **FR-003**: System MUST handle pagination when the POST /api/v1/notes endpoint returns paginated results
- **FR-004**: System MUST extract and store note id from the API response
- **FR-005**: System MUST extract and store note content with proper UTF-8 encoding to preserve all characters
- **FR-006**: System MUST extract and store author_name from the note response
- **FR-007**: System MUST extract and store author_id from the note response
- **FR-008**: System MUST extract and store fellow_created_at timestamp from the note response
- **FR-009**: System MUST extract and store fellow_updated_at timestamp from the note response
- **FR-010**: System MUST store notes in MySQL database with schema: id, content, author_name, author_id, fellow_created_at, fellow_updated_at, created_at, updated_at
- **FR-011**: System MUST use fellow_updated_at timestamps to identify notes that need updating during incremental backups
- **FR-012**: System MUST update existing note records when a note with matching id is retrieved again with a newer fellow_updated_at timestamp
- **FR-013**: System MUST avoid creating duplicate records for the same note id
- **FR-014**: System MUST respect Fellow.app API rate limits and implement automatic retry with exponential backoff when rate limited
- **FR-015**: System MUST log all API requests and responses for troubleshooting
- **FR-016**: System MUST handle API errors gracefully and continue processing remaining notes when individual requests fail
- **FR-017**: System MUST provide progress indicators showing number of notes processed during backup
- **FR-018**: System MUST generate a summary report showing total notes processed, new notes added, existing notes updated, and any errors encountered
- **FR-019**: System MUST preserve original fellow_created_at and fellow_updated_at timestamps without timezone conversion
- **FR-020**: System MUST handle database connection failures with appropriate error messages

### Key Entities

- **Note**: Core entity representing a single note from Fellow.app. Contains text content, author identification (name and ID), timestamps from Fellow.app (fellow_created_at, fellow_updated_at), and local database timestamps (created_at, updated_at). The id field serves as the unique identifier matching Fellow.app's note id.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All notes from Fellow.app are successfully retrieved using the POST /api/v1/notes endpoint and stored in MySQL with 100% data integrity verified by sample audits
- **SC-002**: Backup process completes for 1000 notes in under 10 minutes assuming normal API response times
- **SC-003**: Incremental backup correctly identifies and updates only notes with newer fellow_updated_at timestamps, processing in under 30% of full backup time
- **SC-004**: System successfully handles API rate limits without data loss or manual intervention required
- **SC-005**: Zero data corruption in note content, including preservation of special characters, emojis, and non-Latin scripts
- **SC-006**: Summary report provides accurate counts matching database queries of actual notes processed
- **SC-007**: Database queries to retrieve backed-up notes return results in under 2 seconds for typical queries
- **SC-008**: Team administrator can successfully retrieve any historical note from the database within 5 minutes
