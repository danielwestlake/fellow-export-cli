-- Fellow.app Notes-Only Backup Database Schema
-- MySQL 5.7+ / 8.0+
-- Character Set: UTF-8 (utf8mb4) for full Unicode support

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS backup_metadata;

-- Notes Table (standalone, no foreign keys)
CREATE TABLE notes (
    id VARCHAR(255) PRIMARY KEY COMMENT 'Fellow.app note ID',
    content TEXT NOT NULL COMMENT 'Note text content with full Unicode support',
    author_name VARCHAR(500) COMMENT 'Author display name from Fellow.app',
    author_id VARCHAR(255) COMMENT 'Fellow.app user/author ID',
    fellow_created_at DATETIME COMMENT 'Creation timestamp from Fellow.app',
    fellow_updated_at DATETIME COMMENT 'Last update timestamp from Fellow.app',
    created_at DATETIME NOT NULL COMMENT 'Local record creation timestamp',
    updated_at DATETIME NOT NULL COMMENT 'Local record update timestamp',
    INDEX idx_fellow_updated (fellow_updated_at) COMMENT 'Incremental backup queries',
    INDEX idx_author_id (author_id) COMMENT 'Author-based queries'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fellow.app notes backup - standalone note records';

-- Backup Metadata Table (for tracking sync state)
CREATE TABLE backup_metadata (
    key_name VARCHAR(255) PRIMARY KEY COMMENT 'Metadata key identifier',
    value TEXT NOT NULL COMMENT 'Metadata value (JSON or string)',
    updated_at DATETIME NOT NULL COMMENT 'Last update timestamp'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Backup process metadata and sync state tracking';
