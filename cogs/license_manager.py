import discord
from discord import app_commands
from discord.ext import commands
import logging
import json
import os
import hashlib
from datetime import datetime, timedelta

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    LICENSE_CHANNEL_ID, PREMIUM_ROLE_ID, LICENSE_DURATION_DAYS,
    MAX_LICENSES_PER_USER, INDONESIA_CONFIG
)

class LicenseManager(commands.Cog):
    """License management commands for Roblox Scanner Pro"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_data_file = "user_data.json"
        self.logger = logging.getLogger('license_manager')
        self.logger.info("LicenseManager initialized")

    def load_user_data(self):
        """Load user license data"""
        try:
            with open(self.user_data_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_user_data(self, data):
        """Save user license data"""
        with open(self.user_data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_license_key(self, user_id, tier):
        """Generate unique license key"""
        import uuid
        base_string = f"{user_id}:{tier}:{datetime.now().timestamp()}"
        return hashlib.sha256(base_string.encode()).hexdigest()[:16]

    def verify_license_key(self, license_key):
        """Verify license key format"""
        return len(license_key) == 16 and all(c in '0123456789abcdef' for c in license_key)

    @app_commands.command(name="license")
    async def activate_license(self, interaction: discord.Interaction, license_key: str):
        """Activate premium license"""
        user_id = str(interaction.user.id)
        
        if not license_key:
            await interaction.response.send_message(
                "❌ **Error:** Please provide a license key",
                ephemeral=True
            )
            return
        
        # Verify license key format
        if not self.verify_license_key(license_key):
            await interaction.response.send_message(
                "❌ **Invalid license key format**",
                ephemeral=True
            )
            return
        
        # Load user data
        user_data = self.load_user_data()
        
        # Check if user already has active license
        if user_id in user_data:
            existing_license = user_data[user_id]
            expires_at = datetime.fromisoformat(existing_license.get('expires', '2024-01-01'))
            
            if datetime.now() < expires_at:
                await interaction.response.send_message(
                    "✅ **You already have an active license!**",
                    ephemeral=True
                )
                return
        
        # Activate new license
        tier = "pro"  # Default to pro for demo
        expires_at = datetime.now() + timedelta(days=LICENSE_DURATION_DAYS)
        
        user_data[user_id] = {
            'user_id': user_id,
            'username': interaction.user.name,
            'license_key': license_key,
            'tier': tier,
            'activated': datetime.now().isoformat(),
            'expires': expires_at.isoformat(),
            'features': ['unlimited_scanning', 'advanced_analytics', 'api_access', 'export']
        }
        
        self.save_user_data(user_data)
        
        # Assign premium role if configured
        if PREMIUM_ROLE_ID > 0:
            try:
                role = interaction.guild.get_role(PREMIUM_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)
                    self.logger.info(f"Assigned premium role to {interaction.user.name}")
            except Exception as e:
                self.logger.error(f"Failed to assign role: {e}")
        
        # Send confirmation
        embed = discord.Embed(
            title="🎉 LICENSE ACTIVATED!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Tier", value=tier.upper(), inline=True)
        embed.add_field(name="Status", value="ACTIVE", inline=True)
        embed.add_field(name="Expires", value=expires_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Features", value="4 unlocked", inline=True)
        
        embed.add_field(
            name="🚀 What's Next?",
            value="Use `!scan <amount>` to start unlimited scanning!\n"
                   "All premium features are now available!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Public announcement
        await interaction.channel.send(
            f"🎊 **{interaction.user.name}** has activated **{tier.upper()}** license!"
        )

    @app_commands.command(name="status")
    async def check_status(self, interaction: discord.Interaction):
        """Check user's license status"""
        user_id = str(interaction.user.id)
        user_data = self.load_user_data()
        
        if user_id in user_data:
            license_info = user_data[user_id]
            expires_at = datetime.fromisoformat(license_info.get('expires', '2024-01-01'))
            
            if datetime.now() < expires_at:
                embed = discord.Embed(
                    title="✅ PREMIUM STATUS",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="Tier", value=license_info.get('tier', 'Unknown').upper(), inline=True)
                embed.add_field(name="Status", value="ACTIVE", inline=True)
                embed.add_field(name="Activated", value=license_info.get('activated', 'Unknown')[:10], inline=True)
                embed.add_field(name="Expires", value=expires_at.strftime("%Y-%m-%d"), inline=True)
                
            else:
                embed = discord.Embed(
                    title="⏰ LICENSE EXPIRED",
                    color=discord.Color.orange()
                )
                
                embed.add_field(name="Status", value="EXPIRED", inline=False)
                embed.add_field(name="Renew", value="Use `!premium` to renew", inline=False)
        else:
            embed = discord.Embed(
                title="🔒 FREE USER",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="Status", value="No active license", inline=False)
            embed.add_field(
                name="💎 Upgrade",
                value="Use `!premium` to view plans\nUse `!buy-premium` to purchase a license",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="premium")
    async def premium_info(self, interaction: discord.Interaction):
        """Show premium subscription information"""
        from config import get_pricing_info
        
        pricing = get_pricing_info()
        
        embed = discord.Embed(
            title="💎 PREMIUM LICENSE",
            color=discord.Color.gold(),
            description="Unlock the full power of Roblox market analysis!"
        )
        
        # Premium plan only
        premium = pricing['premium']
        embed.add_field(
            name=f"🔹 PREMIUM LICENSE - ${premium['price_usd']}/month",
            value="\n".join([f"• {feature}" for feature in premium['features']]),
            inline=False
        )
        
        # Payment methods
        embed.add_field(
            name="🌏 PAYMENT METHODS (Indonesia Friendly)",
            value="💳 **PayPal:** Global, supports local banks\n"
                   "🪙 **Crypto:** USDC, USDT, ETH (instant)\n"
                   "📧 **Manual:** Bank transfer available",
            inline=False
        )
        
        embed.add_field(
            name="🚀 HOW TO BUY",
            value="1. `!buy-premium` - Get Premium license\n"
                   "2. Complete payment\n"
                   "3. Use `!license <key>` to activate\n"
                   "4. Enjoy premium features!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help")
    async def custom_help(self, interaction: discord.Interaction):
        """Custom help command"""
        embed = discord.Embed(
            title="🎯 Roblox Trend Scanner Pro",
            color=discord.Color.blue(),
            description="Advanced Roblox market intelligence tool"
        )
        
        embed.add_field(
            name="🚀 Commands",
            value="`!license <key>` - Activate premium\n"
                   "`!premium` - View plans & pricing\n"
                   "`!status` - Check your license status\n"
                   "`!scan <amount>` - Run vulnerability scan\n"
                   "`!buy-pro` - Get Pro license\n"
                   "`!support` - Get help",
            inline=False
        )
        
        embed.add_field(
            name="💎 Premium Features",
            value="✅ Unlimited scanning\n"
                   "✅ Advanced analytics\n"
                   "✅ Export capabilities\n"
                   "✅ Priority support\n"
                   "✅ API access",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="support")
    async def support_command(self, interaction: discord.Interaction):
        """Support command for getting help"""
        embed = discord.Embed(
            title="📞 SUPPORT",
            color=discord.Color.purple(),
            description="Need help? I'm here for you!"
        )
        
        embed.add_field(
            name="🆘 Contact Options",
            value="• **DM me directly** for personal help\n"
                   "• **Email:** support@your-scanner.com\n"
                   "• **Discord:** https://discord.gg/your-server\n"
                   "• **GitHub:** https://github.com/your-repo/issues",
            inline=False
        )
        
        embed.add_field(
            name="💡 Common Issues",
            value="• **License not working?** DM me your license key\n"
                   "• **Payment problems?** DM me transaction details\n"
                   "• **Scan errors?** Check your license status\n"
                   "• **Feature requests?** Use `!support`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message events"""
        # Auto-delete messages in license channel if configured
        if LICENSE_CHANNEL_ID and message.channel.id == LICENSE_CHANNEL_ID:
            if not message.author.bot and not message.content.startswith('!'):
                try:
                    await message.delete()
                except:
                    pass

async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(LicenseManager(bot))
    logging.getLogger('license_manager').info("LicenseManager cog setup complete")
