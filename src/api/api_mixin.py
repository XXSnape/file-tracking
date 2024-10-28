from typing import BinaryIO

import requests
from loguru import logger


class HandleRequestMixin:
    """Миксин для обработки запросов к api"""

    @classmethod
    def _make_request(
        cls,
        url: str,
        error_text: str,
        method: str = "get",
        statuses: dict[int, str] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        files: dict[str, BinaryIO] | None = None,
    ) -> requests.Response | None:
        """
        Делает запрос на нужный ресурс, обрабатывает возможные ошибки и возвращает ответ

        :param url: url, на который нужно отправить запрос
        :param error_text: текст ошибки, который должен быть залогирован в случае исключения
        :param method: метод отправки запроса
        :param statuses: словарь со статусами и сообщениями, которые будут залогированы,
         если статус ответа совпадет хотя бы с одним из переденных
        :param params: параметры запроса
        :param headers: заголовки запроса
        :param files: файлы, отправляемые на сервер
        :return: requests.Response или None, если произойдет ошибка
        """
        try:
            response = requests.request(
                method=method, url=url, params=params, headers=headers, files=files
            )
            if statuses:
                for status, message in statuses.items():
                    if response.status_code == status:
                        logger.info("{}", message)
                        return response
            return response
        except requests.ConnectionError:
            logger.exception("Не удалось соединиться с сервером. {}", error_text)
            return
        except requests.Timeout:
            logger.exception("Сервер не ответил на запрос. {}", error_text)
        except requests.RequestException:
            logger.exception("Произошла ошибка. {}", error_text)
