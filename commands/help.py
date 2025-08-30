"""
Help command for showing all available spice tracking commands.
"""

# Command metadata
COMMAND_METADATA = {
    'aliases': ['commands'],
    'description': "Show all available spice tracking commands"
}

import os
from utils.embed_utils import build_status_embed
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_sand_per_melange, send_response


@handle_interaction_expiration
async def help_command(interaction, use_followup: bool = True):
    """Show all available commands and their descriptions"""
    sand_per_melange = get_sand_per_melange()
    
    # Use utility function for embed building
    fields = {
        "📊 Harvester Commands": "**`/harvest [amount]`**\nLog spice sand harvests (1-10,000). Automatically converts to melange.\n\n"
                                 "**`/refinery`**\nView your refinery statistics and melange production progress.\n\n"
                                 "**`/ledger`**\nView your complete harvest ledger with payment status.\n\n"
                                 "**`/expedition [id]`**\nView details of a specific expedition.\n\n"
                                 "**`/leaderboard [limit]`**\nShow top refiners by melange production (5-25 users).\n\n"
                                 "**`/split [total_sand] [harvester_%]`**\nSplit harvested spice among expedition members. Enter participant Discord IDs in the modal. Creates expedition records and tracks melange owed for payout. Harvester % is optional (default: 10%).\n\n"
                                 "**`/help`**\nDisplay this help message with all commands.",
        "⚙️ Guild Admin Commands": "**`/conversion`**\nView the current refinement rate.\n\n"
                                   "**`/payment [user]`**\nProcess payment for a harvester's deposits.\n\n"
                                   "**`/payroll`**\nProcess payments for all unpaid harvesters.\n\n"
                                   "**`/reset confirm:True`**\nReset all refinery statistics (requires confirmation).",
        "📋 Current Settings": f"**Refinement Rate:** {sand_per_melange} sand = 1 melange (set via SAND_PER_MELANGE env var)\n**Default Harvester %:** {os.getenv('DEFAULT_HARVESTER_PERCENTAGE', '10.0')}%",
        "💡 Example Usage": "• `/harvest 250` or `/sand 250` - Harvest 250 spice sand\n"
                            "• `/refinery` or `/status` - Check your refinery status\n"
                            "• `/ledger` or `/deposits` - View your harvest ledger\n"
                            "• `/leaderboard 15` or `/top 15` - Show top 15 refiners\n"
                            "• `/payment @username` or `/pay @username` - Pay a specific harvester\n"
                            "• `/payroll` or `/payall` - Pay all harvesters at once\n"
                            "• `/split 1000 30` - Split 1000 sand, 30% to primary harvester\n"
                            "• `/split 1000` - Split 1000 sand using default harvester % (10%)\n"
                            "• **Note:** You'll be prompted to enter participant Discord IDs in a modal",
        "🔄 Command Aliases": "**Harvest:** `/harvest` = `/sand`\n"
                              "**Status:** `/refinery` = `/status`\n"
                              "**Ledger:** `/ledger` = `/deposits`\n"
                              "**Leaderboard:** `/leaderboard` = `/top`\n"
                              "**Expedition:** `/expedition` = `/exp`\n"
                              "**Help:** `/help` = `/commands`\n"
                              "**Conversion:** `/conversion` = `/rate`\n"
                              "**Payment:** `/payment` = `/pay`\n"
                              "**Payroll:** `/payroll` = `/payall`"
    }
    
    embed = build_status_embed(
        title="🏜️ Spice Refinery Commands",
        description="Track your spice sand harvests and melange production in the Dune: Awakening universe!",
        color=0xF39C12,
        fields=fields,
        footer="Spice Refinery Bot - Dune: Awakening Guild Resource Tracker",
        timestamp=interaction.created_at
    )
    
    await send_response(interaction, embed=embed.build(), use_followup=use_followup)
