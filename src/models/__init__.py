"""Base data models for Fellow.app backup."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


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
