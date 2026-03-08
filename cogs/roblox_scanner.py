import discord
from discord import app_commands
from discord.ext import commands
import logging
import json
import os
import hashlib
from datetime import datetime

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ROBLOX_SCANNER_PATH

class RobloxScanner(commands.Cog):
    """Roblox scanner integration commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_data_file = "user_data.json"
        self.logger = logging.getLogger('roblox_scanner')
        self.active_scans = {}
        
        # Import scanner if available
        self.scanner_available = False
        try:
            # Try to import the scanner
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from roblox_trend_scanner_monetized import RobloxTrendScanner
            self.scanner = RobloxTrendScanner()
            self.scanner_available = True
            self.logger.info("Roblox scanner loaded successfully")
        except Exception as e:
            self.logger.warning(f"Roblox scanner not available: {e}")
            self.scanner_available = False

    def load_user_data(self):
        """Load user license data"""
        try:
            with open(self.user_data_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def has_premium_license(self, user_id):
        """Check if user has premium license"""
        user_data = self.load_user_data()
        
        if user_id not in user_data:
            return False, "No active license"
        
        license_info = user_data[user_id]
        expires_at = datetime.fromisoformat(license_info.get('expires', '2024-01-01'))
        
        if datetime.now() >= expires_at:
            return False, "License expired"
        
        return True, license_info.get('tier', 'basic')

    @app_commands.command(name="scan")
    async def run_scan(self, interaction: discord.Interaction, amount: int = 100):
        """Run Roblox vulnerability scan"""
        user_id = str(interaction.user.id)
        
        # Check if user has premium license
        has_license, tier_or_reason = self.has_premium_license(user_id)
        
        if not has_license:
            embed = discord.Embed(
                title="🔒 PREMIUM REQUIRED",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="❌ Access Denied",
                value="You need a premium license to run scans!\n\n"
                       "💎 **Get Premium:**\n"
                       "• `!premium` - View plans\n"
                       "• `!buy-premium` - Purchase Premium license\n"
                       "• Only $10/month!",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # No scan limits for premium users (all premium users get unlimited)
        # If you want to add limits later, you can check tier here
        # if tier_or_reason == 'basic' and amount > 100:
            embed = discord.Embed(
                title="📊 SCAN LIMIT REACHED",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="❌ Limit Exceeded",
                value=f"Basic license allows only 100 items per scan\n"
                       f"You requested: {amount} items\n\n"
                       "💎 **Upgrade to Pro for unlimited scanning!**",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Start scan
        await interaction.response.send_message(
            f"🔍 **Starting scan of {amount} items...**\n"
            f"This may take 30-60 seconds. Please wait..."
        )
        
        # Track active scan
        scan_id = hashlib.md5(f"{user_id}{amount}{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        self.active_scans[user_id] = {
            'scan_id': scan_id,
            'amount': amount,
            'started_at': datetime.now()
        }
        
        try:
            # Run the actual scan
            if self.scanner_available:
                results = self.scanner.clothing_hijacker(amount)
            else:
                # Demo results if scanner not available
                results = self.generate_demo_results(amount)
            
            # Clean up active scan
            if user_id in self.active_scans:
                del self.active_scans[user_id]
            
            if results:
                embed = discord.Embed(
                    title="🎯 SCAN RESULTS",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 Vulnerable Creators",
                    value=f"{len(results)} found",
                    inline=False
                )
                
                # Show top 5 results
                for i, creator in enumerate(results[:5], 1):
                    embed.add_field(
                        name=f"🔹 {i}. {creator.get('creator', 'Unknown Creator')}",
                        value=f"**Type:** {creator.get('creator_type', 'Unknown')}\n"
                               f"**Favorites:** {creator.get('total_favorites', 0):,}\n"
                               f"**Items:** {creator.get('total_items', 0)}\n"
                               f"**Premium:** {'❌' if not creator.get('has_premium') else '✅'}",
                        inline=False
                    )
                
                embed.add_field(
                    name="💡 Next Steps",
                    value="• Analyze these creators for opportunities\n"
                           "• Contact non-premium creators\n"
                           "• Monitor their upload patterns\n"
                           "• Use this data for your strategy",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                
            else:
                await interaction.followup.send("❌ **Scan failed**. Please try again later.")
                
        except Exception as e:
            self.logger.error(f"Scan error: {e}")
            await interaction.followup.send(f"❌ **Scan Error:** {str(e)}")

    def generate_demo_results(self, amount):
        """Generate demo results when scanner not available"""
        import random
        
        demo_creators = []
        for i in range(min(5, amount // 20)):  # Generate 1-5 demo results
            creator = {
                'creator': f'DemoCreator{i+1}',
                'creator_type': random.choice(['user', 'group']),
                'total_favorites': random.randint(1000, 50000),
                'total_items': random.randint(10, 100),
                'has_premium': random.choice([True, False])
            }
            demo_creators.append(creator)
        
        return demo_creators

    @app_commands.command(name="keywords")
    async def keyword_analysis(self, interaction: discord.Interaction, amount: int = 50):
        """Run keyword analysis"""
        user_id = str(interaction.user.id)
        
        # Check license
        has_license, tier_or_reason = self.has_premium_license(user_id)
        
        if not has_license:
            await interaction.response.send_message(
                "🔒 **Premium license required for keyword analysis!**\n"
                "Use `!premium` to view plans.",
                ephemeral=True
            )
            return
        
        # Check limits
        if tier_or_reason == 'basic' and amount > 50:
            await interaction.response.send_message(
                "📊 **Basic license limited to 50 items for keyword analysis**\n"
                "Upgrade to Pro for unlimited analysis!",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            f"🔍 **Starting keyword analysis of {amount} items...**"
        )
        
        # Demo keyword analysis
        keywords = [
            "goth", "y2k", "emo", "skater", "evade",
            "aesthetic", "alternative", "vintage", "retro", "streetwear"
        ]
        
        results = {}
        for keyword in keywords[:10]:
            results[keyword] = {
                'count': random.randint(5, 50),
                'trend': random.choice(['up', 'down', 'stable']),
                'saturation': random.uniform(0.1, 0.9)
            }
        
        embed = discord.Embed(
            title="📊 KEYWORD ANALYSIS RESULTS",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for keyword, data in list(results.items())[:5]:
            trend_emoji = {'up': '📈', 'down': '📉', 'stable': '➡️'}[data['trend']]
            embed.add_field(
                name=f"🔹 {keyword.title()} {trend_emoji}",
                value=f"Count: {data['count']}\n"
                       f"Saturation: {data['saturation']:.1%}\n"
                       f"Trend: {data['trend'].title()}",
                inline=True
            )
        
        embed.add_field(
            name="💡 Insights",
            value="• Monitor rising trends\n"
                   "• Avoid oversaturated keywords\n"
                   "• Focus on emerging styles\n"
                   "• Use data for strategy",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="demo")
    async def demo_scan(self, interaction: discord.Interaction):
        """Show demo of scanner capabilities"""
        embed = discord.Embed(
            title="🎯 ROBLOX SCANNER DEMO",
            color=discord.Color.purple(),
            description="Preview of what premium users can access!"
        )
        
        embed.add_field(
            name="🔍 Vulnerability Scanner",
            value="Find non-premium creators with popular clothing items",
            inline=False
        )
        
        embed.add_field(
            name="📊 Keyword Analysis",
            value="Analyze trending keywords and market saturation",
            inline=False
        )
        
        embed.add_field(
            name="👥 Creator Intelligence",
            value="Track creator performance and premium status",
            inline=False
        )
        
        embed.add_field(
            name="💎 Upgrade to Premium",
            value="Use `!premium` to see pricing and unlock all features!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(RobloxScanner(bot))
    logging.getLogger('roblox_scanner').info("RobloxScanner cog setup complete")
