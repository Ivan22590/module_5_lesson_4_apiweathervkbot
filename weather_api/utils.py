"""Вспомогательные функции модуля OpenWeatherAPI."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Tuple

# Регулярное выражение для извлечения чисел (в том числе координат) из строки
_COORDINATES_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")

# Перевод погодных условий OpenWeatherMap на русский язык.
# Ключи соответствуют полю weather[].description в ответах API.
WEATHER_DESCRIPTIONS_RU = {
    # Ясно / облачность
    "clear sky": "ясно",
    "few clouds": "малооблачно",
    "scattered clouds": "рассеянные облака",
    "broken clouds": "облачно с прояснениями",
    "overcast clouds": "пасмурно",
    # Атмосферные явления
    "mist": "дымка",
    "smoke": "дым",
    "haze": "мгла",
    "sand/dust whirls": "пыльные вихри",
    "fog": "туман",
    "sand": "песчаная буря",
    "dust": "пыль",
    "volcanic ash": "вулканический пепел",
    "squalls": "шквал",
    "tornado": "торнадо",
    # Морось
    "light intensity drizzle": "небольшая морось",
    "drizzle": "морось",
    "heavy intensity drizzle": "сильная морось",
    "light intensity drizzle rain": "небольшой дождь с моросью",
    "drizzle rain": "дождь с моросью",
    "heavy intensity drizzle rain": "сильный дождь с моросью",
    "shower rain and drizzle": "ливень с моросью",
    "heavy shower rain and drizzle": "сильный ливень с моросью",
    "shower drizzle": "морось",
    # Дождь
    "light rain": "небольшой дождь",
    "moderate rain": "умеренный дождь",
    "heavy intensity rain": "сильный дождь",
    "very heavy rain": "очень сильный дождь",
    "extreme rain": "экстремальный дождь",
    "freezing rain": "ледяной дождь",
    "light intensity shower rain": "небольшой ливень",
    "shower rain": "ливень",
    "heavy intensity shower rain": "сильный ливень",
    "ragged shower rain": "прерывистый ливень",
    # Снег
    "light snow": "небольшой снег",
    "snow": "снег",
    "heavy snow": "сильный снег",
    "sleet": "дождь со снегом",
    "light shower sleet": "небольшой дождь со снегом",
    "shower sleet": "дождь со снегом",
    "light rain and snow": "небольшой дождь со снегом",
    "rain and snow": "дождь со снегом",
    "light shower snow": "небольшой снегопад",
    "shower snow": "снегопад",
    "heavy shower snow": "сильный снегопад",
    # Гроза
    "thunderstorm with light rain": "гроза с небольшим дождём",
    "thunderstorm with rain": "гроза с дождём",
    "thunderstorm with heavy rain": "гроза с сильным дождём",
    "light thunderstorm": "слабая гроза",
    "thunderstorm": "гроза",
    "heavy thunderstorm": "сильная гроза",
    "ragged thunderstorm": "прерывистая гроза",
    "thunderstorm with light drizzle": "гроза с небольшой моросью",
    "thunderstorm with drizzle": "гроза с моросью",
    "thunderstorm with heavy drizzle": "гроза с сильной моросью",
}


def translate_weather_description(description: str) -> str:
    """Переводит описание погодного условия с английского на русский.

    Если перевод не найден, возвращает исходную строку.
    """
    if not description:
        return ""
    return WEATHER_DESCRIPTIONS_RU.get(description.strip().lower(), description)


def kelvin_to_celsius(kelvin: float) -> float:
    """Переводит температуру из Кельвинов в градусы Цельсия."""
    return kelvin - 273.15


def round_temperature(celsius: float) -> int:
    """Округляет температуру до целого числа градусов."""
    return int(round(celsius))


def format_temperature(celsius: float) -> str:
    """Форматирует температуру в человекочитаемый вид, например '+21°C'."""
    rounded = round_temperature(celsius)
    sign = "+" if rounded > 0 else ""
    return f"{sign}{rounded}°C"


def timestamp_to_time(timestamp: int, tz_offset: int = 0) -> str:
    """Преобразует Unix-timestamp в строку времени вида 'HH:MM'.

    Args:
        timestamp: Unix-время в секундах.
        tz_offset: Смещение часового пояса локации в секундах.
    """
    tz = timezone(timedelta(seconds=tz_offset))
    return datetime.fromtimestamp(timestamp, tz=tz).strftime("%H:%M")


def validate_coordinates(lat: float, lon: float) -> None:
    """Проверяет корректность широты и долготы.

    Raises:
        ValueError: если координаты выходят за допустимые диапазоны.
    """
    if not -90.0 <= lat <= 90.0:
        raise ValueError(f"Широта вне диапазона [-90, 90]: {lat}")
    if not -180.0 <= lon <= 180.0:
        raise ValueError(f"Долгота вне диапазона [-180, 180]: {lon}")


def parse_coordinates(text: str) -> Tuple[float, float]:
    """Извлекает широту и долготу из строки.

    Поддерживаются форматы '55.7558,37.6173' и '55.7558 37.6173'.

    Args:
        text: Строка с координатами.

    Returns:
        Кортеж (широта, долгота).

    Raises:
        ValueError: если координаты не распознаны или некорректны.
    """
    if not text or not text.strip():
        raise ValueError("Пустая строка координат.")

    matches = _COORDINATES_RE.findall(text)
    if len(matches) < 2:
        raise ValueError("Не удалось распознать координаты. Ожидается формат: 55.7558, 37.6173")

    lat = float(matches[0].replace(",", "."))
    lon = float(matches[1].replace(",", "."))

    validate_coordinates(lat, lon)
    return lat, lon


__all__ = (
    "kelvin_to_celsius",
    "round_temperature",
    "format_temperature",
    "timestamp_to_time",
    "validate_coordinates",
    "parse_coordinates",
    "translate_weather_description",
    "WEATHER_DESCRIPTIONS_RU",
)
