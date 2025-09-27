from database.db_manager import db_manager
from telegram import Update
from telegram.ext import ContextTypes # <-- Corrected Import

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Top users aur unke scores dikhata hai."""
    
    top_users = db_manager.get_top_users(limit=10)
    
    leaderboard_text = "🏆 **Global Quiz Champions** 🏆\n\n"
    
    if not top_users:
        leaderboard_text += "Abhi tak koi score nahi hai! /quiz karke shuru karo."
    else:
        for i, user_data in enumerate(top_users): 
            username = user_data.get('username', f"User {user_data['user_id']}")
            leaderboard_text += f"{i+1}. **{username}** - **{user_data['score']} points**\n"
            
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')
