"""Запасной обработчик для сообщений, не совпавших ни с одним сценарием.

Гарантирует, что бот всегда отвечает пользователю и показывает клавиатуру,
даже если тот ввёл произвольный текст без предварительного выбора действия.
Регистрируется последним, поэтому срабатывает только если ни один другой
обработчик не подошёл.
"""

from __future__ import annotations

from vkbottle.bot import BotLabeler, Message

from ..keyboards.main_keyboard import get_main_keyboard
from ..services.formatter import format_fallback
from ..services.state_manager import StateManager


def register_fallback_handler(labeler: BotLabeler, state_manager: StateManager) -> None:
    """Регистрирует обработчик по умолчанию для нераспознанных сообщений."""

    @labeler.message()
    async def fallback(message: Message) -> None:
        """Отвечает подсказкой и главным меню на любое нераспознанное сообщение."""
        await state_manager.reset(message.peer_id)
        await message.answer(format_fallback(), keyboard=get_main_keyboard())


__all__ = ("register_fallback_handler",)
