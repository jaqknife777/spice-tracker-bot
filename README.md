# 🏜️ Spice Tracker Bot

[![CI/CD Pipeline](https://github.com/jaqknife777/spice-tracker-bot/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/jaqknife777/spice-tracker-bot/actions/workflows/ci.yml)

A Discord bot for **Dune: Awakening** that helps guilds track spice sand collection, convert to melange, and manage team spice splits for operations.

## ✨ Features

- **Spice Sand Tracking** - Log individual spice deposits with automatic melange conversion
- **Team Spice Splits** - Calculate fair distribution among team members with customizable harvester cuts
- **Leaderboards** - Track top spice collectors in your guild
- **User Statistics** - View personal refining stats and totals
- **Admin Controls** - Configurable conversion rates and data management
- **Rate Limiting** - Prevents spam and abuse
- **Supabase PostgreSQL** - Production-ready database with automatic backups

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Discord Bot Token
- Discord Application Client ID
- Supabase Account

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/jaqknife777/spice-tracker-bot.git
   cd spice-tracker-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   CLIENT_ID=your_client_id_here
   DATABASE_URL=your_supabase_database_url
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 🚀 Fly.io Deployment

### Quick Deploy
[![Deploy on Fly.io](https://fly.io/static/images/deploy/button.svg)](https://fly.io/apps/new?remote=https://github.com/jaqknife777/spice-tracker-bot)

### Automatic Deployment (Recommended)
Your bot automatically deploys to Fly.io when you push working code to main branch!

**Setup:**
1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Login to Fly**: `fly auth login`
3. **Create app**: `fly apps create spice-tracker-bot`
4. **Get Fly API token**: [Fly.io Dashboard](https://fly.io/user/personal_access_tokens) → New Token
5. **Add GitHub secrets**:
   - `FLY_API_TOKEN` = Your Fly API token
6. **Push to main** → Automatic deployment! 🚀

**How it works:**
- Push to main → CI tests run → If tests pass → Auto-deploy to Fly.io
- If tests fail → No deployment (protects against broken code)

### Manual Setup
1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Create app**: `fly apps create spice-tracker-bot`
4. **Set secrets**:
   ```bash
   fly secrets set DISCORD_TOKEN=your_bot_token_here
   fly secrets set CLIENT_ID=your_client_id_here
   fly secrets set DATABASE_URL=your_supabase_database_url
   ```
5. **Deploy**: `fly deploy`

### Features
- **Global edge deployment** with automatic scaling
- **Custom domains** with automatic SSL
- **PostgreSQL** via Supabase
- **Built-in monitoring** and logs
- **Health checks** at `/health`
- **Zero-downtime deployments**

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Your Discord bot token | ✅ Yes |
| `CLIENT_ID` | Discord application client ID | ✅ Yes |
| `DATABASE_URL` | Supabase PostgreSQL connection string | ✅ Yes |
| `ADMIN_ROLE_IDS` | Comma-separated list of Discord role IDs for admin access | ❌ No |
| `ALLOWED_ROLE_IDS` | Comma-separated list of Discord role IDs for basic bot access | ❌ No |
| `SAND_PER_MELANGE` | Amount of spice sand required for 1 melange | ❌ No (default: 50) |
| `PORT` | Health check server port | ❌ No (default: 8080) |

### Troubleshooting
- **Bot offline?** Check Fly.io logs: `fly logs -a spice-tracker-bot`
- **Build failed?** Check Fly.io build logs
- **CI failing?** Fix tests before deployment
- **Need help?** Check GitHub Actions logs and Fly.io dashboard

## 🗄️ Supabase Database Setup

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Enter project name: `spice-tracker-bot`
5. Enter a strong database password (save this!)
6. Choose a region closest to your users
7. Click "Create new project"
8. Wait for project setup (2-3 minutes)

### Step 2: Get Project Reference

1. In your Supabase dashboard, note the project reference from the URL:
   ```
   https://supabase.com/dashboard/project/[YOUR-PROJECT-REF]
   ```
2. Save this reference - you'll need it for the setup

### Step 3: Install Supabase CLI

```bash
# Install globally
npm install -g supabase

# Verify installation
supabase --version
```

### Step 4: Run Setup Script

#### Option A: Automated Setup (Recommended)

**Linux/macOS:**
```bash
# Make script executable
chmod +x supabase/setup.sh

# Run setup
./supabase/setup.sh
```

**Windows PowerShell:**
```powershell
# Run setup script
.\supabase\setup.ps1

# Or with project reference
.\supabase\setup.ps1 -ProjectRef "your-project-ref"
```

#### Option B: Manual Setup

```bash
# Navigate to project root
cd spice-tracker-bot

# Initialize Supabase
supabase init

# Link to your project
supabase link --project-ref [YOUR-PROJECT-REF]

# Run migrations
supabase db push

# Optional: Seed with sample data
supabase db reset --linked
```

### Database Schema

The bot uses **Supabase PostgreSQL** for data persistence with these main tables:

1. **`users`** - Player information and melange totals
2. **`deposits`** - Individual spice sand harvests
3. **`settings`** - Bot configuration options
4. **`audit_log`** - Change tracking and history

### Get Database Connection String

1. Go to Settings → Database in your Supabase dashboard
2. Copy the connection string from "Connection string" section
3. Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres`
4. Set as `DATABASE_URL` environment variable

## 🤖 Commands

### User Commands
- `/harvest <amount>` - Log spice sand you've collected
- `/sand <amount>` - Alias for harvest command
- `/refinery` - View your personal spice statistics
- `/status` - Alias for refinery command
- `/leaderboard [limit]` - See top spice collectors in the server
- `/top [limit]` - Alias for leaderboard command
- `/ledger` - View your complete harvest ledger
- `/deposits` - Alias for ledger command
- `/expedition <id>` - View details of a specific expedition
- `/exp <id>` - Alias for expedition command
- `/split <total_sand> <participants> [harvester%] [type]` - Split spice among expedition members using Discord mentions (e.g., @username1 @username2). Default: 10% harvester share, 'crawler' type. Types: solo, crawler, harvester
- `/help` - Display all available commands
- `/commands` - Alias for help command

### Admin Commands
- `/conversion <rate>` - Change sand-to-melange conversion rate (default: 50 sand = 1 melange)
- `/rate <rate>` - Alias for conversion command
- `/payment <user>` - Process payment for a harvester's deposits
- `/pay <user>` - Alias for payment command
- `/payroll` - Process payments for all unpaid harvesters
- `/payall` - Alias for payroll command
- `/reset confirm:True` - Reset all user statistics (requires confirmation)

## 📊 Example Usage

### Individual Spice Logging
```
/harvest 2500
```
*Logs 2,500 spice sand (converts to 50 melange at default rate)*

### Team Spice Split
```
/split 50000 @username1 @username2 25
```
*Splits 50,000 sand with 25% harvester cut among 3 participants (including initiator)*

**Result:**
- **Harvester gets:** 12,500 sand (250 melange)
- **Remaining sand:** 37,500 sand (750 melange)
- **Each participant gets:** 18,750 sand (375 melange)

**Note:** The command now creates expedition records and tracks melange owed for payout. The command initiator automatically becomes the primary harvester. Participants are specified using Discord mentions (@username), and the remaining share is split equally among all participants. Expedition types (solo, crawler, harvester) help categorize different types of operations.

## 🏗️ System Architecture

### Bot Framework
- **Discord.py** with slash command support
- **Async/await** - Non-blocking operations for better performance
- **Interaction deferring** - Prevents command timeouts during database operations

### Data Storage
- **Supabase PostgreSQL** with asyncpg for persistent data storage
- **Enhanced Schema**: 
  - `users` table: Tracks user IDs, usernames, melange totals, and timestamps
  - `deposits` table: Records individual spice sand deposits with payment status and type (solo/expedition)
  - `expeditions` table: Tracks expedition details including initiator, total sand, harvester percentage, and expedition type (solo/crawler/harvester)
  - `expedition_participants` table: Records individual participant shares and roles in expeditions
  - `settings` table: Stores configurable bot settings like conversion rates
- **Production-ready database** with automatic backups, scaling, and monitoring

### Command Structure
- **Slash Commands** - Modern Discord interaction pattern
- **Permission-based Access** - Admin-only commands for configuration and data management
- **Rate Limiting** - In-memory rate limiter to prevent spam and abuse
- **Input Validation** - Min/max value constraints on user inputs

## 🚀 CI/CD Pipeline

### GitHub Actions
This project uses GitHub Actions for continuous integration and deployment:

- **Automated Testing** - Runs on every push to main and pull request
- **Multi-Python Support** - Tests against Python 3.11, 3.12, and 3.13
- **Dependency Caching** - Fast builds with pip dependency caching
- **Automatic Deployment** - Deploys to Fly.io when tests pass on main branch
- **Status Badge** - Shows CI/CD status in README and pull requests

### Workflow Details
The CI/CD pipeline automatically:

1. **Checks out code** from the repository
2. **Sets up Python** environment for each version
3. **Installs dependencies** from requirements.txt
4. **Runs test suite** using pytest
5. **Performs code quality checks** with flake8 linting
6. **Runs security audits** with bandit and safety
7. **Checks dependencies** for vulnerabilities
8. **Deploys to Fly.io** if all tests pass on main branch

### CI Status
- 🟢 **Green** - All tests and checks passing, ready for Fly.io deployment
- 🔴 **Red** - Tests or checks failing (check the Actions tab for details)
- 🟡 **Yellow** - Tests running or partially complete
- 🚀 **Deploying** - Tests passed, deploying to Fly.io

## 📝 Configuration

### Conversion Rate
Default: 50 sand = 1 melange (changeable with `/conversion`)

### Rate Limiting
- Commands are rate-limited per user to prevent spam
- Configurable cooldowns for different command types

### Admin Role Configuration

You can grant admin permissions to specific Discord roles by setting the `ADMIN_ROLE_IDS` environment variable:

```env
# Single admin role
ADMIN_ROLE_IDS=123456789

# Multiple admin roles (comma-separated)
ADMIN_ROLE_IDS=123456789,987654321,555666777
```

**How it works:**
- Users with these role IDs will have admin permissions
- This works **in addition to** Discord administrator permissions
- If no admin roles are configured, only Discord administrators can use admin commands
- Role IDs can be found by enabling Developer Mode in Discord and right-clicking on roles

**Admin commands include:**
- `/conversion` - Modify sand to melange conversion rate
- `/payment` - Process payments for harvesters
- `/payroll` - Process all pending payments
- `/reset` - Reset all user statistics (use with caution)

### Allowed Role Configuration

You can restrict basic bot access to specific Discord roles by setting the `ALLOWED_ROLE_IDS` environment variable:

```env
# Single allowed role
ALLOWED_ROLE_IDS=111222333

# Multiple allowed roles (comma-separated)
ALLOWED_ROLE_IDS=111222333,444555666,777888999
```

**How it works:**
- Users with these role IDs can use basic bot commands
- If no allowed roles are configured, **all users** can use the bot
- This provides an additional layer of access control beyond Discord permissions
- Useful for restricting bot usage to specific guild roles or membership tiers

## 🛡️ Security & Permissions

- **Discord Permissions Integration** - Uses Discord's built-in permission system
- **Admin Verification** - Commands like `/conversion` and `/reset` require Administrator permissions or admin roles
- **Custom Admin Roles** - Configure specific Discord role IDs for admin access via environment variables
- **Rate Limiting** - Per-user, per-command cooldowns stored in memory
- **Input Sanitization** - Validates user inputs for type and range
- **Environment Variables** - Sensitive data stored securely in Fly.io secrets

## 🎮 Game Mechanics

- **Progressive Conversion** - Sand accumulates and converts to melange at configurable thresholds
- **Persistent Progress** - User statistics persist between bot restarts
- **Leaderboard System** - Encourages competition through ranking display
- **Administrative Controls** - Admins can modify conversion rates and reset all data
- **Payment System** - Track paid vs unpaid harvests for guild management

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 🎮 About Dune: Awakening

This bot is designed for the Dune: Awakening MMO game to help guilds manage spice operations, track resource collection, and fairly distribute rewards among team members.

---

**Bot Status:** Active and maintained  
**Game:** Dune: Awakening  
**Version:** 1.0.0  
**Deployment:** Fly.io + Supabase