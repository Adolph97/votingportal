from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    # Environment detection
    IS_PRODUCTION: bool = os.getenv('RENDER', 'false').lower() == 'true'
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./votes.db"
    
    # Paystack settings
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    
    # Security settings
    SECRET_KEY: str
    ADMIN_PASSWORD: str
    
    # Get the Render URL or fallback to localhost
    RENDER_EXTERNAL_URL: Optional[str] = os.getenv('RENDER_EXTERNAL_URL')
    
    @property
    def base_url(self) -> str:
        """Get the correct application URL"""
        if self.IS_PRODUCTION:
            if not self.RENDER_EXTERNAL_URL:
                raise ValueError("RENDER_EXTERNAL_URL must be set in production")
            base = self.RENDER_EXTERNAL_URL
        else:
            base = "http://localhost:8000"
            
        # Remove trailing slash if present
        return base.rstrip('/')

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 