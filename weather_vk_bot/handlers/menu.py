"""Обработчики главного меню и навигации."""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import MenuCommand, get_main_keyboard
from ..services.formatter import format_main_menu
from ..services.state_manager import StateManager


def register_menu_handlers(labeler: BotLabeler, state_manager: StateManager) -> None:
    """Регистрирует обработчики возврата в главное меню и команды /start."""

    @labeler.message(payload_contains={"cmd": MenuCommand.MENU})
    @labeler.message(payload_contains={"cmd": MenuCommand.BACK})
    async def show_main_menu(message: Message) -> None:
        """Показывает главное меню по кнопкам «Назад» и «Главное меню»."""
        await state_manager.reset(message.peer_id)
        await message.answer(format_main_menu(), keyboard=get_main_keyboard())

    # Кнопка «Начать» ВКонтакте присылает payload {"command": "start"},
    # при этом текст сообщения может быть пустым.
    @labeler.message(payload_contains={"command": "start"})
    async def start_button(message: Message) -> None:
        """Показывает главное меню по кнопке «Начать»."""
        await state_manager.reset(message.peer_id)
        await message.answer(format_main_menu(), keyboard=get_main_keyboard())

    @labeler.message(text=["/start", "start", "начать", "меню"])
    async def start_command(message: Message) -> None:
        """Обрабатывает команду запуска бота, введённую текстом."""
        await state_manager.reset(message.peer_id)
        await message.answer(format_main_menu(), keyboard=get_main_keyboard())


__all__ = ("register_menu_handlers",)
