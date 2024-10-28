import os
from datetime import datetime


class LocaleTracking:
    """Предоставляет методы для работы с локальной файловой системой"""

    def __init__(self, local_folder: str) -> None:
        """
        Инициализатор класса

        :param local_folder: локальная директория для отслеживания
        """
        self._local_folder = local_folder

    def get_files_in_local_folder(self) -> set[str]:
        """
        Собирает названия файлов в локальной директории

        :return: множество из названий файлов
        """
        return set(os.listdir(self._local_folder))

    def get_files_and_latest_modification(
        self, locale_files: set[str]
    ) -> dict[str, datetime]:
        """
        Собирает информацию о датах последних модификаций файлов

        :param locale_files: названия локальных файлов
        :return: словарь из названий файлов и дат их последних модификаций
        """
        return {
            filename: datetime.utcfromtimestamp(
                os.path.getmtime(os.path.join(self._local_folder, filename))
            )
            for filename in locale_files
        }
