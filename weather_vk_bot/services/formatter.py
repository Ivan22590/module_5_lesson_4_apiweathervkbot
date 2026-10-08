"""Оформление сообщений бота.

Модуль отвечает только за представление данных: тексты меню, подсказок,
ошибок и красиво оформленные карточки погоды. Логика запросов и состояний
здесь отсутствует.
"""

from __future__ import annotations

from typing import Any, Dict, List

from weather_api.utils import format_temperature, translate_weather_description

SEPARATOR = "──────────────"


def _location_title(location: Dict[str, Any]) -> str:
    """Возвращает строку вида 'Москва, RU'."""
    name = location.get("name") or "Неизвестное место"
    country = location.get("country")
    return f"{name}, {country}" if country else name


def format_main_menu() -> str:
    """Текст главного меню."""
    return "\n".join(
        [
            "🌤 Погодный бот",
            SEPARATOR,
            "Выберите действие кнопками ниже:",
            "",
            "🌤 Погода сейчас — текущая погода в городе",
            "📅 Прогноз 5 дней — прогноз на 5 дней",
            "⚖️ Сравнить города — погода в двух городах",
            "📍 Геолокация — погода по вашему местоположению",
            "🌫 Расширенный режим — подробности и качество воздуха",
            "ℹ️ Помощь — инструкция по работе",
        ]
    )


def format_help() -> str:
    """Текст справки."""
    return "\n".join(
        [
            "ℹ️ Помощь",
            SEPARATOR,
            "Этот бот показывает погоду и качество воздуха.",
            "",
            "• «🌤 Погода сейчас» — введите название города.",
            "• «📅 Прогноз 5 дней» — прогноз на 5 дней вперёд.",
            "• «⚖️ Сравнить города» — введите два города через запятую,",
            "  например: Москва, Лондон",
            "• «📍 Геолокация» — отправьте геолокацию кнопкой",
            "  или координаты в формате: 55.7558, 37.6173",
            "• «🌫 Расширенный режим» — рассвет/закат, давление,",
            "  видимость и полный анализ воздуха.",
            "",
            "Данные предоставлены OpenWeatherMap.",
        ]
    )


def format_ask_city() -> str:
    """Подсказка о вводе города для текущей погоды."""
    return f"🌤 Введите название города:\n{SEPARATOR}"


def format_ask_forecast_city() -> str:
    """Подсказка о вводе города для прогноза."""
    return f"📅 Введите город для прогноза на 5 дней:\n{SEPARATOR}"


def format_ask_extended_city() -> str:
    """Подсказка о вводе города для расширенного режима."""
    return f"🌫 Введите город для расширенного режима:\n{SEPARATOR}"


def format_ask_compare() -> str:
    """Подсказка о вводе двух городов для сравнения."""
    return "\n".join(
        [
            "⚖️ Введите два города через запятую:",
            "например: Москва, Лондон",
            SEPARATOR,
        ]
    )


def format_ask_geo() -> str:
    """Подсказка об отправке геолокации или координат."""
    return "\n".join(
        [
            "📍 Отправьте геолокацию кнопкой ниже",
            "или координаты в формате: 55.7558, 37.6173",
            SEPARATOR,
        ]
    )


def format_error(message: str) -> str:
    """Оформляет текст ошибки для пользователя."""
    return f"⚠️ {message}"


def format_fallback() -> str:
    """Текст ответа на нераспознанное сообщение."""
    return "\n".join(
        [
            "🤔 Не понял запрос.",
            SEPARATOR,
            format_main_menu(),
        ]
    )


def format_weather(result: Dict[str, Any]) -> str:
    """Оформляет карточку текущей погоды."""
    weather = result["weather"]
    location = result["location"]
    return "\n".join(
        [
            "🌤 Погода сейчас",
            SEPARATOR,
            f"🌍 Город: {_location_title(location)}",
            f"🌡 Температура: {format_temperature(weather['temp'])} "
            f"(ощущается как {format_temperature(weather['feels_like'])})",
            f"📋 Погода: {translate_weather_description(weather['description'])}",
            f"💧 Влажность: {weather['humidity']}%",
            f"💨 Ветер: {weather['wind_speed']} м/с",
            f"☁️ Облачность: {weather['clouds']}%",
        ]
    )


def _format_pollutants(pollutants: Dict[str, Any]) -> str:
    """Формирует список загрязнителей с категориями."""
    return "\n".join(
        f"• {name}: {info['value']:.2f} ({info['category']})"
        for name, info in pollutants.items()
    )


def format_extended_weather(result: Dict[str, Any]) -> str:
    """Оформляет расширенную карточку погоды с анализом воздуха."""
    extended = result.get("extended") or {}
    air = extended.get("air_quality") or {}

    lines = [format_weather(result), SEPARATOR]

    if extended.get("pressure") is not None:
        lines.append(f"🧭 Давление: {extended['pressure']} гПа")
    if extended.get("sea_level") is not None:
        lines.append(f"🌊 На уровне моря: {extended['sea_level']} гПа")
    if extended.get("grnd_level") is not None:
        lines.append(f"⛰ На уровне земли: {extended['grnd_level']} гПа")
    if extended.get("visibility") is not None:
        lines.append(f"👁 Видимость: {extended['visibility'] / 1000:.1f} км")
    if extended.get("sunrise"):
        lines.append(f"🌅 Рассвет: {extended['sunrise']}")
    if extended.get("sunset"):
        lines.append(f"🌇 Закат: {extended['sunset']}")

    if air:
        aqi_index = air.get("aqi_index")
        suffix = f" (AQI {aqi_index})" if aqi_index is not None else ""
        lines.append(SEPARATOR)
        lines.append(f"🌫 Воздух: {air['aqi_label']}{suffix}")
        lines.append("📊 Загрязнители:")
        lines.append(_format_pollutants(air.get("pollutants", {})))
        lines.append(f"💬 {air['summary']}")

    return "\n".join(lines)


def format_forecast(result: Dict[str, Any]) -> str:
    """Оформляет прогноз на 5 дней, группируя записи по дням."""
    location = result["location"]
    entries: List[Dict[str, Any]] = result.get("forecast", [])

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        date = (entry.get("dt_txt") or "")[:10]
        grouped.setdefault(date, []).append(entry)

    day_blocks: List[str] = []
    for date, items in grouped.items():
        temps = [item["temp"] for item in items]
        block = [
            f"📆 {date}: {format_temperature(min(temps))}…{format_temperature(max(temps))}"
        ]
        for item in items:
            time_part = (item.get("dt_txt") or "")[11:16]
            description = translate_weather_description(item["description"])
            block.append(
                f"  🕒 {time_part} · {format_temperature(item['temp'])} · {description}"
            )
        day_blocks.append("\n".join(block))

    lines = [
        "📅 Прогноз на 5 дней",
        f"🌍 Город: {_location_title(location)}",
        SEPARATOR,
        f"\n{SEPARATOR}\n".join(day_blocks),
    ]

    air = (result.get("extended") or {}).get("air_quality")
    if air:
        lines.append(SEPARATOR)
        lines.append(f"🌫 Воздух: {air['aqi_label']}")
        lines.append(f"💬 {air['summary']}")

    return "\n".join(lines)


def _comparison_summary(cities: List[Dict[str, Any]]) -> List[str]:
    """Формирует вывод-сравнение по двум городам."""
    if len(cities) < 2:
        return []

    first, second = cities[0], cities[1]
    name1 = _location_title(first["location"])
    name2 = _location_title(second["location"])
    temp1 = first["weather"]["temp"]
    temp2 = second["weather"]["temp"]

    summaries: List[str] = []
    if temp1 != temp2:
        warmer = name1 if temp1 > temp2 else name2
        summaries.append(f"💬 Теплее в {warmer} на {abs(temp1 - temp2)}°C.")
    else:
        summaries.append("💬 Температура в городах одинаковая.")

    humidity1 = first["weather"].get("humidity")
    humidity2 = second["weather"].get("humidity")
    if humidity1 is not None and humidity2 is not None and humidity1 != humidity2:
        wetter = name1 if humidity1 > humidity2 else name2
        summaries.append(
            f"💬 Влажнее в {wetter} "
            f"({max(humidity1, humidity2)}% против {min(humidity1, humidity2)}%)."
        )

    return summaries


def format_comparison(result: Dict[str, Any]) -> str:
    """Оформляет сравнение погоды в двух городах."""
    cities: List[Dict[str, Any]] = result.get("cities", [])

    lines = ["⚖️ Сравнение погоды", SEPARATOR]
    for entry in cities:
        weather = entry["weather"]
        lines.append(f"🌍 {_location_title(entry['location'])}")
        lines.append(
            f"  🌡 {format_temperature(weather['temp'])} "
            f"(ощущается как {format_temperature(weather['feels_like'])})"
        )
        lines.append(f"  📋 {translate_weather_description(weather['description'])}")
        lines.append(f"  💧 Влажность: {weather['humidity']}%")
        lines.append(f"  💨 Ветер: {weather['wind_speed']} м/с")

    summary = _comparison_summary(cities)
    if summary:
        lines.append(SEPARATOR)
        lines.extend(summary)

    return "\n".join(lines)


__all__ = (
    "SEPARATOR",
    "format_main_menu",
    "format_help",
    "format_ask_city",
    "format_ask_forecast_city",
    "format_ask_extended_city",
    "format_ask_compare",
    "format_ask_geo",
    "format_error",
    "format_fallback",
    "format_weather",
    "format_extended_weather",
    "format_forecast",
    "format_comparison",
)
