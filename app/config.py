from pydantic_settings import BaseSettings
import os

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
    
    # Application settings
    BASE_URL: str = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8000')

    @property
    def app_url(self) -> str:
        """Get the correct application URL based on environment"""
        if self.IS_PRODUCTION:
            # Use RENDER_EXTERNAL_URL in production
            url = os.getenv('RENDER_EXTERNAL_URL', '')
            if not url:
                # Fallback to manual URL if needed
                url = "https://votingportal.onrender.com"
        else:
            url = "http://localhost:8000"

        # Remove trailing slash if present
        return url.rstrip('/')

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }

settings = Settings() 