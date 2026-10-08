"""Точка входа VK Weather Bot.

Запуск:
    python -m weather_vk_bot.main
    python weather_vk_bot/main.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Поддержка запуска как обычного скрипта (python weather_vk_bot/main.py)
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

from weather_api.client import OpenWeatherAPI  # noqa: E402
from weather_api.exceptions import OpenWeatherAPIError  # noqa: E402
from weather_vk_bot.bot import VKWeatherBot  # noqa: E402
from weather_vk_bot.services.weather_service import WeatherService  # noqa: E402

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Настраивает базовое логирование приложения."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    """Запускает бота. Возвращает код возврата процесса."""
    setup_logging()
    load_dotenv()

    vk_token = os.getenv("VK_BOT_TOKEN")
    if not vk_token:
        logger.error("Не задан VK_BOT_TOKEN. Добавьте токен сообщества в .env.")
        return 1

    try:
        weather_api = OpenWeatherAPI()
    except OpenWeatherAPIError as exc:
        logger.error("Ошибка конфигурации OpenWeatherAPI: %s", exc)
        return 1

    service = WeatherService(weather_api)
    bot = VKWeatherBot(vk_token, service)

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")
    finally:
        weather_api.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
