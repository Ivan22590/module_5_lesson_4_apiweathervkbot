"""Точка входа для запуска OpenWeatherAPI из консоли.

Примеры:

    python -m weather_api.cli --city Moscow
    python -m weather_api.cli --city Moscow --extended
    python -m weather_api.cli --city Moscow --forecast
    python -m weather_api.cli --coords "55.7558, 37.6173" --extended
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from .client import OpenWeatherAPI
from .exceptions import APIConnectionError, CityNotFoundError, OpenWeatherAPIError
from .utils import parse_coordinates


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="weather_api",
        description="Получение погоды и качества воздуха через OpenWeatherMap API.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-c", "--city", help="Название города (например, Moscow)")
    source.add_argument("--coords", help="Координаты в формате '55.7558, 37.6173'")
    source.add_argument(
        "--compare",
        nargs=2,
        metavar=("CITY1", "CITY2"),
        help="Сравнить погоду в двух городах",
    )

    parser.add_argument(
        "-f",
        "--forecast",
        action="store_true",
        help="Показать прогноз на 5 дней (только для города)",
    )
    parser.add_argument(
        "-e",
        "--extended",
        action="store_true",
        help="Расширенный режим: рассвет/закат, давление, видимость, анализ воздуха",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа CLI. Возвращает код возврата процесса."""
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        with OpenWeatherAPI() as api:
            if args.compare:
                result = api.compare_weather_by_cities(args.compare[0], args.compare[1])
            elif args.coords:
                if args.forecast:
                    print("Прогноз по координатам не поддерживается. Укажите город через --city.")
                    return 2
                lat, lon = parse_coordinates(args.coords)
                result = api.get_weather_by_coordinates(lat, lon, extended=args.extended)
            elif args.forecast:
                result = api.get_forecast_by_city(args.city, extended=args.extended)
            else:
                result = api.get_weather_by_city(args.city, extended=args.extended)

            print(result["formatted"])
    except CityNotFoundError as exc:
        print(f"Город не найден: {exc}")
        return 1
    except APIConnectionError as exc:
        print(f"Ошибка соединения: {exc}")
        return 1
    except OpenWeatherAPIError as exc:
        print(f"Ошибка OpenWeatherAPI: {exc}")
        return 1
    except ValueError as exc:
        print(f"Некорректные данные: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
