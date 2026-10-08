"""Управление FSM-состояниями диалога бота."""

from __future__ import annotations

from typing import Optional

from vkbottle import ABCStateDispenser, BaseStateGroup


class BotStates(BaseStateGroup):
    """Состояния диалога с пользователем."""

    MAIN_MENU = "main_menu"
    WAITING_CITY = "waiting_city"
    WAITING_FORECAST_CITY = "waiting_forecast_city"
    WAITING_COMPARE_CITIES = "waiting_compare_cities"
    WAITING_GEO = "waiting_geo"
    WAITING_EXTENDED = "waiting_extended"


class StateManager:
    """Обёртка над StateDispenser VKBottle.

    Инкапсулирует работу с состояниями, чтобы обработчики не зависели
    от конкретной реализации диспенсера.
    """

    def __init__(self, dispenser: ABCStateDispenser) -> None:
        self._dispenser = dispenser

    async def set_state(self, peer_id: int, state: BotStates) -> None:
        """Устанавливает состояние для пользователя/диалога."""
        await self._dispenser.set(peer_id, state)

    async def reset(self, peer_id: int) -> None:
        """Сбрасывает состояние (возврат в главное меню)."""
        await self._dispenser.delete(peer_id)

    async def get_state(self, peer_id: int) -> Optional[str]:
        """Возвращает текущее состояние или ``None``."""
        peer = await self._dispenser.get(peer_id)
        return peer.state if peer else None


__all__ = ("BotStates", "StateManager")
