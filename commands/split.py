"""
Split command for splitting harvested spice sand among expedition members.
"""

import os
import discord
from utils.decorators import handle_interaction_expiration
from utils.helpers import get_database, get_sand_per_melange, send_response
from utils.logger import logger


@handle_interaction_expiration
async def split(interaction, total_sand: int, harvester_percentage: float = None, use_followup: bool = True):
    """Split harvested spice sand among expedition members"""
    try:
        # Use environment variable if no harvester_percentage provided
        if harvester_percentage is None:
            harvester_percentage = float(os.getenv('DEFAULT_HARVESTER_PERCENTAGE', 10.0))  # Default to 10%
        
        # Validate inputs
        if total_sand < 1:
            await send_response(interaction, "❌ Total spice sand must be at least 1.", use_followup=use_followup, ephemeral=True)
            return
        if not 0 <= harvester_percentage <= 100:
            await send_response(interaction, "❌ Primary harvester percentage must be between 0 and 100.", use_followup=use_followup, ephemeral=True)
            return
        
        # Create a modal to collect participant information
        class ExpeditionModal(discord.ui.Modal, title="🏜️ Expedition Participants"):
            participants_input = discord.ui.TextInput(
                label="Participant Discord IDs (one per line)",
                placeholder="Enter Discord user IDs, one per line\nExample:\n123456789012345678\n987654321098765432",
                style=discord.TextStyle.paragraph,
                required=True,
                min_length=1,
                max_length=1000
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                try:
                    # Parse participant IDs
                    participant_ids = [pid.strip() for pid in self.participants_input.value.split('\n') if pid.strip()]
                    
                    if not participant_ids:
                        await modal_interaction.response.send_message("❌ No valid participant IDs provided.", ephemeral=True)
                        return
                    
                    # Defer response to prevent timeout
                    await modal_interaction.response.defer(thinking=True)
                    
                    # Get conversion rate
                    sand_per_melange = get_sand_per_melange()
                    
                    # Create expedition record
                    expedition_id = await get_database().create_expedition(
                        str(interaction.user.id),
                        interaction.user.display_name,
                        total_sand,
                        harvester_percentage,
                        sand_per_melange
                    )
                    
                    if not expedition_id:
                        await modal_interaction.followup.send("❌ Failed to create expedition record.", ephemeral=True)
                        return
                    
                    # Calculate harvester share
                    harvester_sand = int(total_sand * (harvester_percentage / 100))
                    remaining_sand = total_sand - harvester_sand
                    
                    # Calculate remaining share per participant (excluding harvester)
                    remaining_participants = len(participant_ids) + 1  # +1 for harvester
                    share_per_participant = remaining_sand // remaining_participants if remaining_participants > 0 else 0
                    leftover_sand = remaining_sand % remaining_participants if remaining_participants > 0 else remaining_sand
                    
                    # Add harvester (initiator) as primary harvester
                    harvester_melange = harvester_sand // sand_per_melange
                    harvester_leftover = harvester_sand % sand_per_melange
                    
                    await get_database().add_expedition_participant(
                        expedition_id,
                        str(interaction.user.id),
                        interaction.user.display_name,
                        harvester_sand,
                        harvester_melange,
                        harvester_leftover,
                        is_harvester=True
                    )
                    
                    # Create expedition deposit for harvester
                    await get_database().add_expedition_deposit(
                        str(interaction.user.id),
                        interaction.user.display_name,
                        harvester_sand,
                        expedition_id
                    )
                    
                    # Add remaining participants
                    participant_details = []
                    total_melange = harvester_melange
                    
                    for participant_id in participant_ids:
                        # Try to get user info from Discord
                        try:
                            if modal_interaction.guild:
                                user = await modal_interaction.guild.fetch_member(int(participant_id))
                                username = user.display_name
                            else:
                                # No guild context (DM), use participant ID as username
                                username = f"User_{participant_id}"
                        except:
                            username = f"User_{participant_id}"
                        
                        # Calculate participant share
                        participant_sand = share_per_participant
                        participant_melange = participant_sand // sand_per_melange
                        participant_leftover = participant_sand % sand_per_melange
                        
                        # Add to database
                        await get_database().add_expedition_participant(
                            expedition_id,
                            participant_id,
                            username,
                            participant_sand,
                            participant_melange,
                            participant_leftover,
                            is_harvester=False
                        )
                        
                        # Create expedition deposit for participant
                        await get_database().add_expedition_deposit(
                            participant_id,
                            username,
                            participant_sand,
                            expedition_id
                        )
                        
                        participant_details.append(f"**{username}**: {participant_sand:,} sand ({participant_melange:,} melange)")
                        total_melange += participant_melange
                    
                    # Add leftover to harvester if any
                    if leftover_sand > 0:
                        leftover_melange = leftover_sand // sand_per_melange
                        leftover_remaining = leftover_sand % sand_per_melange
                        
                        # Update harvester's share
                        await get_database().add_expedition_participant(
                            expedition_id,
                            str(interaction.user.id),
                            interaction.user.display_name,
                            leftover_sand,
                            leftover_melange,
                            leftover_remaining,
                            is_harvester=False
                        )
                        
                        # Create expedition deposit for leftover
                        await get_database().add_expedition_deposit(
                            str(interaction.user.id),
                            interaction.user.display_name,
                            leftover_sand,
                            expedition_id
                        )
                        
                        harvester_sand += leftover_sand
                        harvester_melange += leftover_melange
                        harvester_leftover += leftover_remaining
                    
                    # Build response embed
                    from utils.embed_builder import EmbedBuilder
                    embed = (EmbedBuilder("🏜️ Expedition Created", 
                                          description=f"**Expedition #{expedition_id}** has been created and recorded in the database!",
                                          color=0xF39C12, timestamp=modal_interaction.created_at)
                             .add_field("📊 Expedition Summary", 
                                       f"**Total Sand:** {total_sand:,}\n"
                                       f"**Primary Harvester:** {interaction.user.display_name}\n"
                                       f"**Harvester Share:** {harvester_sand:,} sand ({harvester_percentage}%)\n"
                                       f"**Participants:** {len(participant_ids) + 1}", inline=False)
                             .add_field("💰 Melange Distribution", 
                                       f"**Harvester Melange:** {harvester_melange:,}\n"
                                       f"**Total Melange:** {total_melange:,}", inline=False)
                             .add_field("📋 Participants", 
                                       f"**Primary Harvester:** {interaction.user.display_name} - {harvester_sand:,} sand\n" +
                                       "\n".join(participant_details), inline=False)
                             .add_field("📋 Database Status", 
                                       f"✅ Expedition record created\n"
                                       f"✅ Participant shares recorded\n"
                                       f"✅ Deposits logged for payout tracking\n"
                                       f"🔗 Use `/expedition {expedition_id}` to view details", inline=False)
                             .set_footer(f"Expedition initiated by {interaction.user.display_name}", interaction.user.display_avatar.url))
                    
                    await modal_interaction.followup.send(embed=embed.build())
                    
                    # Log the expedition creation
                    logger.bot_event(f"Expedition {expedition_id} created by {interaction.user.display_name} ({interaction.user.id}) - {total_sand} sand, {harvester_percentage}% harvester share, {len(participant_ids)} participants")
                    
                except Exception as error:
                    logger.error(f"Error in expedition modal: {error}")
                    try:
                        await modal_interaction.followup.send("❌ An error occurred while creating the expedition.", ephemeral=True)
                    except:
                        await modal_interaction.channel.send("❌ An error occurred while creating the expedition.")
        
        # Show the modal
        modal = ExpeditionModal()
        await interaction.response.send_modal(modal)
        
    except Exception as error:
        logger.error(f"Error in split command: {error}")
        await send_response(interaction, "❌ An error occurred while setting up the expedition.", use_followup=use_followup, ephemeral=True)
