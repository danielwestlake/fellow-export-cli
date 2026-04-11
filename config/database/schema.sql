-- Fellow.app Notes-Only Backup Database Schema
-- MySQL 5.7+ / 8.0+
-- Character Set: UTF-8 (utf8mb4) for full Unicode support

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS fellow_notes;
DROP TABLE IF EXISTS fellow_backup_metadata;

-- Notes Table (standalone, no foreign keys)
CREATE TABLE fellow_notes (
    id VARCHAR(255) PRIMARY KEY COMMENT 'Fellow.app note ID',
    title VARCHAR(1000) COMMENT 'Note/meeting title',
    content TEXT COMMENT 'Note text content with full Unicode support',
    content_markdown TEXT COMMENT 'Note content in markdown format',
    event_guid VARCHAR(500) COMMENT 'Calendar event GUID',
    event_start DATETIME COMMENT 'Event start time',
    event_end DATETIME COMMENT 'Event end time',
    event_is_all_day BOOLEAN DEFAULT FALSE COMMENT 'All-day event flag',
    author_name VARCHAR(500) COMMENT 'Author display name from Fellow.app',
    author_id VARCHAR(255) COMMENT 'Fellow.app user/author ID',
    fellow_created_at DATETIME COMMENT 'Creation timestamp from Fellow.app',
    fellow_updated_at DATETIME COMMENT 'Last update timestamp from Fellow.app',
    created_at DATETIME NOT NULL COMMENT 'Local record creation timestamp',
    updated_at DATETIME NOT NULL COMMENT 'Local record update timestamp',
    INDEX idx_fellow_updated (fellow_updated_at) COMMENT 'Incremental backup queries',
    INDEX idx_author_id (author_id) COMMENT 'Author-based queries',
    INDEX idx_event_start (event_start) COMMENT 'Event time queries',
    INDEX idx_event_guid (event_guid) COMMENT 'Calendar event lookups'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fellow.app notes backup - standalone note records';

-- Event Attendees Table (many-to-many relationship)
CREATE TABLE fellow_event_attendees (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Auto-increment ID',
    note_id VARCHAR(255) NOT NULL COMMENT 'Reference to note',
    email VARCHAR(500) NOT NULL COMMENT 'Attendee email address',
    created_at DATETIME NOT NULL COMMENT 'Local record creation timestamp',
    INDEX idx_note_id (note_id) COMMENT 'Note lookups',
    INDEX idx_email (email) COMMENT 'Email lookups',
    FOREIGN KEY (note_id) REFERENCES fellow_notes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Event attendees for Fellow notes';

-- Backup Metadata Table (for tracking sync state)
CREATE TABLE fellow_backup_metadata (
    key_name VARCHAR(255) PRIMARY KEY COMMENT 'Metadata key identifier',
    value TEXT NOT NULL COMMENT 'Metadata value (JSON or string)',
    updated_at DATETIME NOT NULL COMMENT 'Last update timestamp'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fellow backup process metadata and sync state tracking';
