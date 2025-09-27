import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Core Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0)) # Default to 0 if not set, to prevent errors
MONGO_URI = os.environ.get("MONGO_URI")

# --- Bot Settings ---
SCORE_PER_QUESTION = 10

# --- Conversation States for Broadcast ---
BROADCAST_MESSAGE = 1

# Broadcast Functions (will be imported into broadcast.py/main.py)
# Note: Admin ID ko check karne ka simple function yahan define kar dete hain
def is_admin(user_id):
    return user_id == ADMIN_ID
