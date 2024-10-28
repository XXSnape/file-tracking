from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from loguru import logger

from api import YandexApi
from services.system import LocaleTracking


class FileSynchronization:
    """Предоставляет методы для синхронизации локальной и облачной файловых систем"""

    def __init__(
        self, yandex_api: YandexApi, local_tracking: LocaleTracking, interval: int
    ) -> None:
        """
        Инициализатор класс

        :param yandex_api: экземпляр YandexApi
        :param local_tracking: экземпляр LocaleTracking
        :param interval: интервал между проверками файлов (в секундах)
        """
        self._yandex_api = yandex_api
        self._locale_tracking = local_tracking
        self._interval = interval

    @classmethod
    def __compare_files(cls, files1: set[str], files2: set[str]) -> set[str]:
        """
        Ищет файлы, которые есть в одном множестве, но нет в другом.

        :param files1: файлы из первого множества
        :param files2: файлы из второго множества
        :return: файлы, которые есть в первом множестве, но нет во втором
        """
        return files1 - files2

    def _manipulate_files(
        self, files1: set[str], files2: set[str], func: Callable
    ) -> None:
        """
        Получает разницу между множествами с файлами и вызывает _interaction_with_api
        :param files1: файлы из первого множества
        :param files2: файлы из второго множества
        :param func: функция для взаимодействия с api
        :return: None
        """
        files = self.__compare_files(files1, files2)
        self._interaction_with_api(files=files, func=func)

    @classmethod
    def _interaction_with_api(cls, files: Iterable, func: Callable) -> None:
        """
        Делает несколько запросов к api с помощью пула потоков

        :param files: файлы, которые требуются для работы api
        :param func: функция для взаимодействия с api
        :return: None
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = [executor.submit(func, file) for file in files]
            for task in tasks:
                task.result()

    def _get_files_not_replaced_on_disk(
        self, local_files: set[str]
    ) -> tuple[str, ...] | None:
        """
        Получает информацию о локальных файлах и тех, которые хранятся в облаке.
        Формирует кортеж из файлов, которые были изменены локально и не изменены на Яндекс диске

        :param local_files: названия локальных файлов
        :return: None
        """
        local_files = self._locale_tracking.get_files_and_latest_modification(
            local_files
        )
        cloud_files = self._yandex_api.get_info()
        if cloud_files is None:
            return None
        result = tuple(
            filename
            for filename, modified in local_files.items()
            if cloud_files[filename] < modified
        )
        if result:
            logger.info("Измененные файлы {}", result)
            return result
        logger.info("Нет измененных файлов")
        return result

    def endless_synchronization(self) -> None:
        """
        Запускает бесконечный цикл.
        Загружает на диск новые файлы.
        Удаляет из диска файлы, которых нет в локальной директории.
        Перезаписывает локально измененные файлы.
        :return: None
        """
        self._yandex_api.create_cloud_folder_if_not_exists()
        while True:
            local_files = self._locale_tracking.get_files_in_local_folder()
            cloud_files = self._yandex_api.get_files_on_disk()
            if cloud_files is None:
                continue
            self._manipulate_files(
                files1=local_files, files2=cloud_files, func=self._yandex_api.load
            )
            self._manipulate_files(
                files1=cloud_files, files2=local_files, func=self._yandex_api.delete
            )
            files_not_replaces = self._get_files_not_replaced_on_disk(local_files)
            if files_not_replaces is None:
                continue
            self._interaction_with_api(
                files=files_not_replaces, func=self._yandex_api.reload
            )
            sleep(self._interval)
