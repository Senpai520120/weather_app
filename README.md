# Weather App

[![tests](https://github.com/Senpai520120/weather_app/actions/workflows/tests.yml/badge.svg)](https://github.com/Senpai520120/weather_app/actions/workflows/tests.yml)

A small Django app that shows the current weather for a list of cities using the
[OpenWeatherMap API](https://openweathermap.org/current). Anyone can view the list;
signed-in users can add and remove cities.

## Features

- Current temperature and weather icon for every city in the list
- Sign up, log in and log out (Django auth)
- Add a city (unknown cities are rejected) and remove it
- Clear messages instead of crashes when the API key is missing or invalid,
  a city is not found, or the weather service is unreachable
- Tests with the external API mocked, run on GitHub Actions

## Tech stack

Python 3.12, Django 6, requests, SQLite, Bootstrap 5, uv, Docker / Docker Compose.

## Quick start

You need a free OpenWeatherMap API key: <https://home.openweathermap.org/api_keys>.
Without a key the app still runs and shows a "key is not configured" message.

### Option 1: Docker

```bash
git clone https://github.com/Senpai520120/weather_app.git
cd weather_app
cp .env.example .env        # then put your key into OPENWEATHER_APPID
docker compose up --build
```

Open <http://localhost:8000>.

### Option 2: Local (pip)

```bash
git clone https://github.com/Senpai520120/weather_app.git
cd weather_app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000>.

With [uv](https://docs.astral.sh/uv/) the last steps are simply `uv sync`,
`uv run python manage.py migrate` and `uv run python manage.py runserver`.

## Configuration

Settings are read from environment variables or from a `.env` file
(see [`.env.example`](.env.example)):

| Variable | Description | Default |
| --- | --- | --- |
| `OPENWEATHER_APPID` | OpenWeatherMap API key | empty |
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DJANGO_SECRET_KEY` | Django secret key, required when `DJANGO_DEBUG` is off | dev-only key in debug mode |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names | `localhost,127.0.0.1` |
| `DJANGO_DB_PATH` | Path to the SQLite file | `db.sqlite3` |

## Running tests

```bash
python manage.py test
```

The OpenWeatherMap API is mocked, so tests need neither a key nor network access.

## Admin

```bash
python manage.py createsuperuser
# Docker: docker compose exec web uv run python manage.py createsuperuser
```

The admin is available at <http://127.0.0.1:8000/admin/>.

## Project structure

```
tmpr/      Django project settings and root URLs
weather/   app: City model, views, forms, templates, tests
```
