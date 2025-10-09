import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    # Database
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "sportbot_db")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "sportbot_user")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")

    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Admin
    ADMIN_USER_IDS: List[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()
    ]

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

config = Config()