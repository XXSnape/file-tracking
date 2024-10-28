from loguru import logger

from api import YandexApi
from core import settings
from services import FileSynchronization, LocaleTracking


def main() -> None:
    """
    Запускает приложение для синхронизации файлов

    :return: None
    """
    logger.add(settings.LOGGING.LOG_FILE, rotation="5 MB")
    logger.debug("Добавлено логирование файлов")
    api = YandexApi(
        token=settings.API.TOKEN,
        cloud_folder=settings.FOLDERS.CLOUD_FOLDER,
        local_folder=settings.FOLDERS.LOCAL_FOLDER,
    )
    logger.debug("Создан экземпляр класса YandexApi для работы с Яндекс диском")
    local_tracking = LocaleTracking(local_folder=settings.FOLDERS.LOCAL_FOLDER)
    logger.debug(
        "Создан экземпляр класса LocaleTracking для работы с файловой системой"
    )

    app = FileSynchronization(
        yandex_api=api,
        local_tracking=local_tracking,
        interval=settings.APP.INTERVAL,
    )
    logger.info(
        "Запускается приложение. Отслеживаемая директория на файловой системе - {}. "
        "Директория на Яндекс диске - {}",
        settings.FOLDERS.LOCAL_FOLDER,
        settings.FOLDERS.CLOUD_FOLDER,
    )
    app.endless_synchronization()


if __name__ == "__main__":
    main()
