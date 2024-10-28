import os.path
from datetime import datetime
from time import sleep

import requests
from loguru import logger

from .api_mixin import HandleRequestMixin

NOT_OVERWRITING = ("false", "загружен")
OVERWRITING = ("true", "перезаписан")


class YandexApi(HandleRequestMixin):
    """
    Предоставляет методы для работы с апи Яндекс диска
    """

    def __init__(self, token: str, cloud_folder: str, local_folder: str) -> None:
        """
        Инициализатор класса

        :param token: токен доступа к api
        :param cloud_folder: название директории в яндекс диске, которая должна быть связана с local_folder
        :param local_folder: локальная директория для отслеживания
        """
        self._token = token
        self._cloud_folder = cloud_folder
        self._local_folder = local_folder
        self._authorization = {"Authorization": self._token}
        self._path_to_folder = {"path": self._cloud_folder}

    def create_cloud_folder_if_not_exists(self) -> None:
        """
        Создает директорию cloud_folder, если она не создана.
        Вызывается перед запуском всех методов, поэтому проверяет токен на корректность.
        В случае, если токен невалиден, прерывает работу программы

        :return: None
        """
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            method="put",
            error_text="Облачная директория не создана",
            statuses={requests.codes.created: "Облачная директория создана успешно"},
            params=self._path_to_folder,
            headers=self._authorization,
        )
        if response is None:
            while response is None:
                logger.error(
                    "Произошла ошибка при получении ответ от сервера. Пробуем снова"
                )
                sleep(5)
                response = self._make_request(
                    url="https://cloud-api.yandex.net/v1/disk/resources",
                    method="put",
                    error_text="Облачная директория не создана",
                    statuses={
                        requests.codes.created: "Облачная директория создана успешно"
                    },
                    params=self._path_to_folder,
                    headers=self._authorization,
                )
        if response.status_code == requests.codes.unauthorized:
            logger.error("Не получилось авторизоваться, проверьте токен")
            exit(-1)

    def get_files_on_disk(self) -> set[str]:
        """
        Делает запрос на получение всех файлов на диске

        :return: названия файлов на диске
        """
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            params={**self._path_to_folder, "fields": "_embedded.items.name"},
            statuses={requests.codes.ok: "Получен список файлов в облаке"},
            headers=self._authorization,
            error_text="Не удалось получить список файлов в облаке",
        )
        if response:
            return {file["name"] for file in response.json()["_embedded"]["items"]}

    def _get_link_to_upload(
        self, filename: str, overwrite: tuple[str, str]
    ) -> str | None:
        """
        Делает запрос на получение ссылки для загрузки файла

        :param filename: название файла
        :param overwrite: кортеж из значения, передающегося в апи и сообщения для логирования
        :return: ссылка или None
        """
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources/upload",
            params={
                "path": f"{self._cloud_folder}/{filename}",
                "overwrite": overwrite[0],
                "fields": "href",
            },
            statuses={requests.codes.ok: f"Получена ссылка на скачивание {filename}"},
            headers=self._authorization,
            error_text=f"Не удалось получить ссылку для загрузки {filename}",
        )
        if response.status_code == requests.codes.ok:
            return response.json()["href"]
        logger.error(f"Не удалось получить ссылку для загрузки {filename}")
        return None

    def load(self, filename: str, overwrite: tuple[str, str] = NOT_OVERWRITING) -> None:
        """
        Делает запрос на загрузку файла

        :param filename: название файла
        :param overwrite: кортеж из значения, передающегося в апи и сообщения для логирования
        :return: None
        """
        link_to_upload = self._get_link_to_upload(
            filename=filename, overwrite=overwrite
        )
        if link_to_upload is None:
            logger.error("Нет ссылки для загрузки {}", filename)
            return
        try:
            file_path = os.path.join(self._local_folder, filename)
            with open(file=file_path, mode="rb") as file:
                self._make_request(
                    url=link_to_upload,
                    method="put",
                    error_text=f"Не удалось загрузить {filename} в облако",
                    files={"file": file},
                    statuses={
                        requests.codes.created: f"Файл {filename} успешно {overwrite[1]}",
                        requests.codes.accepted: "Файл принят сервером,"
                        " но еще не был перенесен непосредственно в Яндекс Диск",
                        requests.codes.content_too_large: "Размер файла больше допустимого",
                        requests.codes.server_error: "Ошибка сервера",
                        requests.codes.insufficient_storage: "Недостаточно места на сервере",
                    },
                )
        except FileNotFoundError:
            logger.exception("Не найден файл по пути {}", file_path)

    def reload(self, filename: str) -> None:
        """
        Делает запрос на перезапись файла

        :param filename: название файла
        :return: None
        """
        self.load(filename, overwrite=OVERWRITING)

    def delete(self, filename: str) -> None:
        """
        Делает запрос на удаление файла

        :param filename: название файла
        :return: None
        """
        self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            method="delete",
            params={"path": f"{self._cloud_folder}/{filename}"},
            headers=self._authorization,
            error_text=f"Не удалось удалить {filename}",
            statuses={requests.codes.no_content: f"{filename} успешно удален"},
        )

    def get_info(self) -> dict[str, datetime] | None:
        """
        Делает запрос на получение информации о файлах.
        Собирает информацию о последней модификации файлов в облаке
        :return: словарь с названиями файлов и датами их последних изменений или None
        """
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            params={
                **self._path_to_folder,
                "fields": "_embedded.items.modified,_embedded.items.name",
            },
            headers=self._authorization,
            error_text="Не удалось получить информацию о файлах",
            statuses={requests.codes.ok: "Информация о модификации файлов получена"},
        )
        if response:
            return {
                file["name"]: datetime.strptime(
                    file["modified"].split("+")[0], "%Y-%m-%dT%H:%M:%S"
                )
                for file in response.json()["_embedded"]["items"]
            }
