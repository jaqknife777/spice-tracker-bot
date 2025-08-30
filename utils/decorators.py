"""
Decorators for Discord bot commands.
"""

import time
import asyncio
from utils.logger import logger
from utils.helpers import send_response


def handle_interaction_expiration(func):
    """Decorator to handle interaction expiration gracefully"""
    async def wrapper(interaction, *args, **kwargs):
        command_start_time = time.time()
        use_followup = True
        
        # Check if this command requires guild context
        if not hasattr(interaction, 'guild') or not interaction.guild:
            try:
                await send_response(interaction, "❌ This command can only be used in a Discord server, not in direct messages.", use_followup=False, ephemeral=True)
            except:
                # If we can't send a response, just log it
                logger.warning(f"Command {func.__name__} called in DM context, cannot proceed")
            return
        
        try:
            # Validate interaction before attempting defer
            if not hasattr(interaction, 'response') or not hasattr(interaction, 'user'):
                logger.warning(f"Invalid interaction object for {func.__name__}, falling back to channel messages")
                use_followup = False
                return
            
            # Try to defer the response with a timeout
            defer_start = time.time()
            await asyncio.wait_for(interaction.response.defer(thinking=True), timeout=5.0)
            defer_time = time.time() - defer_start
            logger.info(f"Interaction deferred successfully", 
                       command=func.__name__, 
                       defer_time=f"{defer_time:.3f}s")
            
        except asyncio.TimeoutError:
            # Defer timed out, fall back to channel messages
            use_followup = False
            defer_time = time.time() - defer_start
            logger.warning(f"Defer timeout for {func.__name__} command", 
                           user=interaction.user.display_name, 
                           user_id=interaction.user.id, 
                           defer_time=f"{defer_time:.3f}s")
        except Exception as defer_error:
            if "Unknown interaction" in str(defer_error) or "NotFound" in str(defer_error):
                # Interaction expired, we'll need to send channel messages
                use_followup = False
                defer_time = time.time() - defer_start
                logger.warning(f"Interaction expired for {func.__name__} command", 
                               user=interaction.user.display_name, 
                               user_id=interaction.user.id, 
                               defer_time=f"{defer_time:.3f}s")
            else:
                # Re-raise if it's a different error
                raise defer_error
        
        # Add use_followup to kwargs so the function can use it
        kwargs['use_followup'] = use_followup
        
        try:
            function_start = time.time()
            result = await func(interaction, *args, **kwargs)
            function_time = time.time() - function_start
            total_time = time.time() - command_start_time
            
            logger.command_success(
                command=func.__name__,
                user_id=str(interaction.user.id),
                username=interaction.user.display_name,
                execution_time=function_time,
                total_time=total_time,
                guild_id=str(interaction.guild.id) if interaction.guild else None,
                guild_name=interaction.guild.name if interaction.guild else None
            )
            
            return result
        except Exception as func_error:
            function_start = time.time()
            function_time = time.time() - function_start
            total_time = time.time() - command_start_time
            
            # Log the error but don't re-raise it
            logger.command_error(
                command=func.__name__,
                user_id=str(interaction.user.id),
                username=interaction.user.display_name,
                error=str(func_error),
                execution_time=function_time,
                total_time=total_time,
                guild_id=str(interaction.guild.id) if interaction.guild else None,
                guild_name=interaction.guild.name if interaction.guild else None
            )
            
            # Try to send error response, but don't let it fail the decorator
            try:
                # Check if interaction is still valid before trying to send response
                # Guild can be None for DMs, so we only require channel
                if hasattr(interaction, 'channel') and interaction.channel:
                    await send_response(interaction, "❌ An error occurred while processing your command.", use_followup=use_followup, ephemeral=True)
                else:
                    logger.warning(f"Interaction invalid for {func.__name__}, skipping error response")
            except Exception as response_error:
                logger.error(f"Failed to send error response for {func.__name__}: {response_error}")
                # Don't re-raise - just log the failure
            
            # Return None to indicate error occurred
            return None
    
    return wrapper


def monitor_performance(operation_name: str = None):
    """Decorator to monitor performance of database operations and other timed operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log performance metrics
                logger.info(f"{operation} completed successfully", 
                           execution_time=f"{execution_time:.3f}s",
                           operation=operation)
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{operation} failed", 
                           execution_time=f"{execution_time:.3f}s",
                           operation=operation,
                           error=str(e))
                raise
        
        return wrapper
    return decorator
