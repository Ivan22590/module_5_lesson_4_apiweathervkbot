"""Обработчики прогноза погоды на 5 дней."""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import MenuCommand, get_main_keyboard
from ..keyboards.navigation_keyboard import get_navigation_keyboard
from ..services.formatter import format_ask_forecast_city, format_error, format_forecast
from ..services.state_manager import BotStates, StateManager
from ..services.weather_service import WeatherService, WeatherServiceError


def register_forecast_handlers(
    labeler: BotLabeler,
    service: WeatherService,
    state_manager: StateManager,
) -> None:
    """Регистрирует обработчики прогноза на 5 дней."""

    @labeler.message(payload_contains={"cmd": MenuCommand.FORECAST})
    async def ask_forecast_city(message: Message) -> None:
        """Запрашивает город для прогноза."""
        await state_manager.set_state(message.peer_id, BotStates.WAITING_FORECAST_CITY)
        await message.answer(format_ask_forecast_city(), keyboard=get_navigation_keyboard())

    @labeler.message(state=BotStates.WAITING_FORECAST_CITY)
    async def handle_forecast_city(message: Message) -> None:
        """Обрабатывает город, введённый для прогноза."""
        city = (message.text or "").strip()
        if not city:
            await message.answer(
                format_error("Пустой ввод. Введите название города."),
                keyboard=get_navigation_keyboard(),
            )
            return

        try:
            result = service.get_forecast(city)
        except WeatherServiceError as exc:
            await message.answer(format_error(str(exc)), keyboard=get_navigation_keyboard())
            return

        await state_manager.reset(message.peer_id)
        await message.answer(format_forecast(result), keyboard=get_main_keyboard())


__all__ = ("register_forecast_handlers",)
