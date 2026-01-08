Как запустить

1. Подготовить переменные окружения
Создайте локальный файл `.env` на основе шаблона:

```bash
cp .env.example .env
```

Откройте `.env` и убедитесь, что значения секретов не пустые:
- `REDASH_COOKIE_SECRET`
- `REDASH_SECRET_KEY`

Пример:
.env
REDASH_COOKIE_SECRET=absolutely_not_the_cookie_secret
REDASH_SECRET_KEY=surely_not_the_secret_key

2) Запуск
```bash
docker compose up -d --build
```

Проверка статуса контейнеров:
```bash
docker compose ps
```

---

Проверка количества записей в таблице
Запустите команду дважды с паузой 10–20 секунд — число должно увеличиваться:
```bash
docker exec -it mini_app_db psql -U appuser -d appdb -c "select count(*) from weather_events;"
```

---

Redash: подключение и создание дашборда

1) Войти в Redash
Открыть
http://localhost:5000

При первом входе создайте admin-пользователя.

2) Подключить Data Source к PostgreSQL (app_db)
В Redash: Settings → Data Sources → New Data Source → PostgreSQL

Параметры (по умолчанию):
- Host: `app_db`
- Port: `5432`
- Database name: `appdb`
- User: `appuser`
- Password: `apppassword`

Нажмите Test Connection -> Create.

> Важно: внутри Docker-сети указывать `app_db`, а не `localhost`.

3) Запросы для 3 визуализаций

Визуализация 1: Температура (Line)
```sql
SELECT
  date_trunc('minute', ts) AS minute,
  avg(temperature_c) AS temperature_c
FROM weather_events
WHERE ts >= now() - interval '6 hours'
GROUP BY 1
ORDER BY 1;
```

Визуализация 2: Влажность (Line)
```sql
SELECT
  date_trunc('minute', ts) AS minute,
  avg(humidity_pct) AS humidity_pct
FROM weather_events
WHERE ts >= now() - interval '6 hours'
GROUP BY 1
ORDER BY 1;
```

Визуализация 3: Давление (Line)
```sql
SELECT
  date_trunc('minute', ts) AS minute,
  avg(pressure_hpa) AS pressure_hpa
FROM weather_events
WHERE ts >= now() - interval '24 hours'
GROUP BY 1
ORDER BY 1;
```
Jupyter Notebook (анализ)

В проекте предусмотрен анализ данных через JupyterLab.

1. Убедитесь, что сервис `jupyter` добавлен в `docker-compose.yml`, а в `.env` задан `JUPYTER_TOKEN`.
2. Запустите/пересоберите стек:
   ```bash
   docker compose up -d --build
   ```
3. Откройте JupyterLab:
   - URL: `http://localhost:8888`
   - Token: значение `JUPYTER_TOKEN` из `.env`
4. Ноутбуки примонтированы в контейнер по пути `/work`:
   - на хосте: `./notebooks`
   - в контейнере: `/work`
5. Откройте ноутбук `analysis.ipynb` и выполните ячейки по порядку. Ноутбук:
   - подключается к PostgreSQL (`app_db`),
   - читает данные из `weather_events`,
   - строит базовые агрегаты и графики.

> В контейнерном сценарии подключение к БД выполняется по хосту `app_db:5432`.






Описание


 Мини-система сбора и анализа данных: Погодная станция (PostgreSQL + Generator + Redash)

 Описание
Проект реализует простую end-to-end систему для сбора и анализа данных:
1) Генератор автоматически генерирует осмысленные показания погодной станции с заданной периодичностью и записывает их напрямую в БД.
2) PostgreSQL хранит поток событий в таблице `weather_events`.
3) Redash подключается к PostgreSQL и позволяет построить дашборд из 3+ визуализаций.
4) Jupyter используется для альтернативного анализа данных

Поля данных: температура, влажность, давление, скорость ветра, направление ветра + timestamp и station_id.


Стек
PostgreSQL 16 (контейнер `app_db`)
Python 3.11 (контейнер `generator`)
Redash (server/worker/scheduler) + Redis + PostgreSQL для метаданных Redash
Docker Compose



Структура репозитория
.
├─ docker-compose.yml
├─ .env.example
├─ db/
│  └─ init/
│     └─ 01_weather_events.sql
├─ generator/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app.py
├─ notebooks/          
└─ data/ 
