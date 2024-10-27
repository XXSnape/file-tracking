import os.path
from datetime import datetime

import requests
from loguru import logger
from .api_mixin import HandleRequestMixin


NOT_OVERWRITING = ("false", "загружен")
OVERWRITING = ("true", "перезаписан")


class YandexApi(HandleRequestMixin):
    def __init__(self, token: str, cloud_folder: str, local_folder: str) -> None:
        self._token = token
        self._cloud_folder = cloud_folder
        self._local_folder = local_folder
        self._AUTHORIZATION = {"Authorization": self._token}
        self.PATH_TO_FOLDER = {"path": self._cloud_folder}

    def create_cloud_folder_if_not_exists(self) -> None:
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            method="put",
            error_text="Облачная директория не создана",
            statuses={requests.codes.created: "Облачная директория создана успешно"},
            params=self.PATH_TO_FOLDER,
            headers=self._AUTHORIZATION,
        )
        if response.status_code == requests.codes.unauthorized:
            logger.info("Не получилось авторизоваться, проверьте токен")
            exit(0)

    def get_files_on_disk(self) -> set[str]:
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            params={**self.PATH_TO_FOLDER, "fields": "_embedded.items.name"},
            statuses={requests.codes.ok: "Получен список файлов в облаке"},
            headers=self._AUTHORIZATION,
            error_text="Не удалось получить список файлов в облаке",
        )
        if response:
            return {file["name"] for file in response.json()["_embedded"]["items"]}

    def _get_link_to_upload(self, path: str, overwrite: tuple[str, str]) -> str | None:
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources/upload",
            params={
                "path": f"{self._cloud_folder}/{path}",
                "overwrite": overwrite[0],
                "fields": "href",
            },
            statuses={requests.codes.ok: f"Получена ссылка на скачивание {path}"},
            headers=self._AUTHORIZATION,
            error_text=f"Не удалось получить ссылку для загрузки {path}",
        )
        if response.status_code == requests.codes.ok:
            return response.json()["href"]
        logger.error(f"Не удалось получить ссылку для загрузки {path}")
        return None

    def load(self, path: str, overwrite: tuple[str, str] = NOT_OVERWRITING) -> None:
        link_to_upload = self._get_link_to_upload(path=path, overwrite=overwrite)
        if link_to_upload is None:
            logger.error("Нет ссылки для загрузки {}", path)
            return
        try:
            file_path = os.path.join(self._local_folder, path)
            with open(file=file_path, mode="rb") as file:
                self._make_request(
                    url=link_to_upload,
                    method="put",
                    error_text=f"Не удалось загрузить {path} в облако",
                    files={"file": file},
                    statuses={
                        requests.codes.created: f"Файл {path} успешно {overwrite[1]}",
                        requests.codes.accepted: "Файл принят сервером, но еще не был перенесен непосредственно в Яндекс Диск",
                        requests.codes.content_too_large: "Размер файла больше допустимого",
                        requests.codes.server_error: "Ошибка сервера",
                        requests.codes.insufficient_storage: "Недостаточно места на сервере",
                    },
                )
        except FileNotFoundError:
            logger.error("Не найден файл по пути {}", file_path)

    def overwrite(self, path: str):
        self.load(path, overwrite=OVERWRITING)

    def delete(self, filename: str) -> None:
        self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            method="delete",
            params={"path": f"{self._cloud_folder}/{filename}"},
            headers=self._AUTHORIZATION,
            error_text=f"Не удалось удалить {filename}",
            statuses={requests.codes.no_content: f"{filename} успешно удален"},
        )

    def get_info(self) -> dict[str, float] | None:
        response = self._make_request(
            url="https://cloud-api.yandex.net/v1/disk/resources",
            params={
                **self.PATH_TO_FOLDER,
                "fields": "_embedded.items.modified,_embedded.items.name",
            },
            headers=self._AUTHORIZATION,
            error_text="Не удалось получить информацию о файлах",
            statuses={requests.codes.ok: "Информация о модификации файлов получена"},
        )
        if response:
            return {
                file["name"]: datetime.timestamp(
                    datetime.strptime(
                        file["modified"].split("+")[0], "%Y-%m-%dT%H:%M:%S"
                    )
                )
                for file in response.json()["_embedded"]["items"]
            }
