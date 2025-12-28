"""CLI entry point for Fellow.app notes-only backup tool."""
import sys
import os
from pathlib import Path
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.lib.logger import configure_logger, get_logger
from src.services.fellow_api import FellowAPIClient
from src.services.database import DatabaseService
from src.services.backup import BackupService

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
configure_logger(log_level)
logger = get_logger(__name__)


@click.group()
@click.version_option(version='2.0.0')
def cli():
    """Fellow.app Notes Backup Tool - Export notes to MySQL."""
    pass


@cli.command()
@click.option('--full', is_flag=True, help='Force full backup (ignore incremental timestamp)')
@click.option('--dry-run', is_flag=True, help='Preview operations without database commits')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', is_flag=True, help='Quiet mode (errors only)')
@click.option('--json', 'output_json', is_flag=True, help='Output summary in JSON format')
def backup(full, dry_run, verbose, quiet, output_json):
    """Run backup of Fellow.app notes to MySQL database."""
    
    # Validate conflicting options
    if verbose and quiet:
        click.echo("Error: Cannot use both --verbose and --quiet", err=True)
        sys.exit(1)
    
    if quiet and not output_json:
        # In quiet mode without JSON, user might miss all output
        logger.warning("quiet_mode_without_json", 
                      message="Running in quiet mode without --json may hide all output")
    
    # Adjust log level
    if verbose:
        configure_logger('DEBUG')
    elif quiet:
        configure_logger('ERROR')
    
    try:
        # Initialize services
        api_client = FellowAPIClient()
        db_service = DatabaseService()
        db_service.connect()
        backup_service = BackupService(api_client, db_service)
        
        if not quiet and not output_json:
            click.echo("Fellow.app Notes Backup Tool v2.0.0")
            click.echo("=" * 40)
            click.echo()
        
        if dry_run and not quiet and not output_json:
            click.echo("⚠️  DRY RUN MODE - No database changes will be made")
            click.echo()
        
        # Execute backup
        report = backup_service.backup_notes(
            full=full,
            dry_run=dry_run
        )
        
        # Display report
        if output_json:
            click.echo(report.to_json())
        else:
            click.echo(report.format_summary())
        
        # Cleanup
        db_service.disconnect()
        api_client.close()
        
        if not quiet and not output_json:
            if report.status == 'success':
                click.echo("✅ Backup completed successfully!")
            else:
                click.echo("⚠️  Backup completed with errors")
        
        # Exit with appropriate code
        if report.status == 'success' and report.notes_errors == 0:
            sys.exit(0)
        elif report.status == 'success' and report.notes_errors > 0:
            sys.exit(2)  # Partial success
        else:
            sys.exit(1)  # Failure
        
    except Exception as e:
        logger.error("backup_command_failed", error=str(e))
        if not output_json:
            click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def report(output_json):
    """Generate summary report of backed-up notes."""
    try:
        db_service = DatabaseService()
        db_service.connect()
        
        # Query database for statistics
        with db_service.transaction() as cursor:
            # Count notes
            cursor.execute("SELECT COUNT(*) FROM notes")
            notes_count = cursor.fetchone()[0]
            
            # Count unique authors
            cursor.execute("SELECT COUNT(DISTINCT author_id) FROM notes WHERE author_id IS NOT NULL")
            authors_count = cursor.fetchone()[0]
            
            # Get earliest and latest note timestamps
            cursor.execute("SELECT MIN(fellow_created_at), MAX(fellow_updated_at) FROM notes")
            earliest, latest = cursor.fetchone()
            
            # Get last backup summary
            last_summary = db_service.get_backup_metadata('last_backup_summary')
        
        if output_json:
            import json
            data = {
                'notes': notes_count,
                'unique_authors': authors_count,
                'earliest_note': earliest.isoformat() if earliest else None,
                'latest_update': latest.isoformat() if latest else None,
                'last_backup_summary': json.loads(last_summary) if last_summary else None
            }
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo("Backup Report")
            click.echo("=" * 50)
            click.echo(f"  Total Notes: {notes_count}")
            click.echo(f"  Unique Authors: {authors_count}")
            if earliest:
                click.echo(f"  Earliest Note: {earliest.isoformat()}")
            if latest:
                click.echo(f"  Latest Update: {latest.isoformat()}")
            if last_summary:
                import json
                summary = json.loads(last_summary)
                click.echo(f"\n  Last Backup:")
                click.echo(f"    Timestamp: {summary.get('timestamp', 'N/A')}")
                click.echo(f"    Mode: {summary.get('mode', 'N/A')}")
                click.echo(f"    Notes Processed: {summary.get('notes_total', 0)}")
                click.echo(f"    Errors: {summary.get('notes_errors', 0)}")
        
        db_service.disconnect()
        
    except Exception as e:
        logger.error("report_command_failed", error=str(e))
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def test_connection():
    """Test API and database connections."""
    click.echo("Testing connections...")
    click.echo()
    
    # Test API connection
    try:
        click.echo("1. Testing Fellow.app API connection...")
        api_client = FellowAPIClient()
        
        # Make a simple request to fetch one page
        response = api_client.fetch_notes(page=1, per_page=1)
        
        click.echo(f"   ✅ API connection successful")
        api_client.close()
    except Exception as e:
        click.echo(f"   ❌ API connection failed: {str(e)}")
        sys.exit(1)
    
    # Test database connection
    try:
        click.echo("2. Testing MySQL database connection...")
        db_service = DatabaseService()
        db_service.connect()
        
        # Verify tables exist
        with db_service.transaction() as cursor:
            cursor.execute("SHOW TABLES LIKE 'notes'")
            notes_table = cursor.fetchone()
            cursor.execute("SHOW TABLES LIKE 'backup_metadata'")
            metadata_table = cursor.fetchone()
        
        if not notes_table:
            click.echo("   ⚠️  Notes table not found - run schema.sql")
        if not metadata_table:
            click.echo("   ⚠️  Backup metadata table not found - run schema.sql")
        
        if notes_table and metadata_table:
            click.echo("   ✅ Database connection successful (all tables present)")
        else:
            click.echo("   ⚠️  Database connected but schema incomplete")
        
        db_service.disconnect()
    except Exception as e:
        click.echo(f"   ❌ Database connection failed: {str(e)}")
        sys.exit(1)
    
    click.echo()
    click.echo("✅ All connections successful!")


if __name__ == '__main__':
    cli()
