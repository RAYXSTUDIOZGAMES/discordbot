import os
import logging
import discord
from discord.ext import commands
from config import load_config
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('discord_bot')

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class EditingHelperBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            case_insensitive=True,
            help_command=None
        )

    async def setup_hook(self):
        # Load extensions
        initial_extensions = [
            'cogs.ai',
            'cogs.moderation',
            'cogs.general',
            'cogs.legacy',
            'cogs.economy',
            'cogs.leveling'
        ]

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f'Loaded extension: {extension}')
            except Exception as e:
                logger.error(f'Failed to load extension {extension}: {e}', exc_info=True)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')

def run_bot():
    config = load_config()
    token = config.get('DISCORD_TOKEN') or os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("No Discord token found! Check your .env file.")
        return

    bot = EditingHelperBot()
    bot.run(token)

if __name__ == "__main__":
    run_bot()
