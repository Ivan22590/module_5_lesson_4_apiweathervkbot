"""Связующее звено между VKBottle и OpenWeatherAPI.

Сервис инкапсулирует обращения к backend-модулю, парсинг координат и
преобразование технических исключений в понятные пользователю сообщения.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, Tuple

from weather_api.client import OpenWeatherAPI
from weather_api.exceptions import APIConnectionError, CityNotFoundError, OpenWeatherAPIError
from weather_api.utils import parse_coordinates

# Разделители для ввода двух городов: "Москва, Лондон", "Москва и Лондон",
# "Москва vs Лондон", "Москва / Лондон".
_CITY_SPLIT_RE = re.compile(r"\s*(?:,|/|\bи\b|\bvs\b|\bпротив\b)\s*", re.IGNORECASE)


class WeatherServiceError(Exception):
    """Ошибка уровня сервиса с готовым для пользователя сообщением."""


class WeatherService:
    """Высокоуровневый сервис погоды для бота."""

    def __init__(self, api: OpenWeatherAPI) -> None:
        self._api = api

    def get_weather(self, city: str) -> Dict[str, Any]:
        """Текущая погода по названию города."""
        return self._call(lambda: self._api.get_weather_by_city(city), city=city)

    def get_extended_weather(self, city: str) -> Dict[str, Any]:
        """Расширенная погода по названию города."""
        return self._call(lambda: self._api.get_weather_by_city(city, extended=True), city=city)

    def get_forecast(self, city: str) -> Dict[str, Any]:
        """Прогноз на 5 дней по названию города."""
        return self._call(lambda: self._api.get_forecast_by_city(city), city=city)

    def compare_cities(self, city1: str, city2: str) -> Dict[str, Any]:
        """Сравнивает погоду в двух городах."""
        try:
            return self._api.compare_weather_by_cities(city1, city2)
        except CityNotFoundError as exc:
            raise WeatherServiceError(
                f"{exc}. Проверьте названия обоих городов."
            ) from exc
        except APIConnectionError as exc:
            raise WeatherServiceError(
                "Сервис погоды недоступен. Проверьте соединение и попробуйте позже."
            ) from exc
        except OpenWeatherAPIError as exc:
            raise WeatherServiceError(
                "Не удалось получить данные о погоде. Попробуйте позже."
            ) from exc

    @staticmethod
    def parse_cities(text: str) -> Tuple[str, str]:
        """Разбирает строку с двумя городами.

        Raises:
            WeatherServiceError: если не удалось выделить два города.
        """
        if not text or not text.strip():
            raise WeatherServiceError("Пустой ввод. Введите два города.")

        parts = [part.strip() for part in _CITY_SPLIT_RE.split(text) if part.strip()]
        if len(parts) < 2:
            raise WeatherServiceError(
                "Нужно два города. Пример: Москва, Лондон"
            )
        return parts[0], parts[1]

    def get_weather_by_coordinates(
        self,
        lat: float,
        lon: float,
        extended: bool = False,
    ) -> Dict[str, Any]:
        """Текущая погода по координатам."""
        return self._call(
            lambda: self._api.get_weather_by_coordinates(lat, lon, extended=extended)
        )

    @staticmethod
    def parse_coordinates(text: str) -> Tuple[float, float]:
        """Разбирает координаты из строки.

        Raises:
            WeatherServiceError: если координаты некорректны.
        """
        try:
            return parse_coordinates(text)
        except ValueError as exc:
            raise WeatherServiceError(
                "Не удалось распознать координаты. "
                "Отправьте их в формате: 55.7558, 37.6173"
            ) from exc

    @staticmethod
    def _call(func: Callable[[], Dict[str, Any]], city: Optional[str] = None) -> Dict[str, Any]:
        """Выполняет запрос, переводя исключения backend в WeatherServiceError."""
        try:
            return func()
        except CityNotFoundError as exc:
            if city:
                raise WeatherServiceError(
                    f"Город «{city}» не найден. Проверьте название и попробуйте снова."
                ) from exc
            raise WeatherServiceError(
                "Локация не найдена. Проверьте координаты и попробуйте снова."
            ) from exc
        except APIConnectionError as exc:
            raise WeatherServiceError(
                "Сервис погоды недоступен. Проверьте соединение и попробуйте позже."
            ) from exc
        except OpenWeatherAPIError as exc:
            raise WeatherServiceError(
                "Не удалось получить данные о погоде. Попробуйте позже."
            ) from exc


__all__ = ("WeatherService", "WeatherServiceError")
