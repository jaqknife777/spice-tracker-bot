# 🏜️ Spice Tracker Bot

A Discord bot for **Dune: Awakening** guilds to track spice sand collection, manage expeditions, and handle guild treasury operations.

## ✨ Features

- **Individual Harvests** - Track personal spice sand deposits
- **Team Expeditions** - Split spice among team members with guild cuts
- **Guild Treasury** - Automatic 10% guild cut from expeditions
- **User Statistics** - View personal refinery stats and pending payments
- **Admin Controls** - Treasury withdrawals and payment processing
- **Per-Guild Databases** - Each guild has isolated data

## 🚀 Quick Setup

### Prerequisites
- Python 3.11+
- Discord Bot Token
- Supabase Account

### Local Development

1. **Clone and install**
   ```bash
   git clone https://github.com/jaqknife777/spice-tracker-bot.git
   cd spice-tracker-bot
   pip install -r requirements.txt
   ```

2. **Environment variables**
   ```env
   DISCORD_TOKEN=your_bot_token
   DATABASE_URL=your_supabase_url
   ```

3. **Run**
   ```bash
   python bot.py
   ```

## 🗄️ Database Setup

### Supabase Setup
1. Create project at [supabase.com](https://supabase.com)
2. Install Supabase CLI: `npm install -g supabase`
3. Link project: `supabase link --project-ref YOUR-PROJECT-REF`
4. Apply schema: `supabase db push`

**Note:** Each guild gets its own Supabase database for data isolation.

## 🤖 Commands

### User Commands
- `/harvest <amount>` - Log spice sand collected
- `/refinery` - View your stats (private)
- `/leaderboard` - Top collectors in guild
- `/ledger` - Your harvest history (private)
- `/expedition <id>` - View expedition details
- `/help` - Command list (private)

### Team Commands
- `/split <total> <users> [guild:10]` - Split expedition with guild cut
  - Example: `/split total_sand:1000 users:"@user1 50 @user2 @user3" guild:15`
  - Users with percentages get exact amounts, others split equally
  - Guild cut taken off the top (default 10%)

### Guild Commands
- `/guild_treasury` - View guild treasury balance
- `/pending` - List all users with unpaid melange (admin only)
- `/guild_withdraw <user> <amount>` - Transfer from treasury (admin only)

### Admin Commands
- `/conversion <rate>` - Set sand-to-melange rate (default: 50)
- `/payment <user>` - Pay user's pending melange
- `/payroll` - Pay all pending melange
- `/reset confirm:True` - Reset all data

## 📊 How It Works

### Individual Harvests
```
/harvest 2500  →  50 melange owed (at 50:1 rate)
```

### Team Expeditions
```
/split total_sand:10000 users:"@harvester 30 @scout @pilot" guild:10

Result:
- Guild: 1000 sand (10% cut)
- Harvester: 2700 sand (30% of remaining)
- Scout: 3150 sand (35% of remaining) 
- Pilot: 3150 sand (35% of remaining)
```

### Guild Treasury
- Receives 10% from all expeditions
- Admins can withdraw to reward members
- Tracks all transactions for audit

## 🚀 Deployment

### Fly.io (Production)
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Setup
fly auth login
fly apps create your-bot-name
fly secrets set DISCORD_TOKEN=xxx DATABASE_URL=xxx
fly deploy
```

### Database Schema
Each guild database contains:
- `users` - Discord user info and melange totals
- `deposits` - Individual sand deposits with payment status
- `expeditions` - Team expedition records with guild cuts
- `expedition_participants` - Individual participation records
- `guild_treasury` - Guild's accumulated resources
- `guild_transactions` - Treasury operation audit trail
- `settings` - Bot configuration

## 🔧 Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Bot token | ✅ |
| `DATABASE_URL` | Supabase connection string | ✅ |
| `SAND_PER_MELANGE` | Conversion rate | ❌ (default: 50) |

## 🛡️ Permissions

- **Basic Commands**: All guild members
- **Admin Commands**: Discord administrators only
- **Private Responses**: Personal financial data is ephemeral

## 🏗️ Architecture

- **Discord.py**: Modern slash commands with async/await
- **Supabase**: PostgreSQL database per guild
- **Per-Guild Isolation**: Each guild has separate database
- **Fast Startup**: Minimal database checks, no migrations during boot
- **Health Checks**: `/health` endpoint for monitoring

---

**Status:** Active  
**Game:** Dune: Awakening  
**Deployment:** Fly.io + Supabase