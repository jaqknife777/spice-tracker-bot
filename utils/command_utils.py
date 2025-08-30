"""
Utility functions for Discord bot commands to eliminate code duplication.
"""
import time
from .logger import logger


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


def log_command_metrics(command_name: str, user_id: str, username: str, 
                       total_time: float, **additional_metrics):
    """Centralized logging for command metrics to eliminate repetitive logging code"""
    logger.info(f"{command_name} command completed", 
               user_id=user_id,
               username=username,
               total_time=f"{total_time:.3f}s",
               **additional_metrics)
