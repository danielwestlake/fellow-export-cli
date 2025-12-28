"""Backup orchestration service."""
import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from src.lib.logger import get_logger
from src.services.fellow_api import FellowAPIClient
from src.services.database import DatabaseService
from src.models import Note

logger = get_logger(__name__)


@dataclass
class BackupReport:
    """Backup execution report for notes-only backup."""
    mode: str  # 'full' or 'incremental'
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = 'running'  # 'running', 'success', 'failed'
    
    notes_total: int = 0
    notes_new: int = 0
    notes_updated: int = 0
    notes_errors: int = 0
    
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate backup duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def add_error(self, note_id: str, error: str):
        """Record an error for a specific note."""
        self.errors.append({
            'note_id': note_id,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.notes_errors += 1
    
    def format_summary(self) -> str:
        """Format human-readable summary report."""
        duration_str = f"{int(self.duration_seconds // 60)}m {int(self.duration_seconds % 60)}s"
        
        summary = f"""
Backup Summary
==============
Mode: {self.mode.upper()}
Duration: {duration_str}
Status: {self.status.upper()}

Statistics:
  - Total notes processed: {self.notes_total}
  - New notes: {self.notes_new}
  - Updated notes: {self.notes_updated}
  - Errors: {self.notes_errors}

"""
        
        if self.errors:
            summary += f"Error Details ({len(self.errors)} errors):\n"
            for err in self.errors[:5]:  # Show first 5 errors
                summary += f"  - Note {err['note_id']}: {err['error']}\n"
            if len(self.errors) > 5:
                summary += f"  ... and {len(self.errors) - 5} more errors\n"
        else:
            summary += "No errors encountered.\n"
        
        return summary
    
    def to_json(self) -> str:
        """Format report as JSON."""
        return json.dumps({
            'mode': self.mode,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'statistics': {
                'notes_total': self.notes_total,
                'notes_new': self.notes_new,
                'notes_updated': self.notes_updated,
                'notes_errors': self.notes_errors
            },
            'errors': self.errors
        }, indent=2)


class BackupService:
    """Orchestrates notes-only backup workflow."""
    
    def __init__(self, api_client: FellowAPIClient, db_service: DatabaseService):
        """
        Initialize backup service.
        
        Args:
            api_client: Fellow.app API client
            db_service: Database service
        """
        self.api = api_client
        self.db = db_service
    
    def backup_notes(
        self,
        full: bool = False,
        dry_run: bool = False
    ) -> BackupReport:
        """
        Execute notes-only backup.
        
        Args:
            full: Force full backup (ignore incremental timestamp)
            dry_run: Preview operations without database commits
            
        Returns:
            Backup report with statistics and errors
        """
        mode = 'full' if full else 'incremental'
        logger.info("backup_started", mode=mode, dry_run=dry_run)
        
        report = BackupReport(
            mode=mode,
            start_time=datetime.utcnow()
        )
        
        try:
            # Determine last backup timestamp for incremental mode
            updated_after = None
            if not full:
                updated_after = self.db.get_last_backup_timestamp()
                if updated_after:
                    logger.info("incremental_backup", last_backup=updated_after.isoformat())
                else:
                    logger.info("no_previous_backup_found", mode='full')
                    report.mode = 'full'
            
            # Fetch all notes with pagination
            all_notes = self._fetch_all_notes(updated_after)
            logger.info("notes_fetched", count=len(all_notes))
            
            report.notes_total = len(all_notes)
            
            # Process and save notes
            if not dry_run:
                self._save_notes(all_notes, report)
                
                # Save backup metadata
                summary = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'mode': report.mode,
                    'notes_total': report.notes_total,
                    'notes_new': report.notes_new,
                    'notes_updated': report.notes_updated,
                    'notes_errors': report.notes_errors
                }
                self.db.save_backup_metadata('last_backup_summary', json.dumps(summary))
            else:
                logger.info("dry_run_mode", notes_would_save=len(all_notes))
                report.notes_new = len(all_notes)
            
            report.status = 'success'
            report.end_time = datetime.utcnow()
            
            logger.info("backup_completed", 
                       duration=report.duration_seconds,
                       notes_total=report.notes_total,
                       errors=report.notes_errors)
            
        except Exception as e:
            report.status = 'failed'
            report.end_time = datetime.utcnow()
            logger.error("backup_failed", error=str(e))
            raise
        
        return report
    
    def _fetch_all_notes(self, updated_after: Optional[datetime] = None) -> List[Note]:
        """
        Fetch all notes from API with cursor-based pagination.
        
        Args:
            updated_after: Optional filter for incremental backup
            
        Returns:
            List of all Note objects from all pages
        """
        all_notes = []
        cursor = None  # Start with None for first page
        page_num = 1
        page_size = 50  # API max
        
        while True:
            try:
                response = self.api.fetch_notes(
                    cursor=cursor,
                    page_size=page_size,
                    updated_after=updated_after
                )
                
                # Parse nested structure: {"notes": {"data": [...], "page_info": {...}}}
                notes_container = response.get('notes', {})
                notes_data = notes_container.get('data', []) if isinstance(notes_container, dict) else []
                page_info = notes_container.get('page_info', {}) if isinstance(notes_container, dict) else {}
                
                # Parse notes from API response
                for note_data in notes_data:
                    try:
                        note = self._parse_note(note_data)
                        all_notes.append(note)
                    except Exception as e:
                        logger.error("note_parsing_failed", 
                                   note_id=note_data.get('id', 'unknown'),
                                   error=str(e))
                
                logger.info("notes_page_fetched", 
                           page=page_num,
                           count=len(notes_data),
                           total_so_far=len(all_notes))
                
                # Get next cursor from page_info
                next_cursor = page_info.get('cursor')
                
                # Stop if cursor is None (last page) or no data returned
                if next_cursor is None or len(notes_data) == 0:
                    logger.info("pagination_complete", 
                               reason="no_cursor" if next_cursor is None else "no_data",
                               total_notes=len(all_notes))
                    break
                
                # Continue with next page
                cursor = next_cursor
                page_num += 1
                
            except Exception as e:
                logger.error("notes_fetch_failed", page=page_num, error=str(e))
                break
        
        return all_notes
    
    def _parse_note(self, note_data: Dict[str, Any]) -> Note:
        """
        Parse note from API response data.
        
        Args:
            note_data: Raw note data from API
            
        Returns:
            Note object
        """
        author = note_data.get('author', {})
        
        # Parse timestamps
        fellow_created_at = None
        if note_data.get('created_at'):
            try:
                fellow_created_at = datetime.fromisoformat(
                    note_data['created_at'].replace('Z', '+00:00')
                )
            except Exception as e:
                logger.warning("failed_to_parse_created_at", 
                             note_id=note_data['id'],
                             error=str(e))
        
        fellow_updated_at = None
        if note_data.get('updated_at'):
            try:
                fellow_updated_at = datetime.fromisoformat(
                    note_data['updated_at'].replace('Z', '+00:00')
                )
            except Exception as e:
                logger.warning("failed_to_parse_updated_at",
                             note_id=note_data['id'],
                             error=str(e))
        
        # Parse event timestamps
        event_start = None
        if note_data.get('event_start'):
            try:
                event_start = datetime.fromisoformat(
                    note_data['event_start'].replace('Z', '+00:00')
                )
            except Exception as e:
                logger.warning("failed_to_parse_event_start",
                             note_id=note_data['id'],
                             error=str(e))
        
        event_end = None
        if note_data.get('event_end'):
            try:
                event_end = datetime.fromisoformat(
                    note_data['event_end'].replace('Z', '+00:00')
                )
            except Exception as e:
                logger.warning("failed_to_parse_event_end",
                             note_id=note_data['id'],
                             error=str(e))
        
        # Parse event_attendees (list of dicts with email keys)
        event_attendees = []
        if note_data.get('event_attendees'):
            event_attendees = [
                attendee.get('email') 
                for attendee in note_data['event_attendees']
                if attendee.get('email')
            ]
        
        # Extract author fields once
        author_dict = author if isinstance(author, dict) else {}
        
        return Note(
            id=note_data['id'],
            title=note_data.get('title'),
            content=note_data.get('content'),
            content_markdown=note_data.get('content_markdown'),
            event_guid=note_data.get('event_guid'),
            event_start=event_start,
            event_end=event_end,
            event_is_all_day=note_data.get('event_is_all_day'),
            event_attendees=event_attendees,
            author_name=author_dict.get('name'),
            author_id=author_dict.get('id'),
            fellow_created_at=fellow_created_at,
            fellow_updated_at=fellow_updated_at
        )
    
    def _save_notes(self, notes: List[Note], report: BackupReport):
        """
        Save notes to database and update report statistics.
        
        Args:
            notes: List of Note objects to save
            report: Backup report to update
        """
        for note in notes:
            try:
                # Check if note exists for accurate statistics
                # For simplicity, we'll count all as new in full mode
                # and all as updated in incremental mode
                self.db.upsert_note(note)
                
                if report.mode == 'full':
                    report.notes_new += 1
                else:
                    report.notes_updated += 1
                    
            except Exception as e:
                logger.error("note_save_failed", note_id=note.id, error=str(e))
                report.add_error(note.id, str(e))
