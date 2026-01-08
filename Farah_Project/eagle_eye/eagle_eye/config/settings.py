from pydantic_settings import BaseSettings

from .folder_manager import SQL_DIR


class Settings(BaseSettings):
    APP_NAME: str = "Eagle Eye"
    LOG_LEVEL: str = "DEBUG"

    # WebRTC Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8521

    # Database Settings
    DB_URI: str = f"sqlite:///{SQL_DIR}/{APP_NAME.lower()}.db"

    # Notifications Settings
    GMAIL_USER: str = ""
    GMAIL_PASSWORD: str = ""
    TO_EMAILS: list[str] = []

    @property
    def notification_enabled(self) -> bool:
        return bool(self.GMAIL_USER and self.GMAIL_PASSWORD)

    class ConfigDict:
        env_file = ".env"


settings = Settings()
