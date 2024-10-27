from typing import BinaryIO

from loguru import logger

import requests


class HandleRequestMixin:
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
        try:
            response = requests.request(
                method=method, url=url, params=params, headers=headers, files=files
            )
            if statuses:
                for status, message in statuses.items():
                    if response.status_code == status:
                        logger.info("{}", message)
            return response
        except requests.ConnectionError:
            logger.error("Не удалось соединиться с сервером. {}", error_text)
        except requests.Timeout:
            logger.error("Сервер не ответил на запрос. {}", error_text)
        except Exception as e:
            logger.error("{}. {}", str(e), error_text)
