from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Logging(BaseSettings):
    LOG_FILE: str


class App(BaseSettings):
    INTERVAL: int


class Folders(BaseSettings):
    LOCAL_FOLDER: str
    CLOUD_FOLDER: str


class Api(BaseSettings):
    TOKEN: str


class Settings(BaseSettings):
    API: Api = Api()
    FOLDERS: Folders = Folders()
    APP: App = App()
    LOGGING: Logging = Logging()


settings = Settings()
