# AGENTS.md for Spice Tracker Bot

This document provides instructions for AI coding agents to contribute to the Spice Tracker Bot project.

## Project Overview

The Spice Tracker Bot is a Python-based Discord bot for the game "Dune: Awakening." It allows guild members to track the conversion of "spice sand" to "melange," manage group expeditions, and oversee a guild treasury.

- **Backend**: Python with `asyncpg` for database interaction.
- **Database**: PostgreSQL, hosted on Supabase. Schema is managed via migrations in `supabase/migrations/`.
- **Deployment**: Hosted on Fly.io using a Docker container.
- **CI/CD**: Uses GitHub Actions for linting, testing, and security checks.

## Project Structure

- `bot.py`: Main application entry point. Initializes the bot, registers commands, and handles events.
- `database.py`: Contains the `Database` class for all interactions with the PostgreSQL database.
- `commands/`: Directory for all bot command implementations. Each command is in its own file.
- `utils/`: Contains helper modules for embeds, database operations, logging, etc.
- `supabase/`: Holds database schema migrations and configuration.
- `tests/`: Contains all pytest tests for the application.

## Development Setup

- Create a virtual environment and install dependencies.
- `pip install -r requirements.txt`
- Create a `.env` file from `.env.example` and populate it with your credentials.
- To run the bot locally: `python bot.py`

## Testing Instructions

- The project uses `pytest` for testing.
- To run the full test suite with coverage: `pytest tests/ -v --cov=. --cov-report=term-missing`
- All new functionality must include unit tests.
- Ensure tests pass before committing any code.
- When reading the database schema, make sure to read the ENITRE migration history in order to understand the correct, current database structure.

## Code Style and Conventions

- Follow Python PEP 8 style guidelines.
- Enforce LF line endings
- Use type hints for all function parameters and return values.
- Keep functions small and focused on a single responsibility.
- All database operations should be asynchronous using `async/await`.
- Use the provided `EmbedBuilder` and `embed_utils` for creating Discord embeds to ensure consistency.
- Use the custom `logger` from `utils/logger.py` for all logging. It is optimized for Fly.io.

## Security Considerations

- Never commit API keys, tokens, or other sensitive credentials.
- Use environment variables for all configuration secrets (e.g., `DISCORD_TOKEN`, `DATABASE_URL`).
- Admin-level commands are permission-gated using the `is_admin` or `is_officer` functions in `utils/permissions.py`.
- Validate and sanitize all user inputs, especially for database queries.
