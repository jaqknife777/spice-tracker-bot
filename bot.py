"""
Spice Tracker Bot - Main bot file
A Discord bot for tracking spice sand harvests and melange production in Dune: Awakening.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional
import os
import time
import http.server
import socketserver
import threading
import requests
from dotenv import load_dotenv

# Import utility modules
from utils.logger import logger
from utils.helpers import get_database

# Import command metadata
from commands import COMMAND_METADATA

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
            print(f'{bot.user.name}#{bot.user.discriminator} is online!')
        else:
            logger.bot_event("Bot started - Unknown")
            print('Bot is online!')
        
        print("🔄 Starting bot initialization...")
        
        # Test database connectivity
        try:
            print("🔗 Testing database connection...")
            db_init_start = time.time()
            await get_database().initialize()
            db_init_time = time.time() - db_init_start
            logger.bot_event("Database connection verified", db_init_time=f"{db_init_time:.3f}s")
                
        except Exception as error:
            db_init_time = time.time() - db_init_start
            logger.bot_event(f"Database connection failed: {error}", db_init_time=f"{db_init_time:.3f}s")
            print(f'❌ Database connection failed in {db_init_time:.3f}s: {error}')
            print(f'❌ Error type: {type(error).__name__}')
            import traceback
            print(f'❌ Full traceback: {traceback.format_exc()}')
            return
        
        # Register commands BEFORE syncing
        print("🔧 Registering commands...")
        register_start = time.time()
        register_commands()
        register_time = time.time() - register_start
        print(f"✅ Command registration completed in {register_time:.3f}s")
        
        # Commands registered, ready for manual sync
        print("🎉 Bot is ready! Use the !sync command to sync slash commands.")
        
        # Log total bot startup time
        total_startup_time = time.time() - bot_start_time
        logger.bot_event(f"Bot startup completed", 
                         total_startup_time=f"{total_startup_time:.3f}s",
                         db_init_time=f"{db_init_time:.3f}s",
                         guild_count=len(bot.guilds))
        print(f"🚀 Bot startup completed in {total_startup_time:.3f}s")
            
    except Exception as error:
        total_startup_time = time.time() - bot_start_time
        print(f'❌ CRITICAL ERROR in on_ready: {error}')
        print(f'❌ Error type: {type(error).__name__}')
        print(f'❌ Startup time: {total_startup_time:.3f}s')
        import traceback
        print(f'❌ Full traceback: {traceback.format_exc()}')
        logger.error(f"Critical error in on_ready: {error}", startup_time=f"{total_startup_time:.3f}s")


# Register commands with the bot's command tree
def register_commands():
    """Register all commands explicitly with their exact signatures"""
    from commands import harvest, refinery, leaderboard, conversion, split, help, reset, ledger, expedition, payment, payroll, guild_treasury, guild_withdraw, pending
    
    # Harvest command
    @bot.tree.command(name="harvest", description="Log spice sand harvests and calculate melange conversion")
    @app_commands.describe(amount="Amount of spice sand harvested (1-10,000)")
    async def harvest_cmd(interaction: discord.Interaction, amount: int):  # noqa: F841
        await harvest(interaction, amount, True)
    
    # Refinery command
    @bot.tree.command(name="refinery", description="View your spice refinery statistics and progress")
    async def refinery_cmd(interaction: discord.Interaction):  # noqa: F841
        await refinery(interaction, True)
    
    # Leaderboard command
    @bot.tree.command(name="leaderboard", description="Display top spice refiners by melange production")
    @app_commands.describe(limit="Number of top refiners to display (5-25, default: 10)")
    async def leaderboard_cmd(interaction: discord.Interaction, limit: int = 10):  # noqa: F841
        await leaderboard(interaction, limit, True)
    
    # Conversion command
    @bot.tree.command(name="conversion", description="View the current spice sand to melange conversion rate")
    async def conversion_cmd(interaction: discord.Interaction):  # noqa: F841
        await conversion(interaction, True)
    
    # Split command
    @bot.tree.command(name="split", description="Split harvested spice sand among expedition members with guild cut")
    @app_commands.describe(
        total_sand="Total spice sand to split",
        users="Users and percentages: '@user1 50 @user2 @user3' (users without % split equally)",
        guild="Guild cut percentage (default: 10)"
    )
    async def split_cmd(interaction: discord.Interaction, total_sand: int, users: str, guild: int = 10):  # noqa: F841
        await split(interaction, total_sand, users, guild, True)
    
    # Help command
    @bot.tree.command(name="help", description="Show all available spice tracking commands")
    async def help_cmd(interaction: discord.Interaction):  # noqa: F841
        await help(interaction, True)
    
    # Reset command
    @bot.tree.command(name="reset", description="Reset all spice refinery statistics (Admin only - USE WITH CAUTION)")
    @app_commands.describe(confirm="Confirm that you want to delete all refinery data (True/False)")
    async def reset_cmd(interaction: discord.Interaction, confirm: bool):  # noqa: F841
        await reset(interaction, confirm, True)
    
    # Ledger command
    @bot.tree.command(name="ledger", description="View your complete spice harvest ledger")
    async def ledger_cmd(interaction: discord.Interaction):  # noqa: F841
        await ledger(interaction, True)
    
    # Expedition command
    @bot.tree.command(name="expedition", description="View details of a specific expedition")
    @app_commands.describe(expedition_id="ID of the expedition to view")
    async def expedition_cmd(interaction: discord.Interaction, expedition_id: int):  # noqa: F841
        await expedition(interaction, expedition_id, True)
    
    # Payment command
    @bot.tree.command(name="payment", description="Process payment for a harvester's deposits (Admin only)")
    @app_commands.describe(user="Harvester to pay")
    async def payment_cmd(interaction: discord.Interaction, user: discord.Member):  # noqa: F841
        await payment(interaction, user, True)
    
    # Payroll command
    @bot.tree.command(name="payroll", description="Process payments for all unpaid harvesters (Admin only)")
    async def payroll_cmd(interaction: discord.Interaction):  # noqa: F841
        await payroll(interaction, True)
    
    # Guild Treasury command
    @bot.tree.command(name="guild_treasury", description="View guild treasury balance and statistics")
    async def guild_treasury_cmd(interaction: discord.Interaction):  # noqa: F841
        await guild_treasury(interaction, True)
    
    # Guild Withdraw command
    @bot.tree.command(name="guild_withdraw", description="Withdraw sand from guild treasury to give to a user (Admin only)")
    @app_commands.describe(
        user="User to give sand to",
        amount="Amount of sand to withdraw from guild treasury"
    )
    async def guild_withdraw_cmd(interaction: discord.Interaction, user: discord.Member, amount: int):  # noqa: F841
        await guild_withdraw(interaction, user, amount, True)
    
    # Pending command
    @bot.tree.command(name="pending", description="View all users with pending melange payments (Admin only)")
    async def pending_cmd(interaction: discord.Interaction):  # noqa: F841
        await pending(interaction, True)
    
    print(f"✅ Registered all commands explicitly")


# Manual sync command (recommended by Discord.py docs)
@commands.command()
@commands.guild_only()
@commands.is_owner()
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
    logger.error(f"Command error: {error}", event_type="command_error", 
                 command=ctx.command.name if ctx.command else "unknown",
                 user_id=str(ctx.author.id) if ctx.author else "unknown",
                 username=ctx.author.display_name if ctx.author else "unknown",
                 error=str(error))
    print(f'Command error: {error}')

@bot.event
async def on_error(event, *args, **kwargs):
    error_start = time.time()
    logger.error(f"Discord event error: {event}", event_type="discord_error",
                 event=event, args=str(args), kwargs=str(kwargs))
    print(f'Discord event error: {event}')


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
            print(f"Health check server started on port {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health server failed to start: {e}")
        print(f"Health server failed to start: {e}")


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
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable is not set")
        print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
        print("Please set the DISCORD_TOKEN environment variable in Fly.io or your .env file")
        exit(1)
    
    startup_start = time.time()
    logger.bot_event(f"Bot starting - Token present: {bool(token)}")
    print("Starting Discord bot...")
    
    try:
        bot.run(token)
    except Exception as e:
        startup_time = time.time() - startup_start
        logger.error(f"Bot startup failed", 
                     startup_time=f"{startup_time:.3f}s",
                     error=str(e))
        raise e
