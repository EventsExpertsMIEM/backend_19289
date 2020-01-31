# Experts Backend
Это репозиторий с кодом бекенд сервиса, который предоставляет пользователям:
*	Просматривать, создавать вопросы и отвечать на них;
*   Просматривать, создавать статьи;
*   Просматривать различные документы связанные с конгрессной деятельностью;
*   Зарегистрироваться, подать заявку на получения статуса эксперта и развивать конгрессное сообщество;


## Как работать в репе:
*	Создавать под фичи и задачи отдельные ветки
*	После завершения работы создавать ПР с указанием [меня](https://github.com/mvalkhimovich) для проверки
*	ПР просьба оформлять грамотно и, желательно, с указанием линки на карточку трелло (или как там оно)
*	ПР делаются в ветку dev
*	Ветка master существует для "релизных" версий

## Структура репозитория:
*	В app лежит код самого бекенда
	*	`core` - базовая логика
	*	`db` - структура и взаимодействие с бд
	*	`full` - фронт + ручки для полного сервера
	*	`rest` - рестапи
*	В doc документация и картинки
*	В extra скрипты

## Используемые технологии:
*	Основа - [Python3](https://www.python.org/)
*	СУБД - [PostgreSQL](https://www.postgresql.org/)
*	Связь с БД - [SQLAlchemy](https://www.sqlalchemy.org/)
*	Web-framework - [Flask](http://flask.pocoo.org/)
*	Web-интерфейс - Временно (а может быть и нет `¯\_(ツ)_/¯`) [Bootstrap](https://getbootstrap.com/) 

## Установка:	
*	В первую очередь ставим нужные пакеты (Ubuntu):
		
		sudo apt install git python python3 python3-pip
		pip3 install virtualenv

*	Клонинуем репозиторий и настраиваем виртуальное (опционально для продакшн-сервера) окружение (bash/zsh):

		git clone git@github.com:EventsExpertsMIEM/EventsProj.git
		cd app
		python3 -m virtualenv venv
		. venv/bin/activate
	
*	Ставим зависимости проекта:

		pip3 install -r requirements.txt

*   Настраиваем PostgreSQL:
	-	Сама [настройка](./doc/db.md)
    -   Так же можно поднять PostgreSQL в облаке (например [Heroku](https://www.heroku.com/))


## Использование

*	Сервис берёт свои настройки (БД, параметры почты и др.) через переменные окружения, поэтому рекомендуется использовать специальный скрипт (например [такой](./extra/setup.sh) - рекомендуется положить заполненный вне папки репозиторя) и инициилизировать переменные окручения через `. setup.sh`/`source setup.sh`

*	Существует два сценария использования - как полноценный сервер и как [restful api](./doc/restful_api.md). Первый вариант существует для быстрой обкатки каких-либо фич и "просто так". Второй вариант будет использоваться в продакшене.

*	Для запуска полноценного сервера необходимо указать в качестве аргумента запуска `full`, для restful api - `rest`.

*   При первом запуске необходимо указать `--create-tables password`, где первый параметр (пере)создает в БД нужные таблицы, а второй - пароль от начальной учетной записи `root_mail`

*   Запуск происходит через `python3 main.py` или же через `nohup python3 main.py > service.log &` если необходимо запустить сервис в фоне с записью логов в `service.log`
