import os
from dotenv import load_dotenv

class Settings:

    load_dotenv()

    SECRET_KEY:str = os.getenv('SECRET_KEY')
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES :int = 60 * 24
    JWT_REFRESH_EXPIRE_MINUTES  : int = 60 * 24 *7
    LLM_SERVICE_URL:str = 'http://0.0.0.0:8001'



    @property
    def get_db_url(self):
        return f"postgresql+asyncpg://postgres:postgres@localhost:5432/platform-db"

settings = Settings()
    