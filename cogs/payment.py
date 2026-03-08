import discord
from discord import app_commands
from discord.ext import commands
import logging
import hashlib
from datetime import datetime

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PAYPAL_CLIENT_ID, USDC_WALLET_ADDRESS, USDT_WALLET_ADDRESS, ETH_WALLET_ADDRESS,
    BASIC_PRICE, PRO_PRICE, INDONESIA_CONFIG
)

class Payment(commands.Cog):
    """Payment processing commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('payment')
        self.active_payments = {}

    def generate_payment_id(self, user_id, plan):
        """Generate unique payment ID"""
        return hashlib.md5(f"{user_id}{plan}{datetime.now().timestamp()}".encode()).hexdigest()[:12]

    def create_paypal_link(self, user_id, plan, amount):
        """Create PayPal payment link"""
        if not PAYPAL_CLIENT_ID:
            return None
        
        # In production, you'd use actual PayPal API
        # For demo, create a mock link
        return f"https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=YOUR_BUTTON_ID&item_name={plan}_license&amount={amount}&custom={user_id}"

    def create_crypto_payment_info(self, user_id, plan, amount):
        """Create crypto payment information"""
        if not USDC_WALLET_ADDRESS:
            return None
        
        payment_id = self.generate_payment_id(user_id, plan)
        
        return {
            'payment_id': payment_id,
            'amount_usd': amount,
            'addresses': {
                'USDC': USDC_WALLET_ADDRESS,
                'USDT': USDT_WALLET_ADDRESS,
                'ETH': ETH_WALLET_ADDRESS
            },
            'network': 'ethereum',
            'memo': f"roblox_scanner_{payment_id}"
        }

    @app_commands.command(name="buy-premium")
    async def buy_premium(self, interaction: discord.Interaction):
        """Generate payment link for Premium license"""
        user_id = str(interaction.user.id)
        await self.generate_payment_link(interaction, user_id, 'premium', PRO_PRICE)

    async def generate_payment_link(self, interaction, user_id, plan, amount):
        """Generate payment link and DM to user"""
        payment_id = self.generate_payment_id(user_id, plan)
        
        # Store payment info
        self.active_payments[payment_id] = {
            'user_id': user_id,
            'plan': plan,
            'amount': amount,
            'created_at': datetime.now(),
            'status': 'pending'
        }
        
        embed = discord.Embed(
            title=f"💳 {plan.upper()} LICENSE PAYMENT",
            color=discord.Color.blue(),
            description=f"Amount: ${amount}"
        )
        
        # PayPal option
        paypal_link = self.create_paypal_link(user_id, plan, amount)
        if paypal_link:
            embed.add_field(
                name="💳 PayPal",
                value=f"[Click here for PayPal]({paypal_link})",
                inline=False
            )
        
        # Crypto option
        crypto_info = self.create_crypto_payment_info(user_id, plan, amount)
        if crypto_info:
            crypto_text = f"**Payment ID:** `{crypto_info['payment_id']}`\n\n"
            crypto_text += "🪙 **Crypto Addresses:**\n"
            
            for coin, address in crypto_info['addresses'].items():
                if address:
                    crypto_text += f"**{coin}:** `{address}`\n"
            
            crypto_text += f"\n**Memo/Note:** `{crypto_info['memo']}`"
            
            embed.add_field(
                name="🪙 Cryptocurrency",
                value=crypto_text,
                inline=False
            )
        
        embed.add_field(
            name="⏰ Link expires in",
            value="30 minutes",
            inline=True
        )
        
        embed.add_field(
            name="📧 Next Steps",
            value="1. Complete payment\n"
                   "2. Use `!license <key>` to activate\n"
                   "3. DM me if you need help!",
            inline=False
        )
        
        # Add Indonesia-specific info
        embed.add_field(
            name="🌏 Indonesia Payment Info",
            value=INDONESIA_CONFIG["payment_methods"]["paypal"] + "\n" +
                   INDONESIA_CONFIG["payment_methods"]["crypto"],
            inline=False
        )
        
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                "📧 **Check your DMs for the payment link!**",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ **Error:** I can't DM you. Please enable DMs in your privacy settings.",
                ephemeral=True
            )

    @app_commands.command(name="verify-payment")
    async def verify_payment(self, interaction: discord.Interaction, payment_id: str):
        """Verify payment and issue license (admin only)"""
        # Check if user is admin (you'd implement proper admin check)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ **Admin only command**",
                ephemeral=True
            )
            return
        
        if payment_id not in self.active_payments:
            await interaction.response.send_message(
                "❌ **Payment ID not found**",
                ephemeral=True
            )
            return
        
        payment_info = self.active_payments[payment_id]
        
        # Generate license key
        import hashlib
        license_key = hashlib.sha256(f"{payment_info['user_id']}{payment_info['plan']}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        # Update payment status
        payment_info['status'] = 'completed'
        payment_info['license_key'] = license_key
        payment_info['completed_at'] = datetime.now()
        
        embed = discord.Embed(
            title="✅ PAYMENT VERIFIED",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Payment ID", value=payment_id, inline=True)
        embed.add_field(name="Plan", value=payment_info['plan'].upper(), inline=True)
        embed.add_field(name="License Key", value=f"```{license_key}```", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Also send to the user who paid
        try:
            user = await self.bot.fetch_user(int(payment_info['user_id']))
            await user.send(
                f"🎉 **Payment verified!**\n\n"
                f"Your license key: `{license_key}`\n\n"
                f"Use `!license {license_key}` to activate!"
            )
        except:
            pass

    @app_commands.command(name="payment-status")
    async def payment_status(self, interaction: discord.Interaction):
        """Check payment status"""
        user_id = str(interaction.user.id)
        
        # Find user's active payments
        user_payments = [
            (pid, info) for pid, info in self.active_payments.items()
            if info['user_id'] == user_id
        ]
        
        if not user_payments:
            await interaction.response.send_message(
                "📊 **No active payments found**\n\n"
                "Use `!buy-basic` or `!buy-pro` to start a payment.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📊 PAYMENT STATUS",
            color=discord.Color.blue()
        )
        
        for payment_id, info in user_payments:
            status_emoji = {'pending': '⏳', 'completed': '✅', 'expired': '❌'}.get(info['status'], '❓')
            
            embed.add_field(
                name=f"{status_emoji} Payment {payment_id}",
                value=f"Plan: {info['plan'].upper()}\n"
                       f"Amount: ${info['amount']}\n"
                       f"Status: {info['status'].title()}\n"
                       f"Created: {info['created_at'].strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="admin-payments")
    async def admin_payments(self, interaction: discord.Interaction):
        """View all payments (admin only)"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ **Admin only command**",
                ephemeral=True
            )
            return
        
        if not self.active_payments:
            await interaction.response.send_message(
                "📊 **No active payments**",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📊 ADMIN - ALL PAYMENTS",
            color=discord.Color.purple()
        )
        
        total_revenue = sum(info['amount'] for info in self.active_payments.values() if info['status'] == 'completed')
        
        embed.add_field(name="Total Revenue", value=f"${total_revenue:.2f}", inline=True)
        embed.add_field(name="Active Payments", value=str(len(self.active_payments)), inline=True)
        embed.add_field(name="Completed", value=str(len([p for p in self.active_payments.values() if p['status'] == 'completed'])), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(Payment(bot))
    logging.getLogger('payment').info("Payment cog setup complete")
