from collections.abc import Iterable, Callable
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from api import YandexApi
from datetime import datetime

from services.system import LocaleTracking


class FileSynchronization:
    def __init__(
        self, yandex_api: YandexApi, local_tracking: LocaleTracking, interval: int
    ) -> None:
        self.yandex_api = yandex_api
        self.locale_tracking = local_tracking
        self.interval = interval

    @classmethod
    def __compare_files(cls, files1: set[str], files2: set[str]) -> set[str]:
        return files1 - files2

    def _manipulate_files(
        self, files1: set[str], files2: set[str], func: Callable
    ) -> None:
        files = self.__compare_files(files1, files2)
        self._interaction_with_api(files=files, func=func)

    @classmethod
    def _interaction_with_api(cls, files: Iterable, func: Callable) -> None:
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = [executor.submit(func, file) for file in files]
            for task in tasks:
                task.result()

    def _get_files_not_replaced_on_disk(
        self, local_files: set[str]
    ) -> tuple[str, ...] | None:
        local_files = self.locale_tracking.get_files_and_latest_modification(
            local_files
        )
        cloud_files = self.yandex_api.get_info()
        if cloud_files is None:
            return None
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
        self.yandex_api.create_cloud_folder_if_not_exists()
        while True:
            local_files = self.locale_tracking.get_files_in_local_folder()
            cloud_files = self.yandex_api.get_files_on_disk()
            if cloud_files is None:
                continue
            self._manipulate_files(
                files1=local_files, files2=cloud_files, func=self.yandex_api.load
            )
            self._manipulate_files(
                files1=cloud_files, files2=local_files, func=self.yandex_api.delete
            )
            files_not_replaces = self._get_files_not_replaced_on_disk(local_files)
            if files_not_replaces is None:
                continue
            self._interaction_with_api(
                files=files_not_replaces, func=self.yandex_api.overwrite
            )
            sleep(self.interval)
