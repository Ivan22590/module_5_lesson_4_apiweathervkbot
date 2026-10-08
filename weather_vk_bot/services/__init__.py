"""Сервисы бота: состояния, оформление, доступ к погоде."""

from __future__ import annotations

from .formatter import (
    format_ask_city,
    format_ask_compare,
    format_ask_extended_city,
    format_ask_forecast_city,
    format_ask_geo,
    format_comparison,
    format_error,
    format_extended_weather,
    format_fallback,
    format_forecast,
    format_help,
    format_main_menu,
    format_weather,
)
from .state_manager import BotStates, StateManager
from .weather_service import WeatherService, WeatherServiceError

__all__ = (
    "BotStates",
    "StateManager",
    "WeatherService",
    "WeatherServiceError",
    "format_main_menu",
    "format_help",
    "format_ask_city",
    "format_ask_forecast_city",
    "format_ask_extended_city",
    "format_ask_compare",
    "format_ask_geo",
    "format_error",
    "format_fallback",
    "format_weather",
    "format_extended_weather",
    "format_forecast",
    "format_comparison",
)
