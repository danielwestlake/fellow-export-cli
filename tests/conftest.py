"""Pytest configuration and fixtures."""
import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test', override=True)


@pytest.fixture
def test_workspace():
    """Fixture for test workspace data."""
    from src.models import Workspace
    return Workspace(
        id='ws_test123',
        name='Test Workspace'
    )


@pytest.fixture
def test_meeting():
    """Fixture for test meeting data."""
    from datetime import datetime
    from src.models import Meeting
    return Meeting(
        id='mtg_test123',
        workspace_id='ws_test123',
        title='Test Meeting',
        meeting_date=datetime(2025, 12, 24, 10, 0, 0),
        status='completed'
    )


@pytest.fixture
def test_participant():
    """Fixture for test participant data."""
    from src.models import Participant
    return Participant(
        id='usr_test123',
        name='Test User',
        email='test@example.com'
    )


@pytest.fixture
def test_note():
    """Fixture for test note data."""
    from src.models import Note
    return Note(
        id='note_test123',
        meeting_id='mtg_test123',
        content='Test note content',
        author_id='usr_test123',
        note_order=1
    )


@pytest.fixture
def test_action_item():
    """Fixture for test action item data."""
    from src.models import ActionItem
    return ActionItem(
        id='act_test123',
        meeting_id='mtg_test123',
        description='Test action item',
        assignee_id='usr_test123',
        completed=False
    )
