"""Класс VKWeatherBot: сборка, регистрация обработчиков и запуск Long Poll."""

from __future__ import annotations

import logging
from typing import Any

from vkbottle import BaseMiddleware, GroupEventType
from vkbottle.bot import Bot, MessageEvent

from .handlers import compare, fallback, forecast, geo, help as help_handler, menu, weather
from .keyboards.main_keyboard import MenuCommand, get_main_keyboard
from .keyboards.navigation_keyboard import get_help_keyboard
from .services.formatter import format_help, format_main_menu
from .services.state_manager import StateManager
from .services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware[Any]):
    """Логирует входящие сообщения пользователей."""

    async def pre(self) -> None:
        text = getattr(self.event, "text", "")
        peer_id = getattr(self.event, "peer_id", None)
        logger.info("Входящее сообщение peer_id=%s text=%r", peer_id, text)

    async def post(self) -> None:
        """Пост-обработка не требуется."""


class VKWeatherBot:
    """Production-ready погодный бот ВКонтакте на VKBottle.

    Args:
        token: Токен сообщества ВКонтакте.
        weather_service: Сервис доступа к погодным данным.
    """

    def __init__(self, token: str, weather_service: WeatherService) -> None:
        self.bot = Bot(token)
        self.weather_service = weather_service
        self.state_manager = StateManager(self.bot.state_dispenser)

        self._register_middleware()
        self._register_handlers()

    def _register_middleware(self) -> None:
        """Подключает middleware к представлению сообщений."""
        self.bot.labeler.message_view.register_middleware(LoggingMiddleware)

    def _register_handlers(self) -> None:
        """Регистрирует все роуты бота в порядке приоритета.

        Порядок важен: сначала меню/навигация, затем геолокация, затем
        сценарии ввода города и прогноза.
        """
        labeler = self.bot.labeler

        menu.register_menu_handlers(labeler, self.state_manager)
        geo.register_geo_handlers(labeler, self.weather_service, self.state_manager)
        weather.register_weather_handlers(labeler, self.weather_service, self.state_manager)
        forecast.register_forecast_handlers(labeler, self.weather_service, self.state_manager)
        compare.register_compare_handlers(labeler, self.weather_service, self.state_manager)
        help_handler.register_help_handlers(labeler, self.state_manager)
        # Запасной обработчик регистрируется последним: он срабатывает только
        # если ни один сценарий выше не подошёл.
        fallback.register_fallback_handler(labeler, self.state_manager)

        self._register_callback_handlers()

    def _register_callback_handlers(self) -> None:
        """Регистрирует обработчик нажатий callback-кнопок (message_event)."""

        @self.bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
        async def handle_message_event(event: MessageEvent) -> None:
            payload = event.payload or {}
            command = payload.get("cmd")

            if command == MenuCommand.HELP:
                await event.show_snackbar("Открываю помощь")
                await event.send_message(format_help(), keyboard=get_help_keyboard())
            elif command == MenuCommand.MENU:
                await event.show_snackbar("Главное меню")
                await event.send_message(format_main_menu(), keyboard=get_main_keyboard())
            else:
                await event.show_snackbar("Готово")

    def run(self) -> None:
        """Запускает бота в режиме Long Poll."""
        logger.info("Запуск VK Weather Bot (Long Poll)…")
        self.bot.run()


__all__ = ("VKWeatherBot", "LoggingMiddleware")
