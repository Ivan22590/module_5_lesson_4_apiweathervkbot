"""Фасад backend-модуля OpenWeatherAPI.

Позволяет использовать привычный импорт:

    from OpenWeatherAPI import OpenWeatherAPI, CityNotFoundError
"""

from __future__ import annotations

from weather_api.client import OpenWeatherAPI
from weather_api.exceptions import (
    APIConnectionError,
    CityNotFoundError,
    OpenWeatherAPIError,
)

__all__ = (
    "OpenWeatherAPI",
    "OpenWeatherAPIError",
    "CityNotFoundError",
    "APIConnectionError",
)
