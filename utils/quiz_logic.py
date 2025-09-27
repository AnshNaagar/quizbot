# utils/quiz_logic.py

import logging
from telegram import Update, Bot
from telegram.ext import ContextTypes
from random import choice
from bson.objectid import ObjectId

from utils import db_manager

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 1. Helper Functions (Fetching & Updating Question)
# ----------------------------------------------------------------------

def fetch_and_update_next_question(db, session_id, category_id, language):
    """
    MongoDB se next non-repeated question fetch karta hai aur session update karta hai.
    """
    try:
        # Session data nikalna
        session = db.sessions.find_one({"_id": ObjectId(session_id)})
        
        if not session:
            return None

        questions_asked = session.get('questions_asked', [])
        total_questions = session['total_questions']
        current_index = len(questions_asked)
        
        if current_index >= total_questions:
            return None # Quiz set complete

        # Next non-repeated question dhoondhna (MongoDB Aggregation/Query)
        # Humne PostgreSQL se simple logic rakha hai: random ek question lo jiska ID asked mein na ho.
        
        # Ek simple approach:
        pipeline = [
            {"$match": {
                "category_id": category_id, 
                "language": language,
                "question_id": {"$nin": questions_asked} # Those not in asked list
            }},
            {"$sample": {"size": 1}} # Random ek question
        ]
        
        question_data = list(db.questions.aggregate(pipeline))
        
        if not question_data:
            logger.warning(f"No more questions available for session {session_id}.")
            return None
            
        question = question_data[0]
        question_id = question['question_id']
        
        # Session update karna
        new_questions_asked = questions_asked + [question_id]
        
        db.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$push": {"questions_asked": question_id},
             "$inc": {"current_question_index": 1}} # Index 1 se badhana
        )
        
        options = [question['option_a'], question['option_b']] 
        if question.get('option_c'): options.append(question['option_c'])
        if question.get('option_d'): options.append(question['option_d'])
        
        return {
            'id': question_id,
            'text': question['question_text'],
            'options': options,
            'correct_option_id': question['correct_option_id'],
            'current_index': current_index + 1,
            'total_questions': total_questions
        }

    except Exception as e:
        logger.error(f"Error in fetching/updating question: {e}")
        return None

# ----------------------------------------------------------------------
# 2. Main Job Queue Functions (Timer Logic)
# ----------------------------------------------------------------------

async def end_of_set_flow(bot: Bot, chat_id: int, session_id: str):
    """Jab saare questions ho jaate hain, toh result aur New Set ka option deta hai."""
    
    db = db_manager.get_db_connection()
    if db:
        session = db.sessions.find_one({"_id": ObjectId(session_id)})
        
        if session:
            score = session['current_score']
            total = session['total_questions']
            result_message = f"Quiz Set Complete! Aapka final score hai: {score} out of {total}."
        else:
            result_message = "Quiz set complete ho gaya."
        
        # Session status ko 'completed' set karein
        db.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": "completed"}}
        )
    else:
        result_message = "Quiz set complete ho gaya. Score check karne mein error hui."
        
    await bot.send_message(
        chat_id=chat_id,
        text=f"{result_message}\n\nKya aap naya set shuru karna chahte hain (/start) ya Leaderboard dekhna chahte hain (/leaderboard)?"
    )


async def send_next_quiz_poll(context: ContextTypes.DEFAULT_TYPE):
    """Next Quiz Poll bhejta hai aur phir khud ko dobara schedule karta hai."""
    job = context.job
    chat_id = job.context['chat_id']
    session_id = job.context['session_id']
    category_id = job.context['category_id']
    language = job.context['language']
    
    db = db_manager.get_db_connection()
    if not db:
        await context.bot.send_message(chat_id, "Quiz engine error: DB connection lost.")
        return

    # 1. Next question fetch aur session update karein
    question_data = fetch_and_update_next_question(db, session_id, category_id, language)

    if question_data is None:
        # Quiz set complete
        logger.info(f"Session {session_id} completed. Starting end flow.")
        await end_of_set_flow(context.bot, chat_id, session_id)
        return

    # 2. Quiz Poll bhejenge (15-second timer ke saath)
    try:
        await context.bot.send_poll(
            chat_id=chat_id,
            question=f"({question_data['current_index']}/{question_data['total_questions']}) {question_data['text']}",
            options=question_data['options'],
            type='quiz',
            correct_option_id=question_data['correct_option_id'],
            open_period=15, # 15-second timer
            is_anonymous=True
        )
        logger.info(f"Sent poll {question_data['current_index']} for session {session_id}")

        # 3. Next poll ko schedule karein
        context.job_queue.run_once(
            send_next_quiz_poll,
            16.5, # 15 sec poll time + 1.5 sec buffer
            context={
                'chat_id': chat_id, 
                'session_id': session_id,
                'category_id': category_id,
                'language': language
            },
            name=f"quiz_{session_id}_{question_data['current_index'] + 1}"
        )

    except Exception as e:
        logger.error(f"Error sending poll or scheduling next job: {e}")
