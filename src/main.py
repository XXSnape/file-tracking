from core import settings
from api import YandexApi
from loguru import logger

from services import LocaleTracking, FileSynchronization


def main():
    logger.add(settings.LOGGING.LOG_FILE)

    api = YandexApi(
        token=settings.API.TOKEN,
        cloud_folder=settings.FOLDERS.CLOUD_FOLDER,
        local_folder=settings.FOLDERS.LOCAL_FOLDER,
    )

    local_tracking = LocaleTracking(local_folder=settings.FOLDERS.LOCAL_FOLDER)

    app = FileSynchronization(
        yandex_api=api,
        local_tracking=local_tracking,
        interval=settings.APP.INTERVAL,
    )

    app.endless_synchronization()


if __name__ == "__main__":
    main()
