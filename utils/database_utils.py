"""
Utility functions for database operations to eliminate code duplication.
"""
import time
from .logger import logger


async def timed_database_operation(operation_name: str, operation_func, *args, **kwargs):
    """Execute a database operation with timing and logging"""
    start_time = time.time()
    
    try:
        result = await operation_func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.info(f"{operation_name} completed successfully", 
                   execution_time=f"{execution_time:.3f}s",
                   operation=operation_name)
        
        return result, execution_time
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"{operation_name} failed", 
                   execution_time=f"{execution_time:.3f}s",
                   operation=operation_name,
                   error=str(e))
        raise


async def validate_user_exists(database, user_id: str, username: str, 
                             create_if_missing: bool = True):
    """Validate user exists and create if missing"""
    user = await database.get_user(user_id)
    
    if not user and create_if_missing:
        await database.upsert_user(user_id, username)
        user = await database.get_user(user_id)
        logger.info(f"User created/updated during operation", 
                   user_id=user_id, 
                   username=username)
    
    return user


async def get_user_stats(database, user_id: str):
    """Get comprehensive user statistics in a single operation"""
    # Get user data
    user = await database.get_user(user_id)
    
    # Get total sand
    total_sand_start = time.time()
    total_sand = await database.get_user_total_sand(user_id)
    total_sand_time = time.time() - total_sand_start
    
    # Get pending melange data
    pending_start = time.time()
    pending_data = await database.get_user_pending_melange(user_id)
    pending_time = time.time() - pending_start
    
    return {
        'user': user,
        'total_sand': total_sand,
        'total_melange': pending_data.get('total_melange', 0),
        'paid_melange': pending_data.get('paid_melange', 0),
        'pending_melange': pending_data.get('pending_melange', 0),
        'timing': {
            'get_user_time': 0,  # User already fetched above
            'get_total_sand_time': f"{total_sand_time:.3f}s",
            'get_pending_time': f"{pending_time:.3f}s"
        },
        'total_time': total_sand_time + pending_time
    }
