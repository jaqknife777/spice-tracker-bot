# 🏜️ Spice Tracker Bot

A Discord bot for **Dune: Awakening** guilds to convert spice sand to melange, manage expeditions, and handle guild treasury operations with automated melange production tracking.

## ✨ Features

- **🏜️ Sand Conversion** - Convert spice sand into melange (primary currency) at 50:1 ratio (or 37.5:1 with landsraad bonus)
- **⚗️ Refinery System** - View melange production, pending payments, and payment statistics
- **🚀 Team Expeditions** - Split spice among team members with customizable guild cuts
- **🏛️ Guild Treasury** - Automatic guild cuts from expeditions with withdrawal controls
- **📊 Leaderboards** - Guild rankings by melange production
- **💰 Payment System** - Track pending melange and process payments to users
- **🏛️ Landsraad Bonus** - Global conversion rate bonus (37.5 sand = 1 melange when active)
- **🔧 Admin Controls** - Treasury management, payroll processing, and data resets
- **🗄️ Database Migrations** - Automated schema management with Alembic
- **🔧 Modern Architecture** - SQLAlchemy ORM with async support and production-ready migrations

## 🚀 Quick Setup

### Prerequisites
- Python 3.11+
- Discord Bot Token
- Supabase Account (PostgreSQL database)
- Git (for version control)

### Local Development

1. **Clone and install**
   ```bash
   git clone https://github.com/your-username/spice-tracker-bot.git
   cd spice-tracker-bot
   # Using uv (recommended)
   uv pip install -r requirements.txt

   # Or with pip
   pip install -r requirements.txt
   ```

2. **Environment variables**
   Create a `.env` file with:
   ```env
   DISCORD_TOKEN=your_bot_token
   DATABASE_URL=your_supabase_connection_string
   BOT_OWNER_ID=your_discord_user_id
   AUTO_SYNC_COMMANDS=true
   ```

3. **Database setup**
   ```bash
   # Apply database migrations
   python migrate.py apply
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 🗄️ Database Management

### Architecture
This project uses **SQLAlchemy ORM** with **Alembic migrations** for modern database management:

- **Development**: SQLite database for local testing
- **Production**: PostgreSQL (Supabase) with full migration support
- **Schema Management**: ORM models define structure, migrations handle changes
- **Version Control**: All database changes are tracked and reversible

### Migration Commands
```bash
# Check current migration status
python migrate.py status

# Apply all pending migrations
python migrate.py apply

# Generate new migration from model changes
python migrate.py generate "Add user email field"

# Show migration history
python migrate.py history

# Rollback last migration
python migrate.py rollback

# Stamp current state as baseline (for existing databases)
python migrate.py stamp
```

### Supabase Setup
1. Create project at [supabase.com](https://supabase.com)
2. Get your connection string from Project Settings → Database
3. Add to your `.env` file: `DATABASE_URL=your_supabase_connection_string`
4. Apply migrations: `python migrate.py apply`

### Quick Reference
```bash
# Database migrations
python migrate.py status     # Check migration status
python migrate.py apply      # Apply pending migrations
python migrate.py generate   # Create new migration
python migrate.py rollback   # Undo last migration
python migrate.py stamp      # Mark current state as baseline

# Development
python -m pytest            # Run tests
python bot.py               # Start the bot
```

## 🤖 Commands

### 🏜️ Harvester Commands
- **`/sand <amount>`** - Convert spice sand to melange (1-10,000). Primary currency conversion at 50:1 ratio
- **`/refinery`** - View your melange production and payment status (private)
- **`/ledger`** - View your sand conversion history and melange status (private)
- **`/leaderboard [limit]`** - Display top spice refiners by melange production (optionally set a limit)
- **`/expedition <expedition_id>`** - View details of a specific expedition
- **`/help`** - Display all available commands (private)
 - **`/perms`** - Show your permission status and matched roles (private)
 - **`/water [destination]`** - Request a water delivery (default: "DD base")

### 🚀 Team Commands
- **`/split <total_sand> <users> [guild]`** - Split spice sand among expedition members and convert to melange
  - **Example:** `/split 10000 "@harvester 30 @scout @pilot" 15`
  - **Guild Cut:** Percentage taken off the top (default: 10%)
  - **User Percentages:** Users with percentages get exact amounts, others split equally
  - **Creates:** Expedition records and tracks melange owed for payout

### 🏛️ Guild Admin Commands
 - **`/reset confirm:True`** - Reset all refinery statistics (requires confirmation)
 - **`/pending`** - View all users with pending melange payments and amounts owed
 - **`/pay <user> [amount]`** - Process payment for a specific harvester (defaults to full pending)
 - **`/payroll`** - Process payments for all unpaid harvesters at once
 - **`/guild_withdraw <user> <amount>`** - Withdraw resources from guild treasury to give to a user
 - **`/landsraad <action> [confirm]`** - Manage landsraad bonus (status/enable/disable)
  - **Status:** Check current conversion rate (50:1 or 37.5:1)
  - **Enable:** Activate landsraad bonus (37.5 sand = 1 melange)
  - **Disable:** Return to normal rate (50 sand = 1 melange)

### 🧾 User/Finance Viewing
 - **`/treasury`** - View guild treasury balance and melange reserves

### 🔧 Bot Owner Commands
- **`/sync`** - Sync slash commands (Bot Owner Only)

## 📊 How It Works

### Individual Harvests
```
/sand 2500  →  50 melange produced (50:1 conversion rate)
/sand 2500  →  66 melange produced (37.5:1 with landsraad bonus)
```

### Team Expeditions
```
/split 10000 "@harvester 30 @scout @pilot" 15

Result (15% guild cut):
- Guild Treasury: 1500 sand → 30 melange
- Harvester: 2550 sand (30% of remaining) → 51 melange
- Scout: 2975 sand (35% of remaining) → 59 melange
- Pilot: 2975 sand (35% of remaining) → 59 melange
```

### Guild Treasury System
- **Automatic Collection:** Receives configurable percentage from all expeditions
- **Admin Withdrawals:** Controlled access for guild leaders to reward members
- **Full Audit Trail:** All transactions logged for transparency
- **Balance Tracking:** Real-time sand and melange reserves

### Payment System
- **Pending Tracking:** All melange owed to users from deposits and expeditions
- **Individual Payments:** Process specific user payments with `/pay`
- **Bulk Payroll:** Pay all pending melange at once with `/payroll`
- **Payment History:** Complete audit trail of all melange payments

## 🚀 Deployment

### Fly.io (Recommended)
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Setup and deploy
fly auth login
fly apps create your-spice-bot
fly secrets set DISCORD_TOKEN=xxx DATABASE_URL=xxx BOT_OWNER_ID=xxx
# Optional role configuration
fly secrets set ADMIN_ROLE_IDS=123,456 OFFICER_ROLE_IDS=789 ALLOWED_ROLE_IDS=111,222
fly deploy
```

The bot includes:
- **Health Checks:** `/health` endpoint for Fly.io monitoring
- **Auto-Sync:** Commands sync automatically on startup
- **Structured Logging:** Production-ready logging for monitoring
- **Error Handling:** Graceful error recovery and user feedback

## 🏗️ Database Schema

### Core Tables
- **`users`** - Discord user info, total/paid melange, last activity
- **`deposits`** - Individual sand deposits with type and expedition tracking
- **`expeditions`** - Team expedition records with guild cuts and participants
- **`expedition_participants`** - Individual participation in expeditions
- **`guild_treasury`** - Guild's accumulated sand and melange reserves
- **`guild_transactions`** - Treasury operation audit trail
- **`melange_payments`** - Payment records with amounts and timestamps

### Database Views
- **`user_stats`** - Comprehensive user statistics with pending payments
- **`guild_summary`** - Guild-wide statistics and treasury information

## 🔧 Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_TOKEN` | Discord bot token | ✅ | - |
| `DATABASE_URL` | Supabase PostgreSQL connection string | ✅ | - |
| `BOT_OWNER_ID` | Discord user ID for bot owner commands | ✅ | - |
| `AUTO_SYNC_COMMANDS` | Auto-sync slash commands on startup | ❌ | `true` |
| `CMD_PREFIX` | Prefix added to all slash command names | ❌ | - |
| `CMD_NAME_OVERRIDES` | Rename specific commands (JSON or CSV map) | ❌ | - |
| `COMMAND_PERMISSION_OVERRIDES` | Override command permissions (format: `cmd:level`) | ❌ | - |
| `ADMIN_ROLE_IDS` | Comma-separated admin Discord role IDs | ❌ | - |
| `OFFICER_ROLE_IDS` | Comma-separated officer Discord role IDs | ❌ | - |
| `ALLOWED_ROLE_IDS` | Comma-separated roles allowed to use user-level cmds | ❌ | - |
| `PORT` | Health server port (Fly/containers) | ❌ | `8080` |

### Command customization (names and permissions)

You can customize both the registered slash command names and their required permission levels via environment variables.

1) Prefix all command names
```bash
# Registers /dev_sand, /dev_calc, ...
export CMD_PREFIX="dev_"
```

2) Rename specific commands
```bash
# JSON format
export CMD_NAME_OVERRIDES='{"sand":"harvest","calc":"estimate"}'

# or CSV key=value pairs
export CMD_NAME_OVERRIDES='sand=harvest,calc=estimate'
```

3) Override command permission levels
```bash
# Make reset command officer-only instead of admin
export COMMAND_PERMISSION_OVERRIDES="reset:officer"

# Make sand command public
export COMMAND_PERMISSION_OVERRIDES="sand:any"

# Multiple overrides
export COMMAND_PERMISSION_OVERRIDES="reset:officer,sand:any,help:user"
```

4) Apply changes
- If `AUTO_SYNC_COMMANDS=true` (default), changes will sync on startup.
- Otherwise, run the owner-only `/sync` command after the bot is online.

Notes:
- Only the registered slash names change; internal Python function names remain the same.
- You can combine prefix and overrides. Name overrides are applied after prefixing.
- Permission levels: `admin` → `officer` → `user` → `any` (public)

## 🏗️ Technical Architecture

### Database Layer
- **SQLAlchemy ORM** - Modern async database abstraction
- **Alembic Migrations** - Version-controlled schema management
- **PostgreSQL** - Production database (Supabase)
- **SQLite** - Development and testing database

### Bot Framework
- **discord.py** - Modern Discord API wrapper with slash commands
- **Async/Await** - Non-blocking I/O for high performance
- **Command System** - Modular command architecture with permission controls

### Development Tools
- **pytest** - Comprehensive test suite with fixtures
- **python-dotenv** - Environment variable management
- **Migration Manager** - Custom wrapper for database operations
- **Type Hints** - Full type safety throughout codebase

### Production Features
- **Structured Logging** - Production-ready logging with context
- **Error Handling** - Graceful error recovery and user feedback
- **Rate Limiting** - Built-in Discord API rate limit handling
- **Health Checks** - Database connectivity and command validation

## 🛡️ Permissions

- **👥 Basic Commands:** All guild members can use harvesting and viewing commands
- **🛡️ Admin Commands:** Discord administrators only (pay, payroll, pending, guild_withdraw, reset, landsraad)
- **👥 User Viewing:** `treasury` is viewable by allowed users
- **👑 Owner Commands:** Bot owner only (sync, advanced debugging)
- **🔒 Private Responses:** Personal financial data sent as ephemeral messages

### Permission Overrides

Override command permissions via environment variable for testing or emergency situations:

```bash
# Make reset command officer-only instead of admin
export COMMAND_PERMISSION_OVERRIDES="reset:officer"

# Make sand command public
export COMMAND_PERMISSION_OVERRIDES="sand:any"

# Multiple overrides
export COMMAND_PERMISSION_OVERRIDES="reset:officer,sand:any,help:user"
```

**Permission Levels:** `admin` → `officer` → `user` → `any` (public)

## ⚡ Performance Features

- **🚀 Fast Startup:** < 2 second boot time with automatic command sync
- **📊 Structured Logging:** Production-ready logging with Fly.io integration
- **🔄 Connection Pooling:** Efficient database connections with automatic retry
- **⚡ Async Operations:** Non-blocking Discord interactions and database queries
- **🛡️ Error Recovery:** Graceful handling of database and Discord API failures

## 🧪 Development

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test file
python -m pytest tests/test_commands.py

# Run with verbose output
python -m pytest -v
```

### Database Development
```bash
# Generate new migration from model changes
python migrate.py generate "Description of changes"

# Apply migrations to development database
python migrate.py apply

# Check migration status
python migrate.py status

# Rollback last migration
python migrate.py rollback
```

### Code Quality
- **Type Hints** - All functions have proper type annotations
- **Docstrings** - Comprehensive documentation for all public methods
- **Error Handling** - Graceful error recovery with user feedback
- **Logging** - Structured logging for debugging and monitoring

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run tests: `python -m pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, questions, or feature requests:
- Open an issue on GitHub
- Join our Discord server
- Contact the bot owner

---

**Made with ❤️ for the Dune: Awakening community**
