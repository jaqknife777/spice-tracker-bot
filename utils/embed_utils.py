"""
Utility functions for building common Discord embeds to eliminate code duplication.
"""
from typing import Dict, Optional, List
from .embed_builder import EmbedBuilder


def build_status_embed(title: str, description: str = None, color: int = 0x3498DB, 
                      fields: Optional[Dict[str, str]] = None, footer: str = None, 
                      thumbnail: str = None, timestamp=None) -> EmbedBuilder:
    """Build a standardized status embed for commands"""
    embed = EmbedBuilder(title, description=description, color=color, timestamp=timestamp)
    
    if fields:
        for field_name, field_value in fields.items():
            embed.add_field(field_name, field_value)
    
    if footer:
        embed.set_footer(footer)
    
    if thumbnail:
        embed.set_thumbnail(thumbnail)
    
    return embed


def build_error_embed(title: str, error_message: str, footer: str = None, 
                     timestamp=None) -> EmbedBuilder:
    """Build a standardized error embed"""
    return build_status_embed(
        title=title,
        description=f"❌ {error_message}",
        color=0xE74C3C,
        footer=footer,
        timestamp=timestamp
    )


def build_success_embed(title: str, success_message: str, footer: str = None, 
                       timestamp=None) -> EmbedBuilder:
    """Build a standardized success embed"""
    return build_status_embed(
        title=title,
        description=f"✅ {success_message}",
        color=0x27AE60,
        footer=footer,
        timestamp=timestamp
    )


def build_info_embed(title: str, info_message: str, footer: str = None, 
                    timestamp=None) -> EmbedBuilder:
    """Build a standardized info embed"""
    return build_status_embed(
        title=title,
        description=info_message,
        color=0x3498DB,
        footer=footer,
        timestamp=timestamp
    )


def build_warning_embed(title: str, warning_message: str, footer: str = None, 
                       timestamp=None) -> EmbedBuilder:
    """Build a standardized warning embed"""
    return build_status_embed(
        title=title,
        description=f"⚠️ {warning_message}",
        color=0xF39C12,
        footer=footer,
        timestamp=timestamp
    )


def build_leaderboard_embed(title: str, leaderboard_data: List[Dict], 
                           total_stats: Dict[str, int], footer: str = None, 
                           timestamp=None) -> EmbedBuilder:
    """Build a standardized leaderboard embed"""
    # Build leaderboard text
    leaderboard_text = ""
    medals = ['🥇', '🥈', '🥉']
    
    for index, user in enumerate(leaderboard_data):
        position = index + 1
        medal = medals[index] if index < 3 else f"**{position}.**"
        leaderboard_text += f"{medal} **{user['username']}** - {user['total_melange']:,} melange\n\n"
    
    # Build stats fields
    fields = {
        "📊 Guild Statistics": f"**Total Refiners:** {total_stats.get('total_refiners', len(leaderboard_data))}\n**Total Melange:** {total_stats.get('total_melange', 0):,}",

    }
    
    return build_status_embed(
        title=title,
        description=leaderboard_text,
        color=0xF39C12,
        fields=fields,
        footer=footer,
        timestamp=timestamp
    )


def build_progress_embed(title: str, current: int, total: int, 
                        progress_fields: Dict[str, str], footer: str = None, 
                        thumbnail: str = None, timestamp=None) -> EmbedBuilder:
    """Build a standardized progress embed with progress bar"""
    # Calculate progress
    progress_percent = int((current / total) * 100) if total > 0 else 0
    
    # Create progress bar
    progress_bar_length = 10
    filled_bars = int((current / total) * progress_bar_length) if total > 0 else 0
    progress_bar = '▓' * filled_bars + '░' * (progress_bar_length - filled_bars)
    
    # Add progress bar to fields
    progress_fields["🎯 Progress"] = f"{progress_bar} {progress_percent}%\n**Current:** {current:,} | **Total:** {total:,}"
    
    return build_status_embed(
        title=title,
        color=0x3498DB,
        fields=progress_fields,
        footer=footer,
        thumbnail=thumbnail,
        timestamp=timestamp
    )
