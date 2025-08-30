"""
Helper functions used across multiple commands.
"""

import os
from database import Database

# Initialize database (lazy initialization)
database = None

def get_database():
    """Get or create database instance"""
    global database
    if database is None:
        database = Database()
    return database

def get_sand_per_melange() -> int:
    """Get the spice sand to melange conversion rate from environment variables"""
    return int(os.getenv('SAND_PER_MELANGE', '50'))

async def send_response(interaction, content=None, embed=None, ephemeral=False, use_followup=True):
    """Helper function to send responses using the appropriate method based on use_followup"""
    import time
    from utils.logger import logger
    
    start_time = time.time()
    
    # Validate inputs with better error logging
    if not interaction:
        logger.error("send_response called with None interaction")
        return
    
    # Check if interaction has required attributes
    if not hasattr(interaction, 'channel') or not interaction.channel:
        logger.error(f"send_response called with invalid channel - interaction type: {type(interaction)}, channel: {getattr(interaction, 'channel', 'NO_CHANNEL_ATTR')}")
        return
    
    # Guild can be None for DMs, so we don't require it
    # But we do need to check if we're in a guild context for certain operations
    is_guild_context = hasattr(interaction, 'guild') and interaction.guild is not None
    
    try:
        if use_followup:
            if content:
                await interaction.followup.send(content, ephemeral=ephemeral)
            elif embed:
                await interaction.followup.send(embed=embed)
        else:
            if content:
                await interaction.channel.send(content)
            elif embed:
                await interaction.channel.send(embed=embed)
        
        response_time = time.time() - start_time
        logger.info(f"Response sent successfully", 
                   response_time=f"{response_time:.3f}s", 
                   use_followup=use_followup, 
                   has_content=content is not None, 
                   has_embed=embed is not None)
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Error sending response: {e}", 
                    response_time=f"{response_time:.3f}s", 
                    use_followup=use_followup, 
                    error=str(e))
        # Fallback to channel if followup fails
        try:
            if content:
                await interaction.channel.send(content)
            elif embed:
                await interaction.channel.send(embed=embed)
            
            fallback_time = time.time() - start_time
            logger.info(f"Fallback response sent successfully", 
                       total_time=f"{fallback_time:.3f}s", 
                       fallback_time=f"{fallback_time - response_time:.3f}s")
            
        except Exception as fallback_error:
            total_time = time.time() - start_time
            logger.error(f"Fallback response also failed: {fallback_error}", 
                        total_time=f"{total_time:.3f}s", 
                        original_error=str(e), 
                        fallback_error=str(fallback_error))
            # Last resort - just log the error, don't raise
