import discord
from discord.ext import commands
import logging
import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import TOKEN, check_config, BOT_NAME, BOT_DESCRIPTION

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bot')

class RobloxScannerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.user_data_file = "user_data.json"
        self.active_scans = {}

    async def setup_hook(self):
        """Load cogs and sync commands"""
        logger.info("Setting up bot...")
        
        # Load cogs
        await self.load_extension('cogs.license_manager')
        await self.load_extension('cogs.roblox_scanner')
        await self.load_extension('cogs.payment')
        
        # Sync commands
        try:
            await self.tree.sync()
            logger.info("Commands synced successfully")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'🚀 {self.user} is online!')
        logger.info(f'📊 Serving {len(self.guilds)} servers')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Roblox trends | !premium"
            )
        )
        
        logger.info(f'Bot is ready with {len(self.commands)} commands')

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ **Unknown command.** Use `!help` for available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ **Missing argument.** Use `!help` for command usage.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Permission denied.** You don't have permission to use this command.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ **Error:** {str(error)}")

async def startup_checks():
    """Perform startup validation"""
    try:
        logger.info("Starting configuration check...")
        check_config()
        logger.info("Configuration validated successfully")
        
        # Test storage
        if not os.path.exists("user_data.json"):
            with open("user_data.json", "w") as f:
                f.write("{}")
            logger.info("Created user_data.json")
        
        return True
    except Exception as e:
        logger.error(f"Startup check failed: {str(e)}")
        return False

async def main():
    """Main bot function"""
    try:
        if not await startup_checks():
            logger.error("Startup checks failed. Exiting...")
            sys.exit(1)

        bot = RobloxScannerBot()
        
        async with bot:
            await bot.start(TOKEN)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
