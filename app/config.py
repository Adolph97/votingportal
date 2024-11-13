from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    # Environment detection
    IS_PRODUCTION: bool = os.getenv('RENDER', 'false').lower() == 'true'
    
    # Port configuration
    PORT: int = int(os.getenv('PORT', 10000))
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/votingapp'
    )
    
    # Paystack settings
    PAYSTACK_SECRET_KEY: str = os.getenv('PAYSTACK_SECRET_KEY', '')
    PAYSTACK_PUBLIC_KEY: str = os.getenv('PAYSTACK_PUBLIC_KEY', '')
    
    # Security settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', '')
    ADMIN_PASSWORD: str = os.getenv('ADMIN_PASSWORD', '')
    
    # Render specific settings
    RENDER: Optional[str] = os.getenv('RENDER')
    RENDER_EXTERNAL_URL: Optional[str] = os.getenv('RENDER_EXTERNAL_URL')
    
    @property
    def base_url(self) -> str:
        """Get the correct application URL"""
        if self.IS_PRODUCTION:
            return os.getenv('RENDER_EXTERNAL_URL', f'http://localhost:{self.PORT}')
        return f"http://localhost:{self.PORT}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields
        extra = "allow"

settings = Settings() 