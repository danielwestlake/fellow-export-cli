"""Unit tests for data models."""
import pytest
from datetime import datetime
from src.models import Workspace, Meeting, Participant, Note, ActionItem


def test_workspace_creation():
    """Test workspace model creation."""
    workspace = Workspace(
        id='ws_test123',
        name='Test Workspace'
    )
    assert workspace.id == 'ws_test123'
    assert workspace.name == 'Test Workspace'


def test_meeting_creation():
    """Test meeting model creation."""
    meeting_date = datetime(2025, 12, 24, 10, 0, 0)
    meeting = Meeting(
        id='mtg_test123',
        workspace_id='ws_test123',
        title='Test Meeting',
        meeting_date=meeting_date,
        status='completed'
    )
    assert meeting.id == 'mtg_test123'
    assert meeting.workspace_id == 'ws_test123'
    assert meeting.title == 'Test Meeting'
    assert meeting.meeting_date == meeting_date
    assert meeting.status == 'completed'


def test_participant_creation():
    """Test participant model creation."""
    participant = Participant(
        id='usr_test123',
        name='Test User',
        email='test@example.com'
    )
    assert participant.id == 'usr_test123'
    assert participant.name == 'Test User'
    assert participant.email == 'test@example.com'


def test_note_creation():
    """Test note model creation."""
    note = Note(
        id='note_test123',
        meeting_id='mtg_test123',
        content='Test note content',
        author_id='usr_test123',
        note_order=1
    )
    assert note.id == 'note_test123'
    assert note.meeting_id == 'mtg_test123'
    assert note.content == 'Test note content'
    assert note.author_id == 'usr_test123'
    assert note.note_order == 1


def test_action_item_creation():
    """Test action item model creation."""
    action_item = ActionItem(
        id='act_test123',
        meeting_id='mtg_test123',
        description='Test action item',
        assignee_id='usr_test123',
        completed=False
    )
    assert action_item.id == 'act_test123'
    assert action_item.meeting_id == 'mtg_test123'
    assert action_item.description == 'Test action item'
    assert action_item.assignee_id == 'usr_test123'
    assert action_item.completed is False
