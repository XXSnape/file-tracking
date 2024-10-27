import os.path
from datetime import datetime
from enum import StrEnum

import requests
from loguru import logger


class OverWrite(StrEnum):
    NOT_OVERWRITING = "false"
    OVERWRITING = "true"


class YandexApi:
    def __init__(self, token: str, cloud_folder: str, local_folder: str) -> None:
        self._token = token
        self._cloud_folder = cloud_folder
        self._local_folder = local_folder
        self._AUTHORIZATION = {"Authorization": self._token}
        self.PATH_TO_FOLDER = {"path": self._cloud_folder}

    def create_cloud_folder_if_not_exists(self) -> None:
        try:
            response = requests.put(
                "https://cloud-api.yandex.net/v1/disk/resources",
                params=self.PATH_TO_FOLDER,
                headers=self._AUTHORIZATION,
            )
            if response.status_code == requests.codes.created:
                logger.info("Успешно создана папка")
            else:
                logger.info("Папка не создана, статус код = {}", response.status_code)

        except Exception as e:
            logger.info("Ошибка при создании папки: {}", str(e))

    def get_files_on_disk(self) -> set[str]:
        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources",
            params={**self.PATH_TO_FOLDER, "fields": "_embedded.items.name"},
            headers=self._AUTHORIZATION,
        )
        return {file["name"] for file in response.json()["_embedded"]["items"]}

    def _get_link_to_upload(self, path: str, overwrite: str) -> str | None:
        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources/upload",
            params={
                "path": f"{self._cloud_folder}/{path}",
                "overwrite": overwrite,
                "fields": "href",
            },
            headers=self._AUTHORIZATION,
        )
        if response.status_code == requests.codes.ok:
            return response.json()["href"]
        return None

    def load(self, path: str, overwrite: str = OverWrite.NOT_OVERWRITING) -> None:
        link_to_upload = self._get_link_to_upload(path=path, overwrite=overwrite)
        if link_to_upload is None:
            return
        with open(file=os.path.join(self._local_folder, path), mode="rb") as file:
            response = requests.put(link_to_upload, files={"file": file})
            if response.status_code != requests.codes.created:
                logger.error("Не удалось добавить файл на диск")
                return
            logger.info("Файл {} успешно добавлен на диск", path)

    def overwrite(self, path: str):
        self.load(path, overwrite=OverWrite.OVERWRITING)

    def delete(self, filename: str) -> None:
        response = requests.delete(
            "https://cloud-api.yandex.net/v1/disk/resources",
            params={"path": f"{self._cloud_folder}/{filename}"},
            headers=self._AUTHORIZATION,
        )
        logger.info("{} {}", response.status_code, response.text)

    def get_info(self) -> dict[str, float]:
        response = requests.get(
            "https://cloud-api.yandex.net/v1/disk/resources",
            params={
                **self.PATH_TO_FOLDER,
                "fields": "_embedded.items.modified,_embedded.items.name,_embedded.items.created",
            },
            headers=self._AUTHORIZATION,
        )
        print(response.json())
        return {
            file["name"]: datetime.timestamp(
                datetime.strptime(file["modified"].split("+")[0], "%Y-%m-%dT%H:%M:%S")
            )
            for file in response.json()["_embedded"]["items"]
        }
