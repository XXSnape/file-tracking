from time import sleep

from loguru import logger

from api import YandexApi
from datetime import datetime

from services.system import LocaleTracking


class FileSynchronization:
    def __init__(
        self, yandex_api: YandexApi, local_tracking: LocaleTracking, interval: int
    ):
        self.yandex_api = yandex_api
        self.locale_tracking = local_tracking
        self.interval = interval

    @classmethod
    def __compare_files(cls, files1: set[str], files2: set[str]) -> set[str]:
        return files1 - files2

    def _upload_new_files_on_disk(self, local_files: set[str], cloud_files: set[str]):
        new_files = self.__compare_files(local_files, cloud_files)
        logger.debug("new files: {}", str(new_files))
        for file in new_files:
            self.yandex_api.load(file)

    def _delete_unnecessary_files(self, local_files: set[str], cloud_files: set[str]):
        unnecessary_files = self.__compare_files(cloud_files, local_files)
        logger.debug("deleted files: {}", str(unnecessary_files))
        for file in unnecessary_files:
            self.yandex_api.delete(file)

    def _get_files_not_replaced_on_disk(self, local_files: set[str]) -> tuple[str, ...]:
        local_files = self.locale_tracking.get_files_and_latest_modification(
            local_files
        )
        cloud_files = self.yandex_api.get_info()
        return tuple(
            filename
            for filename, modified in local_files.items()
            if datetime.fromtimestamp(cloud_files[filename])
            < datetime.utcfromtimestamp(modified)
        )

    def _overwrite_files(self, files: tuple[str, ...]):
        for file in files:
            self.yandex_api.overwrite(file)

    def endless_synchronization(self):
        while True:
            local_files = self.locale_tracking.get_files_in_local_folder()
            cloud_files = self.yandex_api.get_files_on_disk()
            self._upload_new_files_on_disk(local_files, cloud_files)
            self._delete_unnecessary_files(local_files, cloud_files)
            files_not_replaces = self._get_files_not_replaced_on_disk(local_files)
            self._overwrite_files(files_not_replaces)
            sleep(self.interval)
