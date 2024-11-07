from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Environment
    IS_PRODUCTION: bool = os.getenv('RENDER', 'false').lower() == 'true'
    
    # Database
    DATABASE_URL: str = "sqlite:///./votes.db"
    
    # Paystack
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    
    # Security
    SECRET_KEY: str
    ADMIN_PASSWORD: str
    
    # Application
    BASE_URL: str = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8000')
    if BASE_URL.endswith('/'):
        BASE_URL = BASE_URL[:-1]
    
    # Ensure HTTPS in production
    if IS_PRODUCTION and BASE_URL.startswith('http://'):
        BASE_URL = f"https://{BASE_URL.split('http://')[-1]}"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }

settings = Settings() 