from telegram import Update
from telegram.ext import ContextTypes # ContextTypes fix
from database.db_manager import db_manager

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message aur user ko database mein add/fetch karta hai."""
    user = update.effective_user
    username = user.username or user.first_name
    
    user_data = db_manager.get_or_create_user(user.id, username)
    
    await update.message.reply_text(
        f"Namaste, **{user.first_name}**! 👋 Quiz Bot mein tumhara swagat hai.\n\n"
        "Aapka current score hai: **{user_data['score']}**\n\n"
        "Quiz shuru karne ke liye /quiz aur rank dekhne ke liye /leaderboard likho.",
        parse_mode='Markdown'
    )
