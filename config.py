import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
_admin_raw = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()]
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0
DATABASE_URL = os.getenv("DATABASE_URL", "")
