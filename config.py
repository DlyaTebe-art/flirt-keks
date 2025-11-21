import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MODERATOR_CHAT_ID = int(os.getenv("MODERATOR_CHAT_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")

DATABASE_URL = os.getenv("DATABASE_URL")
