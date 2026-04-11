"""CLI entry point for Fellow.app notes-only backup tool."""
import json
import os
import sys

import click
from dotenv import load_dotenv

load_dotenv()

from src.lib.logger import configure_logger, get_logger  # noqa: E402
from src.services.fellow_api import FellowAPIClient  # noqa: E402
from src.services.database import DatabaseService  # noqa: E402
from src.services.backup import BackupService  # noqa: E402
from src.services.export import ExportService  # noqa: E402

log_level = os.getenv('LOG_LEVEL', 'INFO')
configure_logger(log_level)
logger = get_logger(__name__)


@click.group()
@click.version_option(version='2.0.0')
def cli():
    """Fellow.app Notes Backup Tool - Export notes to MySQL."""
    pass


@cli.command()
@click.option(
    '--full', is_flag=True,
    help='Force full backup (ignore incremental timestamp)',
)
@click.option(
    '--dry-run', is_flag=True,
    help='Preview operations without database commits',
)
@click.option(
    '--verbose', is_flag=True, help='Enable verbose logging',
)
@click.option(
    '--quiet', is_flag=True, help='Quiet mode (errors only)',
)
@click.option(
    '--json', 'output_json', is_flag=True,
    help='Output summary in JSON format',
)
def backup(full, dry_run, verbose, quiet, output_json):
    """Run backup of Fellow.app notes to MySQL database."""

    if verbose and quiet:
        click.echo(
            "Error: Cannot use both --verbose and --quiet",
            err=True,
        )
        sys.exit(1)

    if quiet and not output_json:
        logger.warning(
            "quiet_mode_without_json",
            message="Running in quiet mode without --json "
                    "may hide all output",
        )

    if verbose:
        configure_logger('DEBUG')
    elif quiet:
        configure_logger('ERROR')

    try:
        api_client = FellowAPIClient()
        db_service = DatabaseService()
        db_service.connect()
        backup_service = BackupService(
            api_client, db_service
        )

        if not quiet and not output_json:
            click.echo("Fellow.app Notes Backup Tool v2.0.0")
            click.echo("=" * 40)
            click.echo()

        if dry_run and not quiet and not output_json:
            click.echo(
                "DRY RUN MODE - No database changes "
                "will be made"
            )
            click.echo()

        report = backup_service.backup_notes(
            full=full, dry_run=dry_run
        )

        if output_json:
            click.echo(report.to_json())
        else:
            click.echo(report.format_summary())

        db_service.disconnect()
        api_client.close()

        if not quiet and not output_json:
            if report.status == 'success':
                click.echo("Backup completed successfully!")
            else:
                click.echo("Backup completed with errors")

        if (report.status == 'success'
                and report.notes_errors == 0):
            sys.exit(0)
        elif (report.status == 'success'
                and report.notes_errors > 0):
            sys.exit(2)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error("backup_command_failed", error=str(e))
        if not output_json:
            click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--json', 'output_json', is_flag=True,
    help='Output in JSON format',
)
def report(output_json):
    """Generate summary report of backed-up notes."""
    try:
        db_service = DatabaseService()
        db_service.connect()

        with db_service.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM fellow_notes"
            )
            notes_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT author_id) "
                "FROM fellow_notes "
                "WHERE author_id IS NOT NULL"
            )
            authors_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT MIN(fellow_created_at), "
                "MAX(fellow_updated_at) FROM fellow_notes"
            )
            earliest, latest = cursor.fetchone()

            last_summary = db_service.get_backup_metadata(
                'last_backup_summary'
            )

        if output_json:
            data = {
                'notes': notes_count,
                'unique_authors': authors_count,
                'earliest_note': (
                    earliest.isoformat() if earliest
                    else None
                ),
                'latest_update': (
                    latest.isoformat() if latest
                    else None
                ),
                'last_backup_summary': (
                    json.loads(last_summary)
                    if last_summary else None
                ),
            }
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo("Backup Report")
            click.echo("=" * 50)
            click.echo(f"  Total Notes: {notes_count}")
            click.echo(
                f"  Unique Authors: {authors_count}"
            )
            if earliest:
                click.echo(
                    f"  Earliest Note: "
                    f"{earliest.isoformat()}"
                )
            if latest:
                click.echo(
                    f"  Latest Update: "
                    f"{latest.isoformat()}"
                )
            if last_summary:
                summary = json.loads(last_summary)
                click.echo("\n  Last Backup:")
                click.echo(
                    "    Timestamp: "
                    f"{summary.get('timestamp', 'N/A')}"
                )
                click.echo(
                    "    Mode: "
                    f"{summary.get('mode', 'N/A')}"
                )
                click.echo(
                    "    Notes Processed: "
                    f"{summary.get('notes_total', 0)}"
                )
                click.echo(
                    "    Errors: "
                    f"{summary.get('notes_errors', 0)}"
                )

        db_service.disconnect()

    except Exception as e:
        logger.error("report_command_failed", error=str(e))
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def test_connection():
    """Test API and database connections."""
    click.echo("Testing connections...")
    click.echo()

    try:
        click.echo(
            "1. Testing Fellow.app API connection..."
        )
        api_client = FellowAPIClient()
        api_client.fetch_notes(cursor=None, page_size=1)
        click.echo("   API connection successful")
        api_client.close()
    except Exception as e:
        click.echo(
            f"   API connection failed: {str(e)}"
        )
        sys.exit(1)

    try:
        click.echo(
            "2. Testing MySQL database connection..."
        )
        db_service = DatabaseService()
        db_service.connect()

        with db_service.transaction() as cursor:
            cursor.execute(
                "SHOW TABLES LIKE 'fellow_notes'"
            )
            notes_table = cursor.fetchone()
            cursor.execute(
                "SHOW TABLES LIKE "
                "'fellow_backup_metadata'"
            )
            metadata_table = cursor.fetchone()

        if not notes_table:
            click.echo(
                "   fellow_notes table not found "
                "- run schema.sql"
            )
        if not metadata_table:
            click.echo(
                "   fellow_backup_metadata table "
                "not found - run schema.sql"
            )

        if notes_table and metadata_table:
            click.echo(
                "   Database connection successful "
                "(all tables present)"
            )
        else:
            click.echo(
                "   Database connected but "
                "schema incomplete"
            )

        db_service.disconnect()
    except Exception as e:
        click.echo(
            f"   Database connection failed: {str(e)}"
        )
        sys.exit(1)

    click.echo()
    click.echo("All connections successful!")


@cli.command()
def discover_clients():
    """Scan attendee emails and map to client domains."""
    try:
        db_service = DatabaseService()
        db_service.connect()
        export_service = ExportService(db_service)

        click.echo("Scanning attendee email domains...")
        click.echo(
            "Excluding company domains: "
            f"{', '.join(export_service.company_domains)}"
        )
        click.echo()

        domain_map = export_service.discover_domains()

        if not domain_map:
            click.echo("No external domains found.")
            db_service.disconnect()
            return

        click.echo(
            f"Found {len(domain_map)} client domain(s):"
        )
        click.echo()
        click.echo(
            f"  {'Domain':<40} {'Client Name'}"
        )
        click.echo(f"  {'-' * 40} {'-' * 30}")
        for domain, name in sorted(domain_map.items()):
            click.echo(f"  {domain:<40} {name}")

        click.echo()
        click.echo("Review and edit in MySQL if needed:")
        click.echo(
            "  SELECT * FROM fellow_client_domains;"
        )
        click.echo(
            "  UPDATE fellow_client_domains "
            "SET client_name='New Name' "
            "WHERE email_domain='domain.com';"
        )

        db_service.disconnect()

    except Exception as e:
        logger.error(
            "discover_clients_failed", error=str(e)
        )
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--output-dir', default='meeting-notes',
    help='Output directory for markdown files',
)
@click.option(
    '--demo', is_flag=True,
    help='Export one note per client for preview',
)
@click.option(
    '--limit', type=int, default=None,
    help='Limit total notes exported',
)
@click.option(
    '--dry-run', is_flag=True,
    help='Show file tree without writing files',
)
@click.option(
    '--client', default=None,
    help='Export only notes for a specific client',
)
@click.option(
    '--verbose', is_flag=True,
    help='Enable verbose logging',
)
def export(output_dir, demo, limit, dry_run,
           client, verbose):
    """Export notes as markdown files organized by client."""
    if verbose:
        configure_logger('DEBUG')

    try:
        db_service = DatabaseService()
        db_service.connect()
        export_service = ExportService(
            db_service, output_dir=output_dir
        )

        if dry_run:
            click.echo(
                "DRY RUN - files that would be created:"
            )
            click.echo()

        report = export_service.export_notes(
            limit=limit,
            demo=demo,
            dry_run=dry_run,
            client_filter=client,
        )

        click.echo(report.format_summary())

        if report.status == 'success' and not dry_run:
            target = output_dir + (
                "-demo" if demo else ""
            )
            click.echo(f"Files written to: {target}/")

        db_service.disconnect()

        if report.status != 'success':
            sys.exit(1)

    except Exception as e:
        logger.error("export_failed", error=str(e))
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
