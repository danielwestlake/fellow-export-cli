"""Database service for MySQL operations."""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Set
import mysql.connector
from mysql.connector import Error as MySQLError
from contextlib import contextmanager

from src.lib.logger import get_logger
from src.models import Note

logger = get_logger(__name__)


class DatabaseService:
    """MySQL database service with connection management."""
    
    def __init__(self):
        """Initialize database service with configuration from environment."""
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'database': os.getenv('MYSQL_DATABASE', 'fellow_backup'),
            'user': os.getenv('MYSQL_USER', 'fellow_user'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False
        }
        self.connection = None
    
    def connect(self):
        """Establish database connection with proper error handling."""
        try:
            self.connection = mysql.connector.connect(**self.config)
            
            # Verify connection character set
            cursor = self.connection.cursor()
            cursor.execute("SELECT @@character_set_database, @@collation_database")
            charset, collation = cursor.fetchone()
            cursor.close()
            
            if charset != 'utf8mb4':
                logger.warning("database_charset_mismatch", 
                             expected='utf8mb4', 
                             actual=charset,
                             message="Database should use utf8mb4 for full Unicode support")
            
            logger.info("database_connected", 
                       host=self.config['host'], 
                       database=self.config['database'],
                       charset=charset)
        except MySQLError as e:
            error_msg = str(e)
            if "Access denied" in error_msg:
                logger.error("database_authentication_failed", 
                           user=self.config['user'],
                           host=self.config['host'],
                           message="Check MYSQL_USER and MYSQL_PASSWORD in .env")
            elif "Unknown database" in error_msg:
                logger.error("database_not_found",
                           database=self.config['database'],
                           message=f"Create database: CREATE DATABASE {self.config['database']} CHARACTER SET utf8mb4")
            elif "Can't connect" in error_msg:
                logger.error("database_connection_refused",
                           host=self.config['host'],
                           port=self.config['port'],
                           message="Check MySQL is running and host/port are correct")
            else:
                logger.error("database_connection_failed", error=error_msg)
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("database_disconnected")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error("transaction_rolled_back", error=str(e))
            raise
        finally:
            cursor.close()
    
    def upsert_note(self, note: Note):
        """
        Save or update note using upsert pattern with attendees.
        INSERT ... ON DUPLICATE KEY UPDATE handles both new and existing notes.
        """
        now = datetime.utcnow()
        with self.transaction() as cursor:
            query = """
                INSERT INTO notes (
                    id, title, content, content_markdown, event_guid,
                    event_start, event_end, event_is_all_day,
                    author_name, author_id,
                    fellow_created_at, fellow_updated_at,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    content = VALUES(content),
                    content_markdown = VALUES(content_markdown),
                    event_guid = VALUES(event_guid),
                    event_start = VALUES(event_start),
                    event_end = VALUES(event_end),
                    event_is_all_day = VALUES(event_is_all_day),
                    author_name = VALUES(author_name),
                    author_id = VALUES(author_id),
                    fellow_updated_at = VALUES(fellow_updated_at),
                    updated_at = VALUES(updated_at)
            """
            cursor.execute(query, (
                note.id, note.title, note.content, note.content_markdown,
                note.event_guid, note.event_start, note.event_end,
                note.event_is_all_day, note.author_name, note.author_id,
                note.fellow_created_at, note.fellow_updated_at, now, now
            ))
            
            # Delete existing attendees and insert new ones
            cursor.execute("DELETE FROM event_attendees WHERE note_id = %s", (note.id,))
            if note.event_attendees:
                attendee_query = """
                    INSERT INTO event_attendees (note_id, email, created_at)
                    VALUES (%s, %s, %s)
                """
                attendee_data = [(note.id, email, now) for email in note.event_attendees]
                cursor.executemany(attendee_query, attendee_data)
            
            logger.debug("note_upserted", note_id=note.id)
    
    def upsert_notes_batch(self, notes: List[Note]):
        """
        Batch upsert multiple notes for better performance.
        
        Args:
            notes: List of Note objects to upsert
        """
        if not notes:
            return
        
        now = datetime.utcnow()
        with self.transaction() as cursor:
            query = """
                INSERT INTO notes (
                    id, content, author_name, author_id,
                    fellow_created_at, fellow_updated_at,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content),
                    author_name = VALUES(author_name),
                    author_id = VALUES(author_id),
                    fellow_updated_at = VALUES(fellow_updated_at),
                    updated_at = VALUES(updated_at)
            """
            
            data = [
                (
                    note.id, note.content, note.author_name, note.author_id,
                    note.fellow_created_at, note.fellow_updated_at, now, now
                )
                for note in notes
            ]
            
            cursor.executemany(query, data)
            logger.info("notes_batch_upserted", count=len(notes))
    
    def get_last_backup_timestamp(self) -> Optional[datetime]:
        """
        Get the most recent fellow_updated_at timestamp from notes table.
        Used for incremental backup.
        
        Returns:
            Most recent fellow_updated_at datetime or None
        """
        with self.transaction() as cursor:
            query = "SELECT MAX(fellow_updated_at) FROM notes"
            cursor.execute(query)
            result = cursor.fetchone()
            if result and result[0]:
                logger.debug("last_backup_timestamp_retrieved", timestamp=result[0])
                return result[0]
        logger.debug("no_backup_timestamp_found")
        return None
    
    def save_backup_metadata(self, key_name: str, value: str):
        """
        Save backup metadata key-value pair.
        
        Args:
            key_name: Metadata key identifier
            value: Metadata value (can be JSON string)
        """
        now = datetime.utcnow()
        with self.transaction() as cursor:
            query = """
                INSERT INTO backup_metadata (key_name, value, updated_at)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    value = VALUES(value),
                    updated_at = VALUES(updated_at)
            """
            cursor.execute(query, (key_name, value, now))
            logger.debug("backup_metadata_saved", key_name=key_name)
    
    def get_backup_metadata(self, key_name: str) -> Optional[str]:
        """
        Retrieve backup metadata value by key.
        
        Args:
            key_name: Metadata key identifier
            
        Returns:
            Metadata value or None if not found
        """
        with self.transaction() as cursor:
            query = "SELECT value FROM backup_metadata WHERE key_name = %s"
            cursor.execute(query, (key_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
        return None

    def ensure_export_schema(self):
        """Create export-related tables if they don't exist."""
        with self.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_domains (
                    email_domain VARCHAR(255) PRIMARY KEY,
                    client_name VARCHAR(500) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
        logger.info("export_schema_ensured")

    def get_all_notes_with_attendees(
        self, limit: Optional[int] = None
    ) -> List[Note]:
        """Fetch notes joined with attendees, ordered by event_start DESC."""
        with self.transaction() as cursor:
            query = """
                SELECT id, title, content, content_markdown,
                       event_guid, event_start, event_end,
                       event_is_all_day, author_name, author_id,
                       fellow_created_at, fellow_updated_at,
                       created_at, updated_at
                FROM notes
                ORDER BY event_start DESC, fellow_created_at DESC
            """
            if limit:
                query += f" LIMIT {int(limit)}"
            cursor.execute(query)
            rows = cursor.fetchall()

            notes = []
            for row in rows:
                note = Note(
                    id=row[0], title=row[1], content=row[2],
                    content_markdown=row[3], event_guid=row[4],
                    event_start=row[5], event_end=row[6],
                    event_is_all_day=bool(row[7]),
                    author_name=row[8], author_id=row[9],
                    fellow_created_at=row[10],
                    fellow_updated_at=row[11],
                    created_at=row[12], updated_at=row[13]
                )
                notes.append(note)

            # Batch-load attendees for all notes
            if notes:
                note_ids = [n.id for n in notes]
                placeholders = ','.join(['%s'] * len(note_ids))
                cursor.execute(
                    f"SELECT note_id, email FROM event_attendees "
                    f"WHERE note_id IN ({placeholders})",
                    note_ids
                )
                attendee_rows = cursor.fetchall()
                attendees_by_note: Dict[str, List[str]] = {}
                for note_id, email in attendee_rows:
                    attendees_by_note.setdefault(
                        note_id, []
                    ).append(email)
                for note in notes:
                    note.event_attendees = attendees_by_note.get(
                        note.id, []
                    )

            logger.info("notes_fetched_with_attendees", count=len(notes))
            return notes

    def get_distinct_attendee_domains(
        self, exclude_domains: Set[str]
    ) -> List[str]:
        """Get unique email domains from event_attendees."""
        with self.transaction() as cursor:
            cursor.execute("""
                SELECT DISTINCT SUBSTRING_INDEX(email, '@', -1)
                AS domain FROM event_attendees
                ORDER BY domain
            """)
            all_domains = [row[0] for row in cursor.fetchall()]
            return [
                d for d in all_domains
                if d not in exclude_domains
            ]

    def upsert_client_domain(self, domain: str, client_name: str):
        """Insert client domain mapping, skip if already exists."""
        now = datetime.utcnow()
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT IGNORE INTO client_domains
                    (email_domain, client_name, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
            """, (domain, client_name, now, now))

    def get_client_domain_map(self) -> Dict[str, str]:
        """Load all client domain mappings as {domain: client_name}."""
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT email_domain, client_name FROM client_domains"
            )
            return {row[0]: row[1] for row in cursor.fetchall()}
