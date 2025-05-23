# Приложение для синхронизации файлов в локальной директории и Яндекс Диске

# Основные используемые библиотеки

* ### [Requests](https://requests.readthedocs.io/en/latest/index.html)
* ### [Pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
* ### [Loguru](https://loguru.readthedocs.io/en/stable/overview.html)

## Что делает приложение?
* Добавляет новые файлы в Яндекс Диск, если они появляются в локальной директории
* Если файлы в локальной директории удалены, то приложение удаляет их и с Яндекс Диска
* При модификации файлов отправляет все изменения на Яндекс Диск
* Записывает все действия в файл для логирования

## Как запустить приложение?
* Склонировать репозиторий на локальную машину
```sh
git clone https://github.com/XXSnape/file-tracking.git
```

* Создать файл .env, подобный .env.template в корне проекта только с нужными данными:

1. [x] TOKEN - токен для работы с приложением [Яндекс Диска](https://yandex.ru/dev/disk-api/doc/ru/concepts/quickstart).
Обязательно выдайте права для взаимодействия с приложением.
Если не получается выбрать нужные, попробуйте создать приложение [по этой ссылке](https://oauth.yandex.ru/client/new)
2. [x] LOCAL_FOLDER - локальная директория для отслеживания. Впишите абсолютный путь
3. [x] CLOUD_FOLDER - облачная директория на Яндекс Диске. По умолчанию sync_folder
4. [x] INTERVAL - промежуток времени (в секундах), через который приложение будет проверять файлы. По умолчанию 60 секунд
5. [x] LOG_FILE - название файла для логов. По умолчанию log.txt, создается в директории src

* Запустить приложение:
```sh
pip install -r requirements.txt && python src/main.py
```



