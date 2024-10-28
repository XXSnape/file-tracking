from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Logging(BaseSettings):
    """Настройки для логирования"""

    LOG_FILE: str


class App(BaseSettings):
    """Настройки приложения"""

    INTERVAL: int


class Folders(BaseSettings):
    """Настройки локальной и облачной файловых систем"""

    LOCAL_FOLDER: str
    CLOUD_FOLDER: str


class Api(BaseSettings):
    """Настройки для работы с API"""

    TOKEN: str


class Settings(BaseSettings):
    """Основной класс со всеми настройками"""

    API: Api = Api()
    FOLDERS: Folders = Folders()
    APP: App = App()
    LOGGING: Logging = Logging()


settings = Settings()
