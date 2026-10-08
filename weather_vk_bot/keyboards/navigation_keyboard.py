"""Навигационные клавиатуры: возврат назад, главное меню, геолокация, помощь."""

from __future__ import annotations

from vkbottle import Callback, Keyboard, KeyboardButtonColor, Location, OpenLink, Text

from .main_keyboard import MenuCommand, make_payload

# Ссылка на источник данных (используется в кнопке OpenLink)
OPENWEATHER_URL = "https://openweathermap.org/"


def _navigation_row(keyboard: Keyboard) -> Keyboard:
    """Добавляет стандартный ряд навигации: «Назад» и «Главное меню»."""
    return (
        keyboard.row()
        .add(
            Text("⬅️ Назад", payload=make_payload(MenuCommand.BACK)),
            color=KeyboardButtonColor.SECONDARY,
        )
        .add(
            Text("🏠 Главное меню", payload=make_payload(MenuCommand.MENU)),
            color=KeyboardButtonColor.POSITIVE,
        )
    )


def get_navigation_keyboard() -> str:
    """Клавиатура с навигацией (используется при вводе города)."""
    keyboard = Keyboard(one_time=False, inline=False)
    return _navigation_row(keyboard).get_json()


def get_geo_keyboard() -> str:
    """Клавиатура с кнопкой геолокации и навигацией.

    У кнопки Location намеренно нет payload: VK прикладывает payload кнопки
    к сообщению с геолокацией, что мешало бы её обработке.
    """
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Location(), color=KeyboardButtonColor.PRIMARY)
    return _navigation_row(keyboard).get_json()


def get_help_keyboard() -> str:
    """Inline-клавиатура для сообщения помощи (OpenLink + возврат в меню)."""
    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(OpenLink(OPENWEATHER_URL, "🌐 openweathermap.org"), color=KeyboardButtonColor.SECONDARY)
        .row()
        .add(
            Callback("🏠 В главное меню", payload=make_payload(MenuCommand.MENU)),
            color=KeyboardButtonColor.POSITIVE,
        )
    )
    return keyboard.get_json()


__all__ = (
    "OPENWEATHER_URL",
    "get_navigation_keyboard",
    "get_geo_keyboard",
    "get_help_keyboard",
)
