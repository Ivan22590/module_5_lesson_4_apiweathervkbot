"""Обработчики геолокации: VK geo-attachment и ручной ввод координат."""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import MenuCommand, get_main_keyboard
from ..keyboards.navigation_keyboard import get_geo_keyboard
from ..services.formatter import format_ask_geo, format_error, format_weather
from ..services.state_manager import BotStates, StateManager
from ..services.weather_service import WeatherService, WeatherServiceError


async def _respond_by_coordinates(
    message: Message,
    service: WeatherService,
    state_manager: StateManager,
    lat: float,
    lon: float,
) -> None:
    """Запрашивает погоду по координатам и отправляет результат."""
    try:
        result = service.get_weather_by_coordinates(lat, lon)
    except WeatherServiceError as exc:
        await message.answer(format_error(str(exc)), keyboard=get_geo_keyboard())
        return

    await state_manager.reset(message.peer_id)
    await message.answer(format_weather(result), keyboard=get_main_keyboard())


def register_geo_handlers(
    labeler: BotLabeler,
    service: WeatherService,
    state_manager: StateManager,
) -> None:
    """Регистрирует обработчики геолокации и ввода координат."""

    # Обработчик геолокации регистрируется ПЕРВЫМ: сообщение с прикреплённой
    # геолокацией может одновременно содержать payload кнопки Location,
    # поэтому его нужно перехватывать раньше обработчика кнопки «Геолокация».
    @labeler.message(func=lambda message: message.geo is not None)
    async def handle_geo_attachment(message: Message) -> None:
        """Обрабатывает сообщение с прикреплённой геолокацией VK."""
        coordinates = message.geo.coordinates
        if coordinates is None:
            await message.answer(
                format_error("Не удалось определить координаты. Отправьте их текстом."),
                keyboard=get_geo_keyboard(),
            )
            return
        await _respond_by_coordinates(
            message,
            service,
            state_manager,
            coordinates.latitude,
            coordinates.longitude,
        )

    @labeler.message(payload_contains={"cmd": MenuCommand.GEO})
    async def ask_geo(message: Message) -> None:
        """Предлагает отправить геолокацию или координаты."""
        await state_manager.set_state(message.peer_id, BotStates.WAITING_GEO)
        await message.answer(format_ask_geo(), keyboard=get_geo_keyboard())

    @labeler.message(state=BotStates.WAITING_GEO)
    async def handle_geo_text(message: Message) -> None:
        """Обрабатывает координаты, введённые текстом."""
        text = (message.text or "").strip()
        if not text:
            await message.answer(
                format_error("Пустой ввод. Отправьте координаты или геолокацию."),
                keyboard=get_geo_keyboard(),
            )
            return

        try:
            lat, lon = service.parse_coordinates(text)
        except WeatherServiceError as exc:
            await message.answer(format_error(str(exc)), keyboard=get_geo_keyboard())
            return

        await _respond_by_coordinates(message, service, state_manager, lat, lon)


__all__ = ("register_geo_handlers",)
