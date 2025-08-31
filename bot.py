"""
Spice Tracker Bot - Main bot file
A Discord bot for tracking spice sand harvests and melange production in Dune: Awakening.
"""

import discord
from discord.ext import commands
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
        
        # Initialize database
        try:
            print("🗄️ Initializing database...")
            db_init_start = time.time()
            await get_database().initialize()
            db_init_time = time.time() - db_init_start
            logger.bot_event("Database initialized successfully", db_init_time=f"{db_init_time:.3f}s")
            print(f'✅ Database initialized successfully in {db_init_time:.3f}s.')
            
            # Clean up old deposits (older than 30 days)
            try:
                print("🧹 Cleaning up old deposits...")
                cleanup_start = time.time()
                cleaned_count = await get_database().cleanup_old_deposits(30)
                cleanup_time = time.time() - cleanup_start
                if cleaned_count > 0:
                    logger.bot_event(f"Cleaned up {cleaned_count} old paid deposits", cleanup_time=f"{cleanup_time:.3f}s")
                    print(f'✅ Cleaned up {cleaned_count} old paid deposits in {cleanup_time:.3f}s.')
                else:
                    logger.bot_event("No old deposits to clean up", cleanup_time=f"{cleanup_time:.3f}s")
                    print(f"✅ No old deposits to clean up in {cleanup_time:.3f}s.")
            except Exception as cleanup_error:
                cleanup_time = time.time() - cleanup_start
                logger.bot_event(f"Failed to clean up old deposits: {cleanup_error}", cleanup_time=f"{cleanup_time:.3f}s")
                print(f'⚠️ Failed to clean up old deposits in {cleanup_time:.3f}s: {cleanup_error}')
                
        except Exception as error:
            db_init_time = time.time() - db_init_start
            logger.bot_event(f"Failed to initialize database: {error}", db_init_time=f"{db_init_time:.3f}s")
            print(f'❌ Failed to initialize database in {db_init_time:.3f}s: {error}')
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
        
        # Sync slash commands
        try:
            print("🔄 Syncing slash commands...")
            sync_start = time.time()
            
            # Sync to guilds for immediate availability
            guild_sync_start = time.time()
            guild_sync_success = 0
            guild_sync_failed = 0
            for guild in bot.guilds:
                try:
                    guild_synced = await bot.tree.sync(guild=guild)
                    print(f'✅ Synced {len(guild_synced)} commands to guild: {guild.name}')
                    guild_sync_success += 1
                except Exception as guild_error:
                    print(f'⚠️ Failed to sync to guild {guild.name}: {guild_error}')
                    guild_sync_failed += 1
            
            guild_sync_time = time.time() - guild_sync_start
            logger.bot_event(f"Guild command sync completed", 
                           guild_sync_time=f"{guild_sync_time:.3f}s",
                           guilds_success=guild_sync_success,
                           guilds_failed=guild_sync_failed)
            
            # Sync globally (takes up to 1 hour to propagate)
            global_sync_start = time.time()
            synced = await bot.tree.sync()
            global_sync_time = time.time() - global_sync_start
            
            total_sync_time = time.time() - sync_start
            logger.bot_event(f"Command sync completed", 
                           total_sync_time=f"{total_sync_time:.3f}s",
                           guild_sync_time=f"{guild_sync_time:.3f}s",
                           global_sync_time=f"{global_sync_time:.3f}s",
                           commands_synced=len(synced))
            print(f'✅ Synced {len(synced)} commands in {total_sync_time:.3f}s.')
            print("🎉 Bot is fully ready!")
            
        except Exception as error:
            sync_time = time.time() - sync_start
            logger.bot_event(f"Command sync failed: {error}", sync_time=f"{sync_time:.3f}s")
            print(f'❌ Failed to sync commands in {sync_time:.3f}s: {error}')
            print(f'❌ Error type: {type(error).__name__}')
            import traceback
            print(f'❌ Full traceback: {traceback.format_exc()}')
        
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
    from commands import harvest, refinery, leaderboard, conversion, split, help, reset, ledger, expedition, payment, payroll
    
    # Harvest command
    @bot.tree.command(name="harvest", description="Log spice sand harvests and calculate melange conversion")
    async def harvest_cmd(interaction: discord.Interaction, amount: int):  # noqa: F841
        await harvest(interaction, amount, True)
    
    # Refinery command
    @bot.tree.command(name="refinery", description="View your spice refinery statistics and progress")
    async def refinery_cmd(interaction: discord.Interaction):  # noqa: F841
        await refinery(interaction, True)
    
    # Leaderboard command
    @bot.tree.command(name="leaderboard", description="Display top spice refiners by melange production")
    async def leaderboard_cmd(interaction: discord.Interaction, limit: int = 10):  # noqa: F841
        await leaderboard(interaction, limit, True)
    
    # Conversion command
    @bot.tree.command(name="conversion", description="View the current spice sand to melange conversion rate")
    async def conversion_cmd(interaction: discord.Interaction):  # noqa: F841
        await conversion(interaction, True)
    
    # Split command
    @bot.tree.command(name="split", description="Split harvested spice sand among expedition members")
    async def split_cmd(interaction: discord.Interaction, total_sand: int, users: str):  # noqa: F841
        await split(interaction, total_sand, users, True)
    
    # Help command
    @bot.tree.command(name="help", description="Show all available spice tracking commands")
    async def help_cmd(interaction: discord.Interaction):  # noqa: F841
        await help(interaction, True)
    
    # Reset command
    @bot.tree.command(name="reset", description="Reset all spice refinery statistics (Admin only - USE WITH CAUTION)")
    async def reset_cmd(interaction: discord.Interaction, confirm: bool):  # noqa: F841
        await reset(interaction, confirm, True)
    
    # Ledger command
    @bot.tree.command(name="ledger", description="View your complete spice harvest ledger")
    async def ledger_cmd(interaction: discord.Interaction):  # noqa: F841
        await ledger(interaction, True)
    
    # Expedition command
    @bot.tree.command(name="expedition", description="View details of a specific expedition")
    async def expedition_cmd(interaction: discord.Interaction, expedition_id: int):  # noqa: F841
        await expedition(interaction, expedition_id, True)
    
    # Payment command
    @bot.tree.command(name="payment", description="Process payment for a harvester's deposits (Admin only)")
    async def payment_cmd(interaction: discord.Interaction, user: discord.Member):  # noqa: F841
        await payment(interaction, user, True)
    
    # Payroll command
    @bot.tree.command(name="payroll", description="Process payments for all unpaid harvesters (Admin only)")
    async def payroll_cmd(interaction: discord.Interaction):  # noqa: F841
        await payroll(interaction, True)
    
    print(f"✅ Registered all commands explicitly")


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
