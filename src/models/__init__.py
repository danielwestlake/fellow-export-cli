"""Base data models for Fellow.app backup."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Note:
    """Standalone note model for Fellow.app backup."""
    id: str
    content: str
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    fellow_created_at: Optional[datetime] = None
    fellow_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
