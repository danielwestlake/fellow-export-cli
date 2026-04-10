"""Base data models for Fellow.app backup."""
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Note:
    """Standalone note model for Fellow.app backup."""
    id: str
    title: Optional[str] = None
    content: Optional[str] = None
    content_markdown: Optional[str] = None
    event_guid: Optional[str] = None
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
    event_is_all_day: bool = False
    event_attendees: List[str] = field(default_factory=list)  # List of email addresses
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    fellow_created_at: Optional[datetime] = None
    fellow_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ExportReport:
    """Report for markdown export operation."""
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = 'running'
    notes_exported: int = 0
    notes_skipped: int = 0
    clients_found: int = 0
    uncategorized: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, note_id: str, error: str):
        self.errors.append({
            'note_id': note_id,
            'error': error,
        })

    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (
                self.end_time - self.start_time
            ).total_seconds()
        return (
            datetime.utcnow() - self.start_time
        ).total_seconds()

    def format_summary(self) -> str:
        duration = self.duration_seconds
        dur_str = f"{int(duration // 60)}m {int(duration % 60)}s"
        lines = [
            "",
            "Export Summary",
            "==============",
            f"Duration: {dur_str}",
            f"Status: {self.status.upper()}",
            "",
            "Statistics:",
            f"  - Notes exported: {self.notes_exported}",
            f"  - Notes skipped: {self.notes_skipped}",
            f"  - Clients found: {self.clients_found}",
            f"  - Uncategorized: {self.uncategorized}",
            f"  - Errors: {len(self.errors)}",
            "",
        ]
        if self.errors:
            lines.append(
                f"Error Details ({len(self.errors)} errors):"
            )
            for err in self.errors[:5]:
                lines.append(
                    f"  - Note {err['note_id']}: {err['error']}"
                )
            if len(self.errors) > 5:
                lines.append(
                    f"  ... and {len(self.errors) - 5} more"
                )
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({
            'status': self.status,
            'notes_exported': self.notes_exported,
            'notes_skipped': self.notes_skipped,
            'clients_found': self.clients_found,
            'uncategorized': self.uncategorized,
            'errors': self.errors,
            'duration_seconds': self.duration_seconds,
        }, indent=2)
