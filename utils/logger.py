import logging
import os
from typing import Optional

class BotLogger:
    """Clean logger optimized for Fly.io deployment and Discord bot monitoring"""
    
    def __init__(self, name: str = "spice-tracker-bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Fly.io-friendly console handler - no formatter to avoid duplicate timestamps/levels
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # No formatter - let Fly.io handle timestamps and levels
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format log message with clean, readable data - no timestamp/level since Fly.io provides that"""
        
        # Build clean message
        parts = [message]
        
        # Add key-value pairs in clean format
        for key, value in kwargs.items():
            if value is not None:
                # Format the value nicely
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:,}" if isinstance(value, int) else f"{value:.3f}"
                elif isinstance(value, str):
                    formatted_value = value
                else:
                    formatted_value = str(value)
                
                parts.append(f"{key}={formatted_value}")
        
        return " | ".join(parts)
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        formatted = self._format_message(message, **kwargs)
        self.logger.info(formatted)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        formatted = self._format_message(message, **kwargs)
        self.logger.warning(formatted)
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        formatted = self._format_message(message, **kwargs)
        self.logger.error(formatted)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        formatted = self._format_message(message, **kwargs)
        self.logger.debug(formatted)
    
    def command_executed(self, command: str, user_id: str, username: str, 
                        guild_id: Optional[str] = None, guild_name: Optional[str] = None,
                        **kwargs):
        """Log Discord command execution"""
        self.info(
            f"Command executed: {command}",
            user=username,
            user_id=user_id,
            guild=guild_name,
            **kwargs
        )
    
    def command_success(self, command: str, user_id: str, username: str, 
                       execution_time: float, **kwargs):
        """Log successful command execution"""
        self.info(
            f"Command completed: {command}",
            user=username,
            user_id=user_id,
            time=f"{execution_time:.3f}s",
            **kwargs
        )
    
    def command_error(self, command: str, user_id: str, username: str, 
                     error: str, **kwargs):
        """Log command execution errors"""
        self.error(
            f"Command failed: {command}",
            user=username,
            user_id=user_id,
            error=error,
            **kwargs
        )
    
    def rate_limit_hit(self, command: str, user_id: str, username: str):
        """Log rate limit violations"""
        self.warning(
            f"Rate limit hit: {command}",
            user=username,
            user_id=user_id
        )
    
    def permission_denied(self, command: str, user_id: str, username: str, 
                         required_permission: str):
        """Log permission denied events"""
        self.warning(
            f"Permission denied: {command}",
            user=username,
            user_id=user_id,
            required=required_permission
        )
    
    def bot_event(self, event: str, **kwargs):
        """Log bot lifecycle events"""
        self.info(
            f"Bot event: {event}",
            **kwargs
        )
    
    def database_operation(self, operation: str, table: str, success: bool, 
                          **kwargs):
        """Log database operations"""
        if success:
            self.info(
                f"Database {operation} on {table}",
                **kwargs
            )
        else:
            self.error(
                f"Database {operation} failed on {table}",
                **kwargs
            )

# Global logger instance
logger = BotLogger()
