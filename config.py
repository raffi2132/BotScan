import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger('config')

load_dotenv()

# Discord Configuration
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN is required")

try:
    LICENSE_CHANNEL_ID = int(os.getenv('LICENSE_CHANNEL_ID'))
except (TypeError, ValueError):
    raise ValueError("LICENSE_CHANNEL_ID must be a valid integer")

try:
    PREMIUM_ROLE_ID = int(os.getenv('PREMIUM_ROLE_ID', '0'))
except (TypeError, ValueError):
    PREMIUM_ROLE_ID = 0

WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Roblox Scanner Configuration
ROBLOX_SCANNER_PATH = os.getenv('ROBLOX_SCANNER_PATH', './roblox_trend_scanner_monetized.py')

# Payment Configuration
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
USDC_WALLET_ADDRESS = os.getenv('USDC_WALLET_ADDRESS')
USDT_WALLET_ADDRESS = os.getenv('USDT_WALLET_ADDRESS')
ETH_WALLET_ADDRESS = os.getenv('ETH_WALLET_ADDRESS')

# Pricing Configuration
try:
    BASIC_PRICE = float(os.getenv('BASIC_PRICE', '10.00'))
    PRO_PRICE = float(os.getenv('PRO_PRICE', '10.00'))
except (TypeError, ValueError):
    BASIC_PRICE = 10.00
    PRO_PRICE = 10.00

# License Configuration
try:
    LICENSE_DURATION_DAYS = int(os.getenv('LICENSE_DURATION_DAYS', '30'))
    MAX_LICENSES_PER_USER = int(os.getenv('MAX_LICENSES_PER_USER', '1'))
except (TypeError, ValueError):
    LICENSE_DURATION_DAYS = 30
    MAX_LICENSES_PER_USER = 1

# Indonesia Localization
INDONESIA_CONFIG = {
    "welcome_message": "Selamat datang ke Roblox Scanner Pro!",
    "premium_required": "Dibutuhkan lisensi premium untuk fitur ini",
    "payment_methods": {
        "paypal": "PayPal - Mendukung bank BCA, Mandiri, BNI, BRI",
        "crypto": "Crypto - USDC, USDT, ETH (instan)",
        "local": "Transfer Bank Indonesia"
    },
    "currency": "IDR",
    "price_premium_idr": 150000  # ~$10.00
}

# Bot Configuration
BOT_PREFIX = "!"
BOT_NAME = "Roblox Scanner Pro"
BOT_DESCRIPTION = "Advanced Roblox market intelligence tool"

# Command Configuration
COMMANDS = {
    "license": "Activate premium license",
    "premium": "View pricing plans",
    "status": "Check license status",
    "scan": "Run Roblox scan",
    "buy": "Purchase premium",
    "support": "Get help"
}

def check_config():
    """Validate all configuration settings"""
    logger.info("Validating configuration...")
    
    # Check required Discord settings
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is required")
    
    if not LICENSE_CHANNEL_ID:
        raise ValueError("LICENSE_CHANNEL_ID is required")
    
    # Check Roblox scanner path
    if not os.path.exists(ROBLOX_SCANNER_PATH):
        logger.warning(f"Roblox scanner not found at: {ROBLOX_SCANNER_PATH}")
    
    logger.info("Configuration validation completed")
    return True

def get_payment_info():
    """Get payment configuration for display"""
    payment_methods = {}
    
    if PAYPAL_CLIENT_ID:
        payment_methods["paypal"] = {
            "available": True,
            "description": INDONESIA_CONFIG["payment_methods"]["paypal"],
            "fees": "2.9% + $0.30"
        }
    
    if USDC_WALLET_ADDRESS:
        payment_methods["crypto"] = {
            "available": True,
            "description": INDONESIA_CONFIG["payment_methods"]["crypto"],
            "fees": "1-3%",
            "addresses": {
                "USDC": USDC_WALLET_ADDRESS,
                "USDT": USDT_WALLET_ADDRESS,
                "ETH": ETH_WALLET_ADDRESS
            }
        }
    
    return payment_methods

def get_pricing_info():
    """Get pricing information"""
    return {
        "premium": {
            "price_usd": PRO_PRICE,
            "price_idr": INDONESIA_CONFIG["price_premium_idr"],
            "features": [
                "UNLIMITED scanning",
                "Advanced keyword analysis",
                "Creator performance metrics", 
                "Clothing hijacker scanner",
                "Export to JSON/CSV",
                "Priority support",
                "API access",
                "Multi-device support"
            ]
        }
    }
