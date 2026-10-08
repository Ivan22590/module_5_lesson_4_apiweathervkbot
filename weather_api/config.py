"""Конфигурация модуля OpenWeatherAPI.

Здесь выполняется загрузка переменных окружения из файла .env и хранятся
константы: базовый адрес API, пути endpoint'ов, таймаут и лимит геокодирования.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from .exceptions import OpenWeatherAPIError

# Корень проекта — родительский каталог пакета weather_api
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Загружаем переменные окружения из .env в корне проекта (если файл существует)
load_dotenv(PROJECT_ROOT / ".env")

# Базовый адрес OpenWeatherMap API
BASE_URL = "https://api.openweathermap.org"

# Пути endpoint'ов (используются как константы класса OpenWeatherAPI)
CURRENT_WEATHER_PATH = "/data/2.5/weather"
FORECAST_PATH = "/data/2.5/forecast"
AIR_POLLUTION_PATH = "/data/2.5/air_pollution"
DIRECT_GEOCODING_PATH = "/geo/1.0/direct"
REVERSE_GEOCODING_PATH = "/geo/1.0/reverse"

# Таймаут HTTP-запросов в секундах
REQUEST_TIMEOUT = 10

# Максимальное число результатов геокодирования
GEOCODING_LIMIT = 5


def get_api_key() -> str:
    """Возвращает API-ключ OpenWeatherMap из переменных окружения.

    Returns:
        Значение переменной окружения ``OPEN_WEATHER_API_KEY``.

    Raises:
        OpenWeatherAPIError: если ключ не задан.
    """
    api_key = os.getenv("OPEN_WEATHER_API_KEY")
    if not api_key:
        raise OpenWeatherAPIError(
            "Не задан OPEN_WEATHER_API_KEY. Укажите ключ в .env или переменных окружения."
        )
    return api_key


__all__ = (
    "PROJECT_ROOT",
    "BASE_URL",
    "CURRENT_WEATHER_PATH",
    "FORECAST_PATH",
    "AIR_POLLUTION_PATH",
    "DIRECT_GEOCODING_PATH",
    "REVERSE_GEOCODING_PATH",
    "REQUEST_TIMEOUT",
    "GEOCODING_LIMIT",
    "get_api_key",
)
