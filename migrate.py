#!/usr/bin/env python3
"""
Alembic migration management for Supabase.
This script provides a clean interface to manage database migrations.
"""

import os
import sys
import subprocess
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

def run_alembic_command(command_args):
    """Run an alembic command with proper environment setup."""
    try:
        # Set up environment
        env = os.environ.copy()

        # Check if DATABASE_URL is available
        if 'DATABASE_URL' in env and env['DATABASE_URL']:
            # Remove quotes if present
            db_url = env['DATABASE_URL'].strip('"\'')
            env['DATABASE_URL'] = db_url

            if 'postgresql://' in db_url:
                print("🐘 Using PostgreSQL (Supabase)")
            else:
                print(f"🔧 Using database: {db_url}")
        else:
            env['DATABASE_URL'] = 'sqlite:///spice_tracker.db'
            print("🔧 Using SQLite for development (set DATABASE_URL for production)")

        # Debug: Show what DATABASE_URL is being used
        print(f"🔍 DATABASE_URL: {env['DATABASE_URL'][:50]}...")

        # Run alembic command with explicit environment
        cmd = [sys.executable, "-m", "alembic"] + command_args
        result = subprocess.run(
            cmd,
            env=env,
            check=False,  # Don't raise exception on error
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Check if command failed
        if result.returncode != 0:
            print(f"❌ Alembic command failed with return code: {result.returncode}")
            return None

        return result
    except Exception as e:
        print(f"❌ Error running Alembic: {e}")
        return None

def generate_migration(message):
    """Generate a new migration from model changes."""
    print(f"🔄 Generating migration: {message}")
    return run_alembic_command([
        "revision", "--autogenerate", "-m", message
    ])

def apply_migrations():
    """Apply all pending migrations."""
    print("⬆️  Applying migrations...")
    return run_alembic_command(["upgrade", "head"])

def show_status():
    """Show current migration status."""
    print("📊 Migration status:")
    return run_alembic_command(["current"])

def show_history():
    """Show migration history."""
    print("📜 Migration history:")
    return run_alembic_command(["history"])

def rollback_migration():
    """Rollback the last migration."""
    print("⬇️  Rolling back last migration...")
    return run_alembic_command(["downgrade", "-1"])

def stamp_migration():
    """Stamp the current database state as the migration baseline."""
    print("🏷️  Stamping current database state...")
    return run_alembic_command(["stamp", "head"])

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("""
🚀 Alembic Migration Manager

Usage:
  python migrate.py generate "Description of changes"  # Generate new migration
  python migrate.py apply                              # Apply all migrations
  python migrate.py status                            # Show current status
  python migrate.py history                           # Show migration history
  python migrate.py rollback                          # Rollback last migration
  python migrate.py stamp                             # Stamp current state as baseline

Environment:
  DATABASE_URL - Set to your Supabase PostgreSQL URL for production
  (defaults to SQLite for development)
        """)
        return

    command = sys.argv[1].lower()

    if command == "generate":
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message")
            print("Usage: python migrate.py generate 'Add user email field'")
            return
        message = sys.argv[2]
        generate_migration(message)

    elif command == "apply":
        apply_migrations()

    elif command == "status":
        show_status()

    elif command == "history":
        show_history()

    elif command == "rollback":
        rollback_migration()

    elif command == "stamp":
        stamp_migration()

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python migrate.py' for help")

if __name__ == "__main__":
    main()
