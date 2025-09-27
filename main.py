import os
# ... other imports ...
from telegram.ext import Application, CommandHandler, CallbackQueryHandler # ContextTypes ko yahan se import karne ki zarurat nahi, woh handlers mein ho gaya hai

from config import BOT_TOKEN, ADMIN_ID # ADMIN_ID yahan use hoga

# ... handlers aur utils imports ...
from database.db_manager import db_manager 
import logging
# logging setup...

# New Function
async def send_startup_notification(app: Application, admin_id: int):
    """Admin ko bot start hone ki notification bhejta hai."""
    try:
        # Check karte hain ki Admin ID 0 toh nahi hai aur usne bot ko block nahi kiya hai
        if admin_id != 0:
            await app.bot.send_message(
                admin_id,
                "✅ **Quiz Bot has successfully started (Deployed).**\n\n"
                "Worker dyno is running in long-polling mode. Bot ab live hai! Test karne ke liye /start command bhejkar check karo.",
                parse_mode='Markdown'
            )
    except Exception as e:
        # Agar admin ne bot ko block kiya hai, toh yahan error aayega.
        logger.error(f"Failed to send startup notification to admin: {e}")

# New Async hook
async def post_init(application: Application) -> None:
    """Application initialize hone ke baad run hota hai."""
    await send_startup_notification(application, ADMIN_ID)


def main():
    # ... config and db checks ...
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Naya Hook: post_init function ko application object se jod do
    application.post_init = post_init

    # --- Handlers Setup ---
    # ... (Add all handlers here) ...
    
    # --- Run the bot ---
    logger.info("🚀 Starting Quiz Bot (Long Polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
