import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from handlers.user_handlers import start_command
from handlers.quiz_handlers import quiz_command, answer_callback
from utils.leaderboard import show_leaderboard
from utils.broadcast import broadcast_handler

# Ensure DB manager is initialized by importing it
from database.db_manager import db_manager 

# --- Logging Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Bot ko run karta hai aur saare handlers register karta hai."""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN set nahi hai. Please check .env or Heroku Config Vars.")
        return
        
    try:
        # Check if DB connection succeeded
        _ = db_manager 
    except ValueError as e:
        logger.error(f"Database Initialization failed: {e}")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # --- Handlers Setup ---
    
    # User Commands
    application.add_handler(CommandHandler("start", start_command))
    
    # Quiz and Leaderboard Commands
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))
    
    # Callback Query Handler for Quiz Answers
    application.add_handler(CallbackQueryHandler(answer_callback))

    # Broadcast Conversation Handler
    application.add_handler(broadcast_handler)

    # --- Run the bot ---
    logger.info("🚀 Starting Quiz Bot (Long Polling)...")
    application.run_polling()

if __name__ == "__main__":
    main()
