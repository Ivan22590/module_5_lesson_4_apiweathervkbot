"""Пользовательские исключения для работы с OpenWeatherMap API."""

from __future__ import annotations


class OpenWeatherAPIError(Exception):
    """Базовое исключение для всех ошибок модуля OpenWeatherAPI."""


class CityNotFoundError(OpenWeatherAPIError):
    """Город (локация) не найден при геокодировании."""


class APIConnectionError(OpenWeatherAPIError):
    """Не удалось установить соединение с OpenWeatherMap API."""


__all__ = ("OpenWeatherAPIError", "CityNotFoundError", "APIConnectionError")
