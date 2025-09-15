"""
Spice Tracker Bot - Main bot file
A Discord bot for converting spice sand to melange and tracking production in Dune: Awakening.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional
import os
import time
import traceback
import http.server
import socketserver
import threading
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

# Import utility modules
from utils.logger import logger
from utils.helpers import get_database
from utils.base_command import log_permission_overrides

# Import command metadata (currently unused but kept for future use)
# from commands import COMMAND_METADATA

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
# For slash commands, we don't need message_content intent
intents.message_content = False
intents.reactions = True
intents.guilds = True
intents.guild_messages = True

# Note: command_prefix is set but not used since we're using slash commands
# The prefix commands are kept for potential future use or debugging
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    bot_start_time = time.time()
    try:
        if bot.user:
            logger.bot_event(f"Bot started - {bot.user.name} ({bot.user.id}) in {len(bot.guilds)} guilds")
            logger.info(f"Bot online: {bot.user.name}#{bot.user.discriminator}")
        else:
            logger.bot_event("Bot started - Unknown")
            logger.info("Bot is online")

        logger.info("Starting bot initialization")

        # Test database connectivity
        try:
            logger.info("Testing database connection")
            db_init_start = time.time()
            await get_database().initialize()
            db_init_time = time.time() - db_init_start
            logger.bot_event("Database connection verified", db_init_time=f"{db_init_time:.3f}s")

        except Exception as error:
            db_init_time = time.time() - db_init_start
            logger.bot_event(f"Database connection failed: {error}", db_init_time=f"{db_init_time:.3f}s")
            logger.error(f"Database connection failed in {db_init_time:.3f}s", error=str(error), error_type=type(error).__name__)
            logger.debug("Database connection failure traceback", traceback=traceback.format_exc())
            return

        # Register commands BEFORE syncing
        logger.info("Registering commands")
        register_start = time.time()
        register_commands()
        register_time = time.time() - register_start
        logger.info("Command registration completed", register_time=f"{register_time:.3f}s")

        # Auto-sync commands on startup (can be disabled with AUTO_SYNC_COMMANDS=false)
        auto_sync = os.getenv('AUTO_SYNC_COMMANDS', 'true').lower() == 'true'
        if auto_sync:
            try:
                logger.info("Auto-syncing commands (global + guild)")

                # Global sync first to update all guilds
                global_synced = await bot.tree.sync()
                logger.info("Global sync completed", commands_synced=len(global_synced))

                # Guild-specific sync for immediate effect in current guilds
                guild_sync_count = 0
                for guild in bot.guilds:
                    try:
                        guild_synced = await bot.tree.sync(guild=guild)
                        guild_sync_count += len(guild_synced)
                        logger.info("Guild sync completed", guild_name=guild.name, commands_synced=len(guild_synced))
                    except Exception as guild_error:
                        logger.warning("Guild sync failed", guild_name=guild.name, error=str(guild_error))

                logger.info("Auto-sync completed", global_commands=len(global_synced), guild_commands=guild_sync_count)

            except Exception as sync_error:
                logger.error("Auto-sync failed", error=str(sync_error))
                logger.debug("Auto-sync failure traceback", traceback=traceback.format_exc())

        logger.info("Bot is ready! Use /sync command to sync slash commands")

        # Log permission overrides if any are configured
        log_permission_overrides()

        # Log total bot startup time
        total_startup_time = time.time() - bot_start_time
        logger.bot_event(f"Bot startup completed",
                         total_startup_time=f"{total_startup_time:.3f}s",
                         db_init_time=f"{db_init_time:.3f}s",
                         guild_count=len(bot.guilds))
        logger.info("Bot startup completed", total_startup_time=f"{total_startup_time:.3f}s")

    except Exception as error:
        total_startup_time = time.time() - bot_start_time
        logger.error("CRITICAL ERROR in on_ready", error=str(error), error_type=type(error).__name__, startup_time=f"{total_startup_time:.3f}s")
        logger.debug("on_ready failure traceback", traceback=traceback.format_exc())
        logger.error(f"Critical error in on_ready: {error}", startup_time=f"{total_startup_time:.3f}s")


# Register commands with the bot's command tree
def register_commands():
    """Register all commands explicitly with their exact signatures"""
    from commands import sand, refinery, leaderboard, split, help, reset, ledger, expedition, pay, payroll, treasury, guild_withdraw, pending, water, landsraad, perms, calc

    # Helper to allow env-based command renaming/prefixing
    # CMD_PREFIX: optional string prefix added to every command name
    # CMD_NAME_OVERRIDES: JSON or comma-separated mapping like "sand=harvest,calc=estimate"
    def _build_cmd_name_resolver():
        import json
        prefix = os.getenv('CMD_PREFIX', '')
        overrides_env = os.getenv('CMD_NAME_OVERRIDES', '')
        overrides = {}
        if overrides_env:
            try:
                overrides = json.loads(overrides_env)
            except Exception:
                # Fallback to comma-separated key=value pairs
                for pair in overrides_env.split(','):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key and value:
                            overrides[key] = value

        def cmd_name(base: str) -> str:
            name = overrides.get(base, base)
            return f"{prefix}{name}" if prefix else name

        return cmd_name

    cmd_name = _build_cmd_name_resolver()

    # Sand command (formerly harvest)
    @bot.tree.command(name=cmd_name("sand"), description="Convert spice sand into melange (50:1 ratio)")
    @app_commands.describe(amount="Amount of spice sand to convert (1-10,000)")
    async def sand_cmd(interaction: discord.Interaction, amount: int):  # noqa: F841
        await sand(interaction, amount)

    # Calc command (no DB write)
    @bot.tree.command(name=cmd_name("calc"), description="Estimate melange from a sand amount (no database update)")
    @app_commands.describe(amount="Amount of spice sand to calculate (min 1)")
    async def calc_cmd(interaction: discord.Interaction, amount: int):  # noqa: F841
        await calc(interaction, amount)

    # Refinery command
    @bot.tree.command(name=cmd_name("refinery"), description="View your melange production and payment status")
    async def refinery_cmd(interaction: discord.Interaction):  # noqa: F841
        await refinery(interaction)

    # Leaderboard command
    @bot.tree.command(name=cmd_name("leaderboard"), description="Display top spice refiners by melange production")
    @app_commands.describe(limit="Number of top refiners to display (5-25, default: 10)")
    async def leaderboard_cmd(interaction: discord.Interaction, limit: int = 10):  # noqa: F841
        await leaderboard(interaction, limit)



    # Split command
    @bot.tree.command(name=cmd_name("split"), description="Split spice sand among expedition members and convert to melange")
    @app_commands.describe(
        total_sand="Total spice sand to split and convert",
        users="Users and percentages: '@user1 50 @user2 @user3' (users without % split equally)",
        guild="Guild cut percentage (default: 10)"
    )
    async def split_cmd(interaction: discord.Interaction, total_sand: int, users: str, guild: int = 10):  # noqa: F841
        await split(interaction, total_sand, users, guild)

    # Help command
    @bot.tree.command(name=cmd_name("help"), description="Show all available spice tracking commands")
    async def help_cmd(interaction: discord.Interaction):  # noqa: F841
        await help(interaction)

    # Perms command
    @bot.tree.command(name=cmd_name("perms"), description="Show your permission status and matched roles")
    async def perms_cmd(interaction: discord.Interaction):  # noqa: F841
        await perms(interaction)

    # Reset command
    @bot.tree.command(name=cmd_name("reset"), description="Reset all spice refinery statistics (Admin only - USE WITH CAUTION)")
    @app_commands.describe(confirm="Confirm that you want to delete all refinery data (True/False)")
    async def reset_cmd(interaction: discord.Interaction, confirm: bool):  # noqa: F841
        await reset(interaction, confirm)

    # Ledger command
    @bot.tree.command(name=cmd_name("ledger"), description="View your complete spice harvest ledger")
    async def ledger_cmd(interaction: discord.Interaction):  # noqa: F841
        await ledger(interaction)

    # Expedition command
    @bot.tree.command(name=cmd_name("expedition"), description="View details of a specific expedition")
    @app_commands.describe(expedition_id="ID of the expedition to view")
    async def expedition_cmd(interaction: discord.Interaction, expedition_id: int):  # noqa: F841
        await expedition(interaction, expedition_id)

    # Pay command (formerly payment)
    @bot.tree.command(name=cmd_name("pay"), description="Process melange payment for a user (Admin only)")
    @app_commands.describe(
        user="User to pay",
        amount="Amount of melange to pay (optional, defaults to full pending amount)"
    )
    async def pay_cmd(interaction: discord.Interaction, user: discord.Member, amount: int = None):  # noqa: F841
        await pay(interaction, user, amount)

    # Payroll command
    @bot.tree.command(name=cmd_name("payroll"), description="Process payments for all unpaid harvesters (Admin only)")
    async def payroll_cmd(interaction: discord.Interaction):  # noqa: F841
        await payroll(interaction)

    # Treasury command
    @bot.tree.command(name=cmd_name("treasury"), description="View guild treasury balance and statistics")
    async def treasury_cmd(interaction: discord.Interaction):  # noqa: F841
        await treasury(interaction)

    # Guild Withdraw command
    @bot.tree.command(name=cmd_name("guild_withdraw"), description="Withdraw sand from guild treasury to give to a user (Admin only)")
    @app_commands.describe(
        user="User to give sand to",
        amount="Amount of sand to withdraw from guild treasury"
    )
    async def guild_withdraw_cmd(interaction: discord.Interaction, user: discord.Member, amount: int):  # noqa: F841
        await guild_withdraw(interaction, user, amount)

    # Pending command
    @bot.tree.command(name=cmd_name("pending"), description="View all users with pending melange payments (Admin only)")
    async def pending_cmd(interaction: discord.Interaction):  # noqa: F841
        await pending(interaction)

    # Water command
    @bot.tree.command(name=cmd_name("water"), description="Request a water delivery to a specific location")
    @app_commands.describe(destination="Destination for water delivery (default: DD base)")
    async def water_cmd(interaction: discord.Interaction, destination: str = "DD base"):  # noqa: F841
        await water(interaction, destination)

    # Landsraad command
    @bot.tree.command(name=cmd_name("landsraad"), description="Manage the landsraad bonus for melange conversion")
    @app_commands.describe(
        action="Action to perform: 'status', 'enable', 'disable'",
        confirm="Confirmation required for enable/disable actions"
    )
    async def landsraad_cmd(interaction: discord.Interaction, action: str, confirm: bool = False):  # noqa: F841
        await landsraad(interaction, action, confirm)

    # Sync command (slash command version)
    @bot.tree.command(name=cmd_name("sync"), description="Sync slash commands (Bot Owner Only)")
    async def sync_cmd(interaction: discord.Interaction):  # noqa: F841
        if interaction.user.id != int(os.getenv('BOT_OWNER_ID', '0')):
            await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)
            synced = await bot.tree.sync()
            await interaction.followup.send(f"✅ Synced {len(synced)} commands successfully!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error syncing commands: {e}", ephemeral=True)

    logger.info("Registered all commands explicitly")


# Manual sync command (recommended by Discord.py docs)
@commands.command()
@commands.guild_only()
# @commands.is_owner()
async def sync(
    ctx: commands.Context,
    guilds: commands.Greedy[discord.Object],
    spec: Optional[Literal["~", "*", "^"]] = None
) -> None:
    """Sync slash commands. Use !sync for global, !sync ~ for current guild."""
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

bot.add_command(sync)


# Error handling
@bot.event
async def on_command_error(ctx, error):
    error_start = time.time()
    logger.error("Command error", event_type="command_error",
                 command=ctx.command.name if ctx.command else "unknown",
                 user_id=str(ctx.author.id) if ctx.author else "unknown",
                 username=ctx.author.display_name if ctx.author else "unknown",
                 error=str(error))

@bot.event
async def on_error(event, *args, **kwargs):
    error_start = time.time()
    logger.error("Discord event error", event_type="discord_error",
                 event=event, args=str(args), kwargs=str(kwargs))

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reaction additions for water delivery completion"""
    # Ignore bot's own reactions
    if user.bot:
        return

    # Check if it's a checkmark reaction on a water delivery request
    if str(reaction.emoji) == "✅":
        try:
            # Get the message content to check if it's a water request
            message = reaction.message
            if message and message.embeds:
                embed = message.embeds[0]
                if embed.title and "💧 Water Delivery Request" in embed.title:
                    # Extract the requester from the embed fields
                    requester_mention = None
                    for field in embed.fields:
                        if field.name == "👤 Requester":
                            requester_mention = field.value
                            break

                    if requester_mention:
                        # Update the embed to show completion
                        updated_embed = discord.Embed(
                            title="💧 Water Delivery Request",
                            description=embed.description,
                            color=0x27AE60,  # Green color for completed
                            timestamp=message.created_at
                        )

                        # Copy all fields but update status
                        for field in embed.fields:
                            if field.name == "📋 Status":
                                updated_embed.add_field(
                                    name=field.name,
                                    value="✅ Completed by admin",
                                    inline=field.inline
                                )
                            else:
                                updated_embed.add_field(
                                    name=field.name,
                                    value=field.value,
                                    inline=field.inline
                                )

                        # Add completion info
                        updated_embed.add_field(
                            name="✅ Completed by",
                            value=f"{user.mention}",
                            inline=False
                        )

                        # Update the message
                        await message.edit(embed=updated_embed)

                        # Send notification to the original requester
                        try:
                            # Extract user ID from mention
                            if requester_mention.startswith("<@") and requester_mention.endswith(">"):
                                user_id = int(requester_mention[2:-1])
                                requester = await bot.fetch_user(user_id)
                                if requester:
                                    notification_embed = discord.Embed(
                                        title="💧 Water Delivery Complete!",
                                        description=f"Your water delivery request has been completed by {user.mention}",
                                        color=0x27AE60,
                                        timestamp=discord.utils.utcnow()
                                    )
                                    notification_embed.add_field(
                                        name="📍 Destination",
                                        value=embed.description.replace("**Location:** ", ""),
                                        inline=False
                                    )

                                    await requester.send(embed=notification_embed)
                        except Exception as e:
                            logger.warning(f"Could not send notification to requester: {e}")

                        # Log the completion
                        logger.info(f"Water delivery completed by admin",
                                   admin_user_id=str(user.id),
                                   admin_username=user.display_name,
                                   requester_mention=requester_mention,
                                   guild_id=str(message.guild.id) if message.guild else None)

        except Exception as e:
            logger.error(f"Error handling water delivery reaction: {e}")


# Fly.io health check endpoint
def start_health_server():
    """Start a robust HTTP server for Fly.io health checks with keep-alive"""
    class HealthHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            request_start = time.time()

            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Connection', 'keep-alive')
                self.end_headers()

                # Return bot status information
                status = {
                    'status': 'healthy',
                    'bot_ready': bot.is_ready(),
                    'guild_count': len(bot.guilds),
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                }
                self.wfile.write(str(status).encode())

                request_time = time.time() - request_start
                logger.info(f"Health check request completed",
                           request_time=f"{request_time:.3f}s",
                           bot_ready=bot.is_ready(),
                           guild_count=len(bot.guilds))

            elif self.path == '/ping':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'pong')

                request_time = time.time() - request_start
                logger.info(f"Ping request completed", request_time=f"{request_time:.3f}s")

            else:
                self.send_response(404)
                self.end_headers()

                request_time = time.time() - request_start
                logger.warning(f"Invalid health check request",
                               path=self.path,
                               request_time=f"{request_time:.3f}s")

        def log_message(self, format, *args):
            pass  # Suppress HTTP server logs

    try:
        port = int(os.getenv('PORT', 8080))
        with socketserver.TCPServer(("", port), HealthHandler) as httpd:
            logger.bot_event(f"Health server started on port {port}")
            logger.info("Health check server started", port=port)
            httpd.serve_forever()
    except Exception as e:
        logger.error("Health server failed to start", error=str(e))


# Run the bot
if __name__ == '__main__':
    # Start health check server in a separate thread for Fly.io
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # Start a keep-alive thread to prevent machine from going idle
    def keep_alive():
        """Send periodic pings to keep the machine alive"""
        ping_count = 0
        while True:
            try:
                time.sleep(300)  # Every 5 minutes
                ping_start = time.time()
                response = requests.get('http://localhost:8080/ping', timeout=5)
                ping_time = time.time() - ping_start
                ping_count += 1

                logger.info(f"Keep-alive ping completed",
                           ping_count=ping_count,
                           ping_time=f"{ping_time:.3f}s",
                           status_code=response.status_code)

            except Exception as e:
                ping_count += 1
                logger.warning(f"Keep-alive ping failed",
                               ping_count=ping_count,
                               error=str(e))
                pass  # Ignore errors, just keep trying

    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()

    # Validate Supabase connection string is a direct (non-pooled) URL on port 5432
    database_url = os.getenv('DATABASE_URL', '')
    try:
        if database_url:
            parsed = urlparse(database_url)
            # Only validate for postgres URLs that target Supabase
            if parsed.scheme.startswith('postgres'):
                hostname = (parsed.hostname or '').lower()
                is_supabase = 'supabase.' in hostname
                if is_supabase:
                    # Strict validation against the documented direct connection format
                    errors = []

                    # 1) Scheme must be postgresql+asyncpg
                    if parsed.scheme != 'postgresql+asyncpg':
                        errors.append("scheme must be 'postgresql+asyncpg'")

                    # 2) Host must match db.[PROJECT].supabase.co (or .supabase.net)
                    valid_host = (
                        hostname.startswith('db.') and (hostname.endswith('.supabase.co') or hostname.endswith('.supabase.net'))
                    )
                    if not valid_host:
                        errors.append("host must be 'db.[PROJECT].supabase.co' (or .supabase.net)")

                    # 3) Port must be 5432 (non-pooled direct connection)
                    port = parsed.port
                    if port is None or port != 5432:
                        errors.append("port must be 5432 (direct, non-pooled)")

                    # 4) Database name path must be present (e.g., /postgres)
                    if not parsed.path or parsed.path == '/':
                        errors.append("database name missing in path (e.g., '/postgres')")

                    if errors:
                        for issue in errors:
                            logger.error("Invalid Supabase DATABASE_URL: " + issue, hostname=hostname)
                        logger.error("Example format: postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres")
                        exit(1)
    except Exception as e:
        logger.warning("DATABASE_URL validation failed; proceeding anyway", error=str(e))

    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable is not set")
        logger.error("Please set the DISCORD_TOKEN environment variable in Fly.io or your .env file")
        exit(1)

    startup_start = time.time()
    logger.bot_event(f"Bot starting - Token present: {bool(token)}")
    logger.info("Starting Discord bot")

    try:
        bot.run(token)
    except Exception as e:
        startup_time = time.time() - startup_start
        logger.error(f"Bot startup failed",
                     startup_time=f"{startup_time:.3f}s",
                     error=str(e))
        raise e
