"""Обработчики справки."""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import MenuCommand
from ..keyboards.navigation_keyboard import get_help_keyboard
from ..services.formatter import format_help
from ..services.state_manager import StateManager


def register_help_handlers(labeler: BotLabeler, state_manager: StateManager) -> None:
    """Регистрирует обработчики справки (текст и кнопка)."""

    @labeler.message(payload_contains={"cmd": MenuCommand.HELP})
    @labeler.message(text=["/help", "help", "помощь"])
    async def show_help(message: Message) -> None:
        """Отправляет справку по работе с ботом."""
        await state_manager.reset(message.peer_id)
        await message.answer(format_help(), keyboard=get_help_keyboard())


__all__ = ("register_help_handlers",)
