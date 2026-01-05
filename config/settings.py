import os
from dotenv import load_dotenv

load_dotenv("config/secrets.env")

DATABASE_URL = os.getenv("DATABASE_URL")
