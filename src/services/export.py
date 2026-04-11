"""Export service for generating markdown files from notes."""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set

from src.lib.logger import get_logger
from src.services.database import DatabaseService
from src.models import Note, ExportReport

logger = get_logger(__name__)


def slugify(text: str, max_length: int = 80) -> str:
    """Convert text to URL/filename-safe slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text).strip('-')
    text = re.sub(r'-+', '-', text)
    return text[:max_length].rstrip('-')


def domain_to_client_name(domain: str) -> str:
    """Auto-generate a client name from an email domain.

    Examples:
        acme.com -> Acme
        big-corp.co.uk -> Big-Corp
        my.company.io -> My Company
    """
    # Remove common TLDs and country codes
    parts = domain.split('.')
    # Keep everything except the last 1-2 parts (TLD)
    if len(parts) > 2 and parts[-2] in ('co', 'com', 'org', 'ac'):
        name_parts = parts[:-2]
    else:
        name_parts = parts[:-1]
    name = ' '.join(name_parts)
    # Title-case, preserving hyphens
    return '-'.join(
        word.capitalize() for word in name.split('-')
    ) if '-' in name else name.title()


DEFAULT_TEMPLATE_SECTIONS = [
    "# Talking Points",
    "(The things to talk about)",
    "# Action Items",
    "(What came out of this meeting? What are your next steps?)",
    "# Notepad",
    "(Anything else to write down?)",
]


def is_default_template(content: str) -> bool:
    """Check if content is just the Fellow default template with no real notes."""
    stripped = content.strip()
    if not stripped:
        return True
    # Remove all default sections and see if anything meaningful remains
    remaining = stripped
    for section in DEFAULT_TEMPLATE_SECTIONS:
        remaining = remaining.replace(section, '')
    remaining = remaining.strip(' \t\n\r#')
    return len(remaining) == 0


class ExportService:
    """Exports notes as markdown files organized by client."""

    def __init__(
        self,
        db_service: DatabaseService,
        output_dir: str = "meeting-notes",
        company_domains: Optional[Set[str]] = None,
        owner_email: Optional[str] = None,
    ):
        self.db = db_service
        self.output_dir = Path(output_dir)
        self.company_domains = company_domains or {
            d.strip() for d in
            os.getenv('COMPANY_DOMAINS', 'cursor.co.uk').split(',')
        }
        self.owner_email = (
            owner_email
            or os.getenv('OWNER_EMAIL', 'daniel@cursor.co.uk')
        ).lower()

    def discover_domains(self) -> Dict[str, str]:
        """Find all non-company attendee domains and generate
        client name suggestions. Inserts into client_domains table
        (skips existing rows to preserve user edits).

        Returns mapping of domain -> client_name.
        """
        self.db.ensure_export_schema()
        domains = self.db.get_distinct_attendee_domains(
            self.company_domains
        )
        for domain in domains:
            client_name = domain_to_client_name(domain)
            self.db.upsert_client_domain(domain, client_name)
            logger.info(
                "client_domain_discovered",
                domain=domain,
                client_name=client_name,
            )
        return self.db.get_client_domain_map()

    def resolve_client(
        self,
        attendee_emails: List[str],
        domain_map: Dict[str, str],
    ) -> Optional[str]:
        """Determine client name from attendee email domains.

        Returns the first matching non-company client name.
        If all attendees are company employees, returns "Cursor".
        Returns None only if there are no attendees at all.
        """
        if not attendee_emails:
            return None

        for email in attendee_emails:
            parts = email.split('@')
            if len(parts) != 2:
                continue
            domain = parts[1].lower()
            if domain in self.company_domains:
                continue
            if domain in domain_map:
                return domain_map[domain]

        # All attendees are company employees — internal meeting
        return "Cursor"

    def _is_one_to_one(
        self, note: Note, client: str
    ) -> Optional[str]:
        """Check if a Cursor internal note is a 1-to-1 meeting.

        Returns the other person's name if it is, None otherwise.
        """
        if client != "Cursor":
            return None
        company_attendees = [
            e for e in note.event_attendees
            if '@' in e
            and e.split('@')[1].lower() in self.company_domains
        ]
        if len(company_attendees) != 2:
            return None
        if self.owner_email not in (
            e.lower() for e in company_attendees
        ):
            return None
        # Get the other person's name from their email
        for email in company_attendees:
            if email.lower() != self.owner_email:
                local = email.split('@')[0]
                return local.replace('.', ' ').replace(
                    '-', ' '
                ).title()
        return None

    def _resolve_author(self, note: Note) -> str:
        """Get author name, falling back to first company attendee."""
        if note.author_name:
            return note.author_name
        # Fall back to first Cursor employee in attendees
        for email in note.event_attendees:
            parts = email.split('@')
            if len(parts) == 2 and parts[1].lower() in self.company_domains:
                # Use the local part, title-cased
                local = parts[0].replace('.', ' ').replace('-', ' ')
                return local.title()
        return "Unknown"

    def render_markdown(
        self, note: Note, client_name: str
    ) -> str:
        """Render a note as a markdown string with header metadata."""
        title = note.title or "Untitled Note"
        date_str = ""
        if note.event_start:
            date_str = note.event_start.strftime('%Y-%m-%d')
        elif note.fellow_created_at:
            date_str = note.fellow_created_at.strftime('%Y-%m-%d')

        author = self._resolve_author(note)
        attendees = ", ".join(
            note.event_attendees
        ) if note.event_attendees else "None listed"

        content = (
            note.content_markdown
            or note.content
            or "*No content*"
        )

        date_line = f"**Date:** {date_str}" if date_str else "**Date:** Unknown"

        lines = [
            f"# {title}",
            "",
            f"{date_line}  ",
            f"**Client:** {client_name}  ",
            f"**Author:** {author}  ",
            f"**Attendees:** {attendees}",
            "",
            "---",
            "",
            content,
        ]
        return "\n".join(lines)

    def _get_note_year(self, note: Note) -> str:
        """Get the year string for folder grouping."""
        if note.event_start:
            return note.event_start.strftime('%Y')
        elif note.fellow_created_at:
            return note.fellow_created_at.strftime('%Y')
        return "no-year"

    def generate_filename(
        self, note: Note, used_names: Set[str]
    ) -> str:
        """Generate a unique filename for a note.

        Format: YYYY-MM-DD-slugified-title.md
        Appends -2, -3 etc. for duplicates.
        """
        if note.event_start:
            date_str = note.event_start.strftime('%Y-%m-%d')
        elif note.fellow_created_at:
            date_str = note.fellow_created_at.strftime('%Y-%m-%d')
        else:
            date_str = "no-date"

        title_slug = slugify(note.title) if note.title else "untitled"
        base = f"{date_str}-{title_slug}"
        filename = f"{base}.md"

        counter = 2
        while filename in used_names:
            filename = f"{base}-{counter}.md"
            counter += 1

        used_names.add(filename)
        return filename

    def export_notes(
        self,
        limit: Optional[int] = None,
        demo: bool = False,
        dry_run: bool = False,
        client_filter: Optional[str] = None,
    ) -> ExportReport:
        """Export notes as markdown files organized by client.

        Args:
            limit: Max notes to export
            demo: If True, export one note per client (most recent)
            dry_run: If True, print file tree without writing
            client_filter: Export only this client's notes
        """
        report = ExportReport(start_time=datetime.utcnow())
        self.db.ensure_export_schema()
        domain_map = self.db.get_client_domain_map()

        if not domain_map:
            logger.warning("no_client_domains_found")
            report.status = 'failed'
            report.end_time = datetime.utcnow()
            return report

        notes = self.db.get_all_notes_with_attendees(limit=limit)
        logger.info("notes_loaded_for_export", count=len(notes))

        # Track filenames per client folder to avoid duplicates
        used_names: Dict[str, Set[str]] = {}
        # Track clients seen for demo mode (one per client)
        demo_clients_seen: Set[str] = set()
        clients_seen: Set[str] = set()

        output_dir = self.output_dir
        if demo:
            output_dir = Path(str(self.output_dir) + "-demo")

        for note in notes:
            try:
                # Skip notes with only the default template
                note_content = (
                    note.content_markdown or note.content or ""
                )
                if is_default_template(note_content):
                    report.notes_skipped += 1
                    continue

                client = self.resolve_client(
                    note.event_attendees, domain_map
                )
                if client is None:
                    client = "_uncategorized"
                    report.uncategorized += 1

                if client_filter and client != client_filter:
                    report.notes_skipped += 1
                    continue

                # Check if this is a 1-to-1 Cursor meeting
                other_person = self._is_one_to_one(
                    note, client
                )
                if other_person:
                    demo_key = f"1-to-1/{other_person}"
                else:
                    demo_key = client

                if demo and demo_key in demo_clients_seen:
                    report.notes_skipped += 1
                    continue

                year = self._get_note_year(note)

                if other_person:
                    person_slug = slugify(other_person)
                    folder_key = f"1-to-1/{year}/{person_slug}"
                    if folder_key not in used_names:
                        used_names[folder_key] = set()
                    filename = self.generate_filename(
                        note, used_names[folder_key]
                    )
                    file_path = (
                        output_dir / "1-to-1" / year
                        / person_slug / filename
                    )
                else:
                    folder_name = (
                        slugify(client) or "_uncategorized"
                    )
                    folder_key = f"{year}/{folder_name}"
                    if folder_key not in used_names:
                        used_names[folder_key] = set()
                    filename = self.generate_filename(
                        note, used_names[folder_key]
                    )
                    file_path = (
                        output_dir / year
                        / folder_name / filename
                    )

                if dry_run:
                    print(f"  {file_path}")
                else:
                    file_path.parent.mkdir(
                        parents=True, exist_ok=True
                    )
                    md_content = self.render_markdown(
                        note, client
                    )
                    file_path.write_text(
                        md_content, encoding='utf-8'
                    )
                    logger.debug(
                        "note_exported",
                        note_id=note.id,
                        path=str(file_path),
                    )

                report.notes_exported += 1
                clients_seen.add(client)
                if demo:
                    demo_clients_seen.add(demo_key)

            except Exception as e:
                logger.error(
                    "note_export_failed",
                    note_id=note.id,
                    error=str(e),
                )
                report.add_error(note.id, str(e))

        report.clients_found = len(
            clients_seen - {'_uncategorized'}
        )
        report.status = 'success'
        report.end_time = datetime.utcnow()
        return report
