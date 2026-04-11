-- Migration: Add 'fellow_' prefix to all tables
-- Purpose: Namespace Fellow.app tables to support additional data sources (e.g., Confluence)
-- Date: 2026-04-11
--
-- Run this BEFORE deploying the updated Python code.
-- MySQL automatically updates foreign key references on RENAME.

-- Drop the FK first to avoid issues with rename order
ALTER TABLE event_attendees DROP FOREIGN KEY event_attendees_ibfk_1;

-- Rename all tables
ALTER TABLE notes RENAME TO fellow_notes;
ALTER TABLE event_attendees RENAME TO fellow_event_attendees;
ALTER TABLE backup_metadata RENAME TO fellow_backup_metadata;

-- client_domains may not exist in all environments
ALTER TABLE client_domains RENAME TO fellow_client_domains;

-- Re-add the FK with the new table names
ALTER TABLE fellow_event_attendees
    ADD CONSTRAINT fellow_event_attendees_ibfk_1
    FOREIGN KEY (note_id) REFERENCES fellow_notes(id) ON DELETE CASCADE;
