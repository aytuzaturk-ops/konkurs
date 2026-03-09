import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

# PostgreSQL connection URL
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to SQLite if DATABASE_URL is not set (for local development)
if not DATABASE_URL or DATABASE_URL == "contest.db":
    raise ValueError("DATABASE_URL environment variable must be set to a PostgreSQL connection string")
