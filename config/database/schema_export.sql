-- Fellow.app Notes Export - Additional Tables
-- These tables support the markdown export feature.
-- Run after schema.sql. Does not modify existing tables.

-- Client Domain Mapping Table
-- Maps email domains to client/company names for organizing exported notes.
CREATE TABLE IF NOT EXISTS fellow_client_domains (
    email_domain VARCHAR(255) PRIMARY KEY COMMENT 'Email domain (e.g., acme.com)',
    client_name VARCHAR(500) NOT NULL COMMENT 'Human-readable client/company name',
    created_at DATETIME NOT NULL COMMENT 'Record creation timestamp',
    updated_at DATETIME NOT NULL COMMENT 'Record update timestamp'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Maps attendee email domains to client names for Fellow note export';
