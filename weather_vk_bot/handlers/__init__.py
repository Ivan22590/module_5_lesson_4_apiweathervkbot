"""Обработчики сценариев бота."""

from __future__ import annotations

from . import compare, fallback, forecast, geo, help, menu, weather

__all__ = ("menu", "weather", "forecast", "compare", "geo", "help", "fallback")
