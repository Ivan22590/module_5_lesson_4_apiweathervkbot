"""Клавиатура главного меню и идентификаторы команд бота."""

from __future__ import annotations

from typing import Any, Dict

from vkbottle import Callback, Keyboard, KeyboardButtonColor, Text


class MenuCommand:
    """Идентификаторы действий кнопок (передаются в payload)."""

    WEATHER = "weather"
    FORECAST = "forecast"
    COMPARE = "compare"
    GEO = "geo"
    EXTENDED = "extended"
    HELP = "help"
    MENU = "menu"
    BACK = "back"


def make_payload(command: str) -> Dict[str, str]:
    """Формирует payload кнопки по идентификатору команды."""
    return {"cmd": command}


def get_main_keyboard() -> str:
    """Возвращает JSON главной клавиатуры (постоянная, не inline).

    Кнопки:
        🌤 Погода сейчас, 📅 Прогноз 5 дней, ⚖️ Сравнить города,
        📍 Геолокация, 🌫 Расширенный режим, ℹ️ Помощь.
    """
    keyboard = (
        Keyboard(one_time=False, inline=False)
        .add(
            Text("🌤 Погода сейчас", payload=make_payload(MenuCommand.WEATHER)),
            color=KeyboardButtonColor.PRIMARY,
        )
        .add(
            Text("📅 Прогноз 5 дней", payload=make_payload(MenuCommand.FORECAST)),
            color=KeyboardButtonColor.PRIMARY,
        )
        .row()
        .add(
            Text("⚖️ Сравнить города", payload=make_payload(MenuCommand.COMPARE)),
            color=KeyboardButtonColor.PRIMARY,
        )
        .add(
            Text("📍 Геолокация", payload=make_payload(MenuCommand.GEO)),
            color=KeyboardButtonColor.SECONDARY,
        )
        .row()
        .add(
            Text("🌫 Расширенный режим", payload=make_payload(MenuCommand.EXTENDED)),
            color=KeyboardButtonColor.SECONDARY,
        )
        .add(
            Callback("ℹ️ Помощь", payload=make_payload(MenuCommand.HELP)),
            color=KeyboardButtonColor.SECONDARY,
        )
    )
    return keyboard.get_json()


__all__ = ("MenuCommand", "make_payload", "get_main_keyboard")
