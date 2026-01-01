import discord
import os
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger('discord_bot')

INVITERS_FILE = "guild_inviters.json"

def load_guild_inviters():
    """Load guild inviters from file."""
    try:
        if os.path.exists(INVITERS_FILE):
            with open(INVITERS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading guild inviters: {e}")
    return {}

def save_guild_inviters(inviters):
    """Save guild inviters to file."""
    try:
        with open(INVITERS_FILE, 'w') as f:
            json.dump(inviters, f)
    except Exception as e:
        logger.error(f"Error saving guild inviters: {e}")

guild_inviters = load_guild_inviters()

async def log_activity(bot, title, description, color=0x5865F2, fields=None):
    """Send activity log to the designated Discord channel."""
    log_channel_id = os.getenv("LOG_CHANNEL_ID")
    if not log_channel_id:
        return

    try:
        log_channel = bot.get_channel(int(log_channel_id))
        if not log_channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        if fields:
            for name, value in fields.items():
                embed.add_field(name=name, value=str(value), inline=True)
        await log_channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Failed to send activity log: {e}")

def is_server_admin(user, guild):
    """Check if user is the server inviter, guild owner, or has admin permissions."""
    if not guild:
        return False
    guild_id_str = str(guild.id)
    # Check if user is BMR (always has access)
    if 'bmr' in user.name.lower():
        return True
    # Check if user is the guild owner
    if guild.owner and user.id == guild.owner.id:
        return True
    # Check if user is the one who added the bot
    if guild_id_str in guild_inviters and guild_inviters[guild_id_str] == user.id:
        return True
    # Check if user has administrator permission
    if hasattr(user, 'guild_permissions') and user.guild_permissions.administrator:
        return True
    return False

def get_server_admin_name(guild):
    """Get the name of who can use admin commands in this server."""
    if not guild:
        return "the server admin"
    guild_id_str = str(guild.id)
    if guild_id_str in guild_inviters:
        inviter_id = guild_inviters[guild_id_str]
        member = guild.get_member(inviter_id)
        if member:
            return member.name
    if guild.owner:
        return guild.owner.name
    return "the server admin"
