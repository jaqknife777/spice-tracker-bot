# 🏜️ Spice Tracker Bot

A Discord bot for **Dune: Awakening** guilds to convert spice sand to melange, manage expeditions, and handle guild treasury operations with automated melange production tracking.

## ✨ Features

- **🏜️ Sand Conversion** - Convert spice sand into melange (primary currency) at 50:1 ratio
- **⚗️ Refinery System** - View melange production, pending payments, and payment statistics
- **🚀 Team Expeditions** - Split spice among team members with customizable guild cuts
- **🏛️ Guild Treasury** - Automatic guild cuts from expeditions with withdrawal controls
- **📊 Leaderboards** - Guild rankings by melange production
- **💰 Payment System** - Track pending melange and process payments to users
- **🔧 Admin Controls** - Treasury management, payroll processing, and data resets

## 🚀 Quick Setup

### Prerequisites
- Python 3.11+
- Discord Bot Token
- Supabase Account (PostgreSQL database)

### Local Development

1. **Clone and install**
   ```bash
   git clone https://github.com/your-username/spice-tracker-bot.git
   cd spice-tracker-bot
   pip install -r requirements.txt
   ```

2. **Environment variables**
   ```env
   DISCORD_TOKEN=your_bot_token
   DATABASE_URL=your_supabase_connection_string
   BOT_OWNER_ID=your_discord_user_id
   AUTO_SYNC_COMMANDS=true
   ```

3. **Run**
   ```bash
   python bot.py
   ```

## 🗄️ Database Setup

### Supabase Setup
1. Create project at [supabase.com](https://supabase.com)
2. Get your connection string from Project Settings → Database
3. Run the migration: `supabase/migrations/20241201000000_initial_schema.sql`
4. Set `DATABASE_URL` environment variable

## 🤖 Commands

### 🏜️ Harvester Commands
- **`/sand <amount>`** - Convert spice sand to melange (1-10,000). Primary currency conversion at 50:1 ratio
- **`/refinery`** - View your melange production and payment status (private)
- **`/ledger`** - View your sand conversion history and melange status (private)
- **`/leaderboard [limit]`** - Display top spice refiners by melange production (5-25 users)
- **`/expedition <id>`** - View details of a specific expedition
- **`/help`** - Display all available commands (private)

### 🚀 Team Commands
- **`/split <total_sand> <users> [guild]`** - Split spice sand among expedition members and convert to melange
  - **Example:** `/split 10000 "@harvester 30 @scout @pilot" 15`
  - **Guild Cut:** Percentage taken off the top (default: 10%)
  - **User Percentages:** Users with percentages get exact amounts, others split equally
  - **Creates:** Expedition records and tracks melange owed for payout

### 🏛️ Guild Admin Commands
- **`/pending`** - View all users with pending melange payments and amounts owed
- **`/payment <user>`** - Process payment for a specific harvester's deposits
- **`/payroll`** - Process payments for all unpaid harvesters at once
- **`/treasury`** - View guild treasury balance and melange reserves
- **`/guild_withdraw <user> <amount>`** - Withdraw resources from guild treasury to give to a user
- **`/reset confirm:True`** - Reset all refinery statistics (requires confirmation)

### 🔧 Bot Owner Commands
- **`/sync`** - Sync slash commands (Bot Owner Only)

## 📊 How It Works

### Individual Harvests
```
/sand 2500  →  50 melange produced (50:1 conversion rate)
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
- **Individual Payments:** Process specific user payments with `/payment`
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
- **`settings`** - Bot configuration and guild-specific settings

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

## 🛡️ Permissions

- **👥 Basic Commands:** All guild members can use harvesting and viewing commands
- **🛡️ Admin Commands:** Discord administrators only (payment, treasury, reset)
- **👑 Owner Commands:** Bot owner only (sync, advanced debugging)
- **🔒 Private Responses:** Personal financial data sent as ephemeral messages

## ⚡ Performance Features

- **🚀 Fast Startup:** < 2 second boot time with automatic command sync
- **📊 Structured Logging:** Production-ready logging with Fly.io integration  
- **🔄 Connection Pooling:** Efficient database connections with automatic retry
- **⚡ Async Operations:** Non-blocking Discord interactions and database queries
- **🛡️ Error Recovery:** Graceful handling of database and Discord API failures

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

**Test Coverage:** 46 tests covering command functionality, database operations, and utility functions.

## 📝 Recent Updates

- **✅ Command Rename:** `/harvest` → `/sand` for better game alignment
- **✅ Auto-Sync:** Commands sync automatically on bot startup
- **✅ Structured Logging:** Professional logging system for production monitoring
- **✅ Bug Fixes:** Resolved timestamp handling and database schema issues
- **✅ Payment System:** Complete melange payment tracking and processing
- **✅ Guild Treasury:** Advanced treasury management with audit trails

---

**🎮 Game:** Dune: Awakening  
**🚀 Status:** Production Ready  
**📊 Deployment:** Fly.io + Supabase  
**🧪 Tests:** 46 passing ✅