from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes # ContextTypes ko telegram.ext se import kiya
from database.db_manager import db_manager
from config import SCORE_PER_QUESTION

# --- Helper Function ---
async def send_next_question(user_id: int, last_q_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User ko next question bhejta hai."""
    
    question = db_manager.get_next_question(last_q_id)
    
    if not question:
        await context.bot.send_message(user_id, "🎉 **Quiz Series Complete!** Saare questions attempt ho chuke hain.\n/leaderboard par apni rank dekho!", parse_mode='Markdown')
        return

    # Inline Keyboard for options
    keyboard = []
    for option in question["options"]:
        callback_data = f'{question["q_id"]}|{option}'
        keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        user_id,
        f"💡 Sawal **#{question['q_id']}**: {question['text']}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# --- Command Handlers ---

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quiz round shuru karta hai."""
    user_id = update.effective_user.id
    
    user_data = db_manager.get_or_create_user(user_id, update.effective_user.first_name)
    last_q_id = user_data.get('last_q_id', 0)
    
    await send_next_question(user_id, last_q_id, context)

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User ke answer ko handle karta hai."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    q_id_str, selected_answer = query.data.split('|')
    q_id = int(q_id_str)
    
    question = db_manager.get_question_by_id(q_id)
    
    if not question:
        await query.edit_message_text(text="❓ Error: Yeh sawal ab valid nahi hai.")
        return

    # Check Answer and assign points
    is_correct = selected_answer == question["answer"]
    points = SCORE_PER_QUESTION if is_correct else 0
    
    # Update score and progress in MongoDB
    db_manager.update_user_score_and_progress(user_id, q_id, points)

    result_text = f"✅ **Sahi Jawab!** Aapko {points} points mile." if is_correct else f"❌ **Galat Jawab.** Sahi jawab hai: **{question['answer']}**"
    
    # Edit the message
    await query.edit_message_text(
        text=f"{result_text}\n\nSawal: {question['text']}\nAapka Jawab: {selected_answer}", 
        parse_mode='Markdown'
    )

    # Send next question
    await send_next_question(user_id, q_id, context)
