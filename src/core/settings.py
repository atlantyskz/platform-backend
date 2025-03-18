import os
from dotenv import load_dotenv

class Settings:

    load_dotenv()

    SECRET_KEY:str = os.getenv('SECRET_KEY')
    CLIENT_ID:str = os.getenv('CLIENT_ID')
    CLIENT_SECRET:str = os.getenv('CLIENT_SECRET')
    REDIRECT_URI:str = os.getenv('REDIRECT_URI')
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES :int = 60 * 24
    JWT_REFRESH_EXPIRE_MINUTES  : int = 60 * 24 *7
    LLM_SERVICE_URL:str =  os.getenv('LLM_SERVICE_URL')



    @property
    def get_db_url(self):
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT'))
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
        print( f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    
settings = Settings()
    