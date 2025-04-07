Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

![Github actions](https://github.com/Tumanova-Alina/foodgram/actions/workflows/main.yml/badge.svg)

# Foodgram - проект, созданный, чтобы пользователи делились своими навыками готовки и учились у других новому.
 
 
### Описание проекта: 
________________________________________________________________________________________________________
Foodgram - сайт, на котором пользователи публикуют свои рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

### Технологии:
________________________________________________________________________________________________________
- Docker
- PostgreSQL
- Python 3.9
- Node.js
- Git 
- Nginx 
- Gunicorn 
- Django (backend) 
- React (frontend)
- Github Actions
 
### Запуск проекта: 
________________________________________________________________________________________________________
 - Клонирование репозитория:
 
    ```bash
    https://github.com/Tumanova-Alina/foodgram.git
    ```
    ```bash
    cd foodgram
    ```

 - Создание файла .env:

    ```bash
   POSTGRES_USER=логин_от_бд
   POSTGRES_PASSWORD=пароль_от_бд
   POSTGRES_DB=название_бд
   DB_HOST=название_хоста
   DB_PORT=5432
   SECRET_KEY=django_settings_secret_key
   ALLOWED_HOSTS=127.0.0.1, localhost
   DB_ENGINE=PostgreSQL_или_другая_бд
    ```

 - Создание repository secrets в GitHub Actions:

    > [!TIP]
    > Репозиторий проекта -> settings -> secrets and variables -> actions -> new repository secret

    ```
    DOCKER_USERNAME=логин в Docker Hub
    DOCKER_PASSWORD=пароль для Docker Hub
    SSH_KEY=закрытый SSH-ключ для доступа к продакшен-серверу
    SSH_PASSPHRASE=passphrase для этого ключа
    USER=username для доступа к продакшен-серверу
    HOST=адрес хоста для доступа к продакшен-серверу
    TELEGRAM_TO=ID своего телеграм-аккаунта
    TELEGRAM_TOKEN=токен telegram-бота
    ``` 

### Создание Docker-образов:
________________________________________________________________________________________________________
 - Замена username на ваш логин на DockerHub:

    ```bash
    cd frontend
    docker build -t username/foodgram_frontend .
    cd ../foodgram_backend
    docker build -t username/foodgram_backend .
    cd ../infra
    docker build -t username/foodgram_gateway . 
    ```

 - Загрузка образов на DockerHub:

    ```bash
    docker push username/foodgram_frontend
    docker push username/foodgram_backend
    docker push username/foodgram_gateway
    ```
  
### Деплой на удалённый сервер:
________________________________________________________________________________________________________
 - Подключение к удаленному серверу:

    ```bash
    ssh -i путь_до_файла_с_SSH_ключом/название_файла_с_SSH_ключом имя_пользователя@ip_адрес_сервера 
    ```

 - Создание на сервере директории foodgram через терминал:

    ```bash
    mkdir foodgram
    ```

 - Установка docker compose на сервер:

    ```bash
    sudo apt update
    sudo apt install curl
    curl -fSL https://get.docker.com -o get-docker.sh
    sudo sh ./get-docker.sh
    sudo apt-get install docker-compose-plugin
    ```

 - Копирование файлов docker-compose.production.yml и .env в директорию foodgram/ :

    ```bash
    scp -i path_to_SSH/SSH_name docker-compose.production.yml username@server_ip:/home/username/foodgram/docker-compose.production.yml
    ```

 - Запуск docker compose в режиме демона:

    ```bash
    sudo docker compose -f docker-compose.production.yml up -d
    ```

 - Выполнение миграций, сбор статики бэкенда и копирование их в /backend_static/static/:

    ```bash
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

 - Добавление ингредиентов в базу данных: Cкопируйте содержимое папки `data` на сервер. В папке есть файл ingredients.csv с ингредиентами для базы данных. Добавьте их в базу с помощью команды:

    ```bash
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_csv data/ingredients.csv recipes Ingredient
    ```

 - На сервере открытие в редакторе nano конфига nginx:

    ```bash
    sudo nano /etc/nginx/sites-enabled/default
   
    ```

 - Добавление настройки location в секции server:

    ```bash
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8080;
    }
    ```

 - Проверка работоспособности конфигураций и перезапуск Nginx:

    ```bash
    sudo nginx -t 
    sudo service nginx reload
    ```


### Некоторые примеры запросов к API:
________________________________________________________________________________________________________

- POST-запрос пользователя на регистрацию профиля:

    ```
    {
        "email": "vpupkin@yandex.ru",
        "username": "vasya.pupkin",
        "first_name": "Вася",
        "last_name": "Иванов",
        "password": "Qwerty123"
    }
    ```

    Ответ:
    ```
    {
        "email": "vpupkin@yandex.ru",
        "id": 0,
        "username": "vasya.pupkin",
        "first_name": "Вася",
        "last_name": "Иванов"
    }
    ```

- Получение списка пользователей по GET-запросу пользователя foodbloger:

    ```
    {
        "count": 123,
        "next": "http://foodgram.example.org/api/users/?page=4",
        "previous": "http://foodgram.example.org/api/users/?page=2",
        "results": [
        {}
        ]
    }
    ```

- PATCH-запрос пользователя на изменение рецепта:

    ```
    {
        "ingredients": [
        {}
        ],
        "tags": [
        1,
        2
        ],
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
        "name": "string",
        "text": "string",
        "cooking_time": 1
    }
    ```

    Ответ:
    ```
    {
        "id": 0,
        "tags": [
        {}
        ],
        "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/image.png"
        },
        "ingredients": [
        {}
        ],
        "is_favorited": true,
        "is_in_shopping_cart": true,
        "name": "string",
        "image": "http://foodgram.example.org/media/recipes/images/image.png",
        "text": "string",
        "cooking_time": 1
    }
    ```


 
### Cсылка на приложение foodgram:
________________________________________________________________________________________________________
- #### https://foodgramsite.work.gd/
________________________________________________________________________________________________________

## Автор:
+ **Алина Туманова** [Tumanova-Alina](https://github.com/Tumanova-Alina)