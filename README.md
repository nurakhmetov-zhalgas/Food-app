# Foodgram Project
## Реализована Backend составляющая и настройка контейнеров
### ТЗ проекта + frontend часть были взять из открытых ресурсов.

### Технологии
- Python
- Django REST framework
- Docker
- PostgreSQL

# Как запустить приложение

1) Клонируйте репозиторий
```shell
git clone https://github.com/nurakhmetov-zhalgas/Food-app.git
```
2) Поставьте виртуальное окруженин и установите зависимости
```shell
cd Food-app
python3 -m venv venv
source venv/bin/activate # в зависимости от ОС
pip install -r backend/requirements.txt
```
3) Создайте в папке infra файл .env (на примере файла .env.example)
```shell
mv infra/.env.example infra/.env
```
5) Запустите сборку контейнеров. Необходимо заранее установить docker, docker-compose
```shell
cd infra
sudo docker-compose up --build
```
Проект развернут на localhost

Чтобы получить доступ в админку необходимо создать суперпользователя
```shell
sudo docker-compose exec python manage.py cretesuperuser
```
