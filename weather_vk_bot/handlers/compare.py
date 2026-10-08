"""Обработчики сравнения погоды в двух городах."""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import MenuCommand, get_main_keyboard
from ..keyboards.navigation_keyboard import get_navigation_keyboard
from ..services.formatter import format_ask_compare, format_comparison, format_error
from ..services.state_manager import BotStates, StateManager
from ..services.weather_service import WeatherService, WeatherServiceError


def register_compare_handlers(
    labeler: BotLabeler,
    service: WeatherService,
    state_manager: StateManager,
) -> None:
    """Регистрирует обработчики сравнения погоды в двух городах."""

    @labeler.message(payload_contains={"cmd": MenuCommand.COMPARE})
    async def ask_compare(message: Message) -> None:
        """Запрашивает два города для сравнения."""
        await state_manager.set_state(message.peer_id, BotStates.WAITING_COMPARE_CITIES)
        await message.answer(format_ask_compare(), keyboard=get_navigation_keyboard())

    @labeler.message(state=BotStates.WAITING_COMPARE_CITIES)
    async def handle_compare(message: Message) -> None:
        """Сравнивает погоду по двум введённым городам."""
        text = (message.text or "").strip()
        if not text:
            await message.answer(
                format_error("Пустой ввод. Введите два города через запятую."),
                keyboard=get_navigation_keyboard(),
            )
            return

        try:
            city1, city2 = service.parse_cities(text)
            result = service.compare_cities(city1, city2)
        except WeatherServiceError as exc:
            await message.answer(format_error(str(exc)), keyboard=get_navigation_keyboard())
            return

        await state_manager.reset(message.peer_id)
        await message.answer(format_comparison(result), keyboard=get_main_keyboard())


__all__ = ("register_compare_handlers",)
