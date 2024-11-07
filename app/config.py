from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./votes.db"
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    SECRET_KEY: str
    ADMIN_PASSWORD: str
    BASE_URL: str = os.environ.get('VERCEL_URL', 'http://localhost:8000')
    if BASE_URL.startswith('http://'):
        BASE_URL = f"https://{BASE_URL.split('http://')[-1]}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings() 