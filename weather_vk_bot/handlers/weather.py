"""Обработчики текущей и расширенной погоды по названию города."""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import MenuCommand, get_main_keyboard
from ..keyboards.navigation_keyboard import get_navigation_keyboard
from ..services.formatter import (
    format_ask_city,
    format_ask_extended_city,
    format_error,
    format_extended_weather,
    format_weather,
)
from ..services.state_manager import BotStates, StateManager
from ..services.weather_service import WeatherService, WeatherServiceError


async def _handle_city_request(
    message: Message,
    service: WeatherService,
    state_manager: StateManager,
    extended: bool,
) -> None:
    """Общая логика обработки введённого города."""
    city = (message.text or "").strip()
    if not city:
        await message.answer(
            format_error("Пустой ввод. Введите название города."),
            keyboard=get_navigation_keyboard(),
        )
        return

    try:
        result = service.get_extended_weather(city) if extended else service.get_weather(city)
    except WeatherServiceError as exc:
        await message.answer(format_error(str(exc)), keyboard=get_navigation_keyboard())
        return

    await state_manager.reset(message.peer_id)
    text = format_extended_weather(result) if extended else format_weather(result)
    await message.answer(text, keyboard=get_main_keyboard())


def register_weather_handlers(
    labeler: BotLabeler,
    service: WeatherService,
    state_manager: StateManager,
) -> None:
    """Регистрирует обработчики текущей и расширенной погоды."""

    @labeler.message(payload_contains={"cmd": MenuCommand.WEATHER})
    async def ask_city(message: Message) -> None:
        """Запрашивает город для текущей погоды."""
        await state_manager.set_state(message.peer_id, BotStates.WAITING_CITY)
        await message.answer(format_ask_city(), keyboard=get_navigation_keyboard())

    @labeler.message(payload_contains={"cmd": MenuCommand.EXTENDED})
    async def ask_extended_city(message: Message) -> None:
        """Запрашивает город для расширенного режима."""
        await state_manager.set_state(message.peer_id, BotStates.WAITING_EXTENDED)
        await message.answer(format_ask_extended_city(), keyboard=get_navigation_keyboard())

    @labeler.message(state=BotStates.WAITING_CITY)
    async def handle_city(message: Message) -> None:
        """Обрабатывает город, введённый для текущей погоды."""
        await _handle_city_request(message, service, state_manager, extended=False)

    @labeler.message(state=BotStates.WAITING_EXTENDED)
    async def handle_extended_city(message: Message) -> None:
        """Обрабатывает город, введённый для расширенного режима."""
        await _handle_city_request(message, service, state_manager, extended=True)


__all__ = ("register_weather_handlers",)
