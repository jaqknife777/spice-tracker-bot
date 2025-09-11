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



