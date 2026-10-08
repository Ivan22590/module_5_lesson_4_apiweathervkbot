"""Пакет weather_api — backend для работы с OpenWeatherMap API."""

from __future__ import annotations

from .client import OpenWeatherAPI
from .exceptions import APIConnectionError, CityNotFoundError, OpenWeatherAPIError

__all__ = (
    "OpenWeatherAPI",
    "OpenWeatherAPIError",
    "CityNotFoundError",
    "APIConnectionError",
)
