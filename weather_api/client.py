"""Основной клиент OpenWeatherAPI.

Класс :class:`OpenWeatherAPI` объединяет все актуальные endpoint'ы
OpenWeatherMap (текущая погода, прогноз на 5 дней, качество воздуха,
прямое и обратное геокодирование) и предоставляет удобные публичные методы,
возвращающие как структурированные данные, так и готовый текст для вывода.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from .config import (
    AIR_POLLUTION_PATH as DEFAULT_AIR_POLLUTION_PATH,
    BASE_URL as DEFAULT_BASE_URL,
    CURRENT_WEATHER_PATH as DEFAULT_CURRENT_WEATHER_PATH,
    DIRECT_GEOCODING_PATH as DEFAULT_DIRECT_GEOCODING_PATH,
    FORECAST_PATH as DEFAULT_FORECAST_PATH,
    GEOCODING_LIMIT,
    REVERSE_GEOCODING_PATH as DEFAULT_REVERSE_GEOCODING_PATH,
    REQUEST_TIMEOUT,
    get_api_key,
)
from .exceptions import APIConnectionError, CityNotFoundError, OpenWeatherAPIError
from .utils import (
    format_temperature,
    kelvin_to_celsius,
    round_temperature,
    timestamp_to_time,
    translate_weather_description,
    validate_coordinates,
)

logger = logging.getLogger(__name__)

# Разделитель, используемый при оформлении текстовых ответов
SEPARATOR = "──────────────"


class OpenWeatherAPI:
    """Клиент для работы с OpenWeatherMap API.

    Args:
        api_key: API-ключ OpenWeatherMap. Если не передан, берётся из окружения.
        timeout: Таймаут HTTP-запросов в секундах.
        session: Готовая :class:`requests.Session` (удобно для тестов и переиспользования).

    Example:
        >>> api = OpenWeatherAPI()
        >>> api.get_weather_by_city("Moscow")["formatted"]  # doctest: +SKIP
    """

    # --- Константы endpoint'ов (актуальный OpenWeatherMap API) ---
    BASE_URL: str = DEFAULT_BASE_URL
    CURRENT_WEATHER_PATH: str = DEFAULT_CURRENT_WEATHER_PATH
    FORECAST_PATH: str = DEFAULT_FORECAST_PATH
    AIR_POLLUTION_PATH: str = DEFAULT_AIR_POLLUTION_PATH
    DIRECT_GEOCODING_PATH: str = DEFAULT_DIRECT_GEOCODING_PATH
    REVERSE_GEOCODING_PATH: str = DEFAULT_REVERSE_GEOCODING_PATH

    # Заготовки для будущего расширения (UV Index, Historical API, Alerts):
    # UV_INDEX_PATH: str = "/data/2.5/uvi"
    # HISTORICAL_PATH: str = "/data/3.0/onecall/timemachine"
    # ALERTS_PATH: str = "/data/3.0/onecall"

    # Заголовки запросов. Явное закрытие соединения повышает надёжность
    # на сетях и через прокси, где переиспользование keep-alive соединения
    # к OpenWeatherMap может приводить к зависанию запросов.
    REQUEST_HEADERS: Dict[str, str] = {"Connection": "close"}

    # --- Шкала качества воздуха ---
    POLLUTANT_NAMES: Dict[str, str] = {
        "so2": "SO2",
        "no2": "NO2",
        "pm10": "PM10",
        "pm2_5": "PM2.5",
        "o3": "O3",
        "co": "CO",
    }

    # Верхние (исключающие) границы категорий для каждого загрязнителя
    AIR_QUALITY_THRESHOLDS: Dict[str, Tuple[Tuple[float, str], ...]] = {
        "so2": ((20, "Good"), (80, "Fair"), (250, "Moderate"), (350, "Poor")),
        "no2": ((40, "Good"), (70, "Fair"), (150, "Moderate"), (200, "Poor")),
        "pm10": ((20, "Good"), (50, "Fair"), (100, "Moderate"), (200, "Poor")),
        "pm2_5": ((10, "Good"), (25, "Fair"), (50, "Moderate"), (75, "Poor")),
        "o3": ((60, "Good"), (100, "Fair"), (140, "Moderate"), (180, "Poor")),
        "co": ((4400, "Good"), (9400, "Fair"), (12400, "Moderate"), (15400, "Poor")),
    }

    # Порядок категорий от лучшей к худшей
    AQI_ORDER: Tuple[str, ...] = ("Good", "Fair", "Moderate", "Poor", "Very Poor")

    # Человекочитаемые описания категорий (текст на русском)
    AQI_SUMMARIES: Dict[str, str] = {
        "Good": "Качество воздуха: Good. Все основные загрязнители в пределах нормы.",
        "Fair": "Качество воздуха: Fair. Незначительно повышен уровень загрязнителей.",
        "Moderate": "Качество воздуха: Moderate. Отдельные загрязнители превышают идеальные значения.",
        "Poor": "Качество воздуха: Poor. Чувствительным группам стоит сократить активность на улице.",
        "Very Poor": "Качество воздуха: Very Poor. Высокий риск для здоровья.",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key: str = api_key or get_api_key()
        self.timeout: int = timeout
        self.session: requests.Session = session or requests.Session()
        self.geocoding_limit: int = GEOCODING_LIMIT

    # ------------------------------------------------------------------ #
    # Служебные методы
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        """Закрывает HTTP-сессию."""
        self.session.close()

    def __enter__(self) -> "OpenWeatherAPI":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def _make_request(self, path: str, params: Dict[str, Any]) -> Any:
        """Выполняет GET-запрос к OpenWeatherMap и возвращает распарсенный JSON.

        Args:
            path: Путь endpoint'а (например, ``/data/2.5/weather``).
            params: Query-параметры запроса (без ``appid`` — он добавляется сам).

        Returns:
            Результат ``response.json()``.

        Raises:
            APIConnectionError: при сетевых ошибках.
            OpenWeatherAPIError: при некорректном ответе сервера.
        """
        url = f"{self.BASE_URL}{path}"
        query = dict(params)
        query["appid"] = self.api_key

        safe_params = {k: v for k, v in query.items() if k != "appid"}
        logger.debug("GET %s params=%s", url, safe_params)

        try:
            response = self.session.get(
                url,
                params=query,
                timeout=self.timeout,
                headers=self.REQUEST_HEADERS,
            )
        except requests.exceptions.RequestException as exc:
            raise APIConnectionError(f"Не удалось соединиться с OpenWeatherMap: {exc}") from exc

        if response.status_code == 401:
            raise OpenWeatherAPIError("Неверный API-ключ OpenWeatherMap (401).")
        if response.status_code == 404:
            raise OpenWeatherAPIError("Запрашиваемые данные не найдены (404).")
        if response.status_code == 429:
            raise OpenWeatherAPIError("Превышен лимит запросов к OpenWeatherMap (429).")
        if response.status_code != 200:
            raise OpenWeatherAPIError(f"OpenWeatherMap вернул статус {response.status_code}.")

        try:
            return response.json()
        except ValueError as exc:
            raise OpenWeatherAPIError("Некорректный JSON в ответе OpenWeatherMap.") from exc

    # ------------------------------------------------------------------ #
    # Внутренние методы по endpoint'ам
    # ------------------------------------------------------------------ #
    def _direct_geocode(self, city: str) -> List[Dict[str, Any]]:
        """Прямое геокодирование: название города -> список координат."""
        params = {"q": city, "limit": self.geocoding_limit}
        return self._make_request(self.DIRECT_GEOCODING_PATH, params)

    def _reverse_geocode(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        """Обратное геокодирование: координаты -> список названий локаций."""
        params = {"lat": lat, "lon": lon, "limit": self.geocoding_limit}
        return self._make_request(self.REVERSE_GEOCODING_PATH, params)

    def _current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Текущая погода по координатам."""
        return self._make_request(self.CURRENT_WEATHER_PATH, {"lat": lat, "lon": lon})

    def _forecast_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Прогноз на 5 дней по координатам."""
        return self._make_request(self.FORECAST_PATH, {"lat": lat, "lon": lon})

    def _air_pollution(self, lat: float, lon: float) -> Dict[str, Any]:
        """Данные о загрязнении воздуха по координатам."""
        return self._make_request(self.AIR_POLLUTION_PATH, {"lat": lat, "lon": lon})

    # ------------------------------------------------------------------ #
    # Аналитика качества воздуха
    # ------------------------------------------------------------------ #
    def _pollutant_category(self, key: str, value: float) -> str:
        """Определяет категорию загрязнителя по заданной шкале."""
        for upper_bound, label in self.AIR_QUALITY_THRESHOLDS[key]:
            if value < upper_bound:
                return label
        return "Very Poor"

    @staticmethod
    def _format_pollutants(pollutants: Dict[str, Dict[str, Any]]) -> str:
        """Формирует построчный список загрязнителей с их категориями."""
        return "\n".join(
            f"• {name}: {info['value']:.2f} ({info['category']})"
            for name, info in pollutants.items()
        )

    def _build_air_summary(self, label: str, exceeded: List[str]) -> str:
        """Собирает человекочитаемый итог по качеству воздуха."""
        summary = self.AQI_SUMMARIES[label]
        if label != "Good" and exceeded:
            summary += f" Повышенные загрязнители: {', '.join(exceeded)}."
        return summary

    def _analyze_air_quality(self, air_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует данные о загрязнении воздуха.

        Args:
            air_data: Сырой ответ endpoint'а ``air_pollution``.

        Returns:
            Словарь с ключами ``aqi_index``, ``aqi_label``, ``pollutants``,
            ``exceeded_pollutants``, ``summary`` и ``details``.

        Raises:
            OpenWeatherAPIError: если ответ не содержит данных.
        """
        entries = air_data.get("list") or []
        if not entries:
            raise OpenWeatherAPIError("Пустой ответ air_pollution.")

        entry = entries[0]
        aqi_index = entry.get("main", {}).get("aqi")
        components = entry.get("components", {})

        pollutants: Dict[str, Dict[str, Any]] = {}
        exceeded: List[str] = []
        worst_index = 0

        for key, display_name in self.POLLUTANT_NAMES.items():
            raw_value = components.get(key)
            if raw_value is None:
                continue

            value = float(raw_value)
            category = self._pollutant_category(key, value)
            worst_index = max(worst_index, self.AQI_ORDER.index(category))

            is_exceeded = category != "Good"
            pollutants[display_name] = {
                "value": value,
                "category": category,
                "exceeded": is_exceeded,
            }
            if is_exceeded:
                exceeded.append(display_name)

        aqi_label = self.AQI_ORDER[worst_index]

        return {
            "aqi_index": aqi_index,
            "aqi_label": aqi_label,
            "pollutants": pollutants,
            "exceeded_pollutants": exceeded,
            "summary": self._build_air_summary(aqi_label, exceeded),
            "details": self._format_pollutants(pollutants),
        }

    # ------------------------------------------------------------------ #
    # Извлечение и форматирование данных
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_location(
        place: Dict[str, Any],
        lat: float,
        lon: float,
        current: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Формирует описание локации из результата геокодирования."""
        current = current or {}
        sys_data = current.get("sys", {})
        name = place.get("name") or current.get("name") or "Неизвестное место"
        return {
            "name": name,
            "country": place.get("country") or sys_data.get("country"),
            "state": place.get("state"),
            "lat": lat,
            "lon": lon,
        }

    @staticmethod
    def _location_title(location: Dict[str, Any]) -> str:
        """Возвращает строку вида 'Москва, RU'."""
        name = location.get("name") or "Неизвестное место"
        country = location.get("country")
        return f"{name}, {country}" if country else name

    def _extract_weather_fields(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает основные поля текущей погоды."""
        main = current.get("main", {})
        wind = current.get("wind", {})
        weather_list = current.get("weather") or [{}]
        weather = weather_list[0]
        clouds = current.get("clouds", {})

        return {
            "description": weather.get("description", ""),
            "main": weather.get("main", ""),
            "temp": round_temperature(kelvin_to_celsius(main.get("temp", 0.0))),
            "feels_like": round_temperature(kelvin_to_celsius(main.get("feels_like", 0.0))),
            "temp_min": round_temperature(kelvin_to_celsius(main.get("temp_min", 0.0))),
            "temp_max": round_temperature(kelvin_to_celsius(main.get("temp_max", 0.0))),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "wind_speed": wind.get("speed"),
            "clouds": clouds.get("all"),
        }

    def _extract_extended_fields(
        self,
        current: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Извлекает расширенные поля (рассвет, закат, давление, видимость)."""
        main = current.get("main", {})
        sys_data = current.get("sys", {})
        tz_offset = current.get("timezone", 0)

        sunrise = sys_data.get("sunrise")
        sunset = sys_data.get("sunset")

        return {
            "pressure": main.get("pressure"),
            "sea_level": main.get("sea_level"),
            "grnd_level": main.get("grnd_level"),
            "visibility": current.get("visibility"),
            "sunrise": timestamp_to_time(sunrise, tz_offset) if sunrise else None,
            "sunset": timestamp_to_time(sunset, tz_offset) if sunset else None,
        }

    def _extract_forecast_entries(self, forecast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Преобразует список прогноза в удобные записи."""
        entries: List[Dict[str, Any]] = []
        for item in forecast_data.get("list", []):
            main = item.get("main", {})
            weather_list = item.get("weather") or [{}]
            weather = weather_list[0]
            entries.append(
                {
                    "dt_txt": item.get("dt_txt"),
                    "temp": round_temperature(kelvin_to_celsius(main.get("temp", 0.0))),
                    "humidity": main.get("humidity"),
                    "pressure": main.get("pressure"),
                    "description": weather.get("description", ""),
                    "clouds": item.get("clouds", {}).get("all"),
                    "wind_speed": item.get("wind", {}).get("speed"),
                    "pop": item.get("pop"),
                }
            )
        return entries

    def _format_basic_weather(self, fields: Dict[str, Any], location: Dict[str, Any]) -> str:
        """Форматирует базовую погоду в человекочитаемый текст."""
        lines = [
            f"🌍 Город: {self._location_title(location)}",
            f"🌡 Температура: {format_temperature(fields['temp'])} "
            f"(ощущается как {format_temperature(fields['feels_like'])})",
            f"📋 Погода: {translate_weather_description(fields['description'])}",
            f"💧 Влажность: {fields['humidity']}%",
            f"💨 Ветер: {fields['wind_speed']} м/с",
            f"☁️ Облачность: {fields['clouds']}%",
        ]
        return "\n".join(lines)

    def _format_extended_weather(
        self,
        fields: Dict[str, Any],
        extended: Dict[str, Any],
        air_quality: Dict[str, Any],
        location: Dict[str, Any],
    ) -> str:
        """Форматирует расширенную погоду вместе с анализом воздуха."""
        lines = [self._format_basic_weather(fields, location), SEPARATOR]

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

        lines.append(SEPARATOR)
        aqi_index = air_quality.get("aqi_index")
        aqi_index_text = f" (AQI {aqi_index})" if aqi_index is not None else ""
        lines.append(f"🌫 Воздух: {air_quality['aqi_label']}{aqi_index_text}")
        lines.append("📊 Загрязнители:")
        lines.append(air_quality["details"])
        lines.append(f"💬 {air_quality['summary']}")

        return "\n".join(lines)

    def _format_forecast_data(
        self,
        entries: List[Dict[str, Any]],
        location: Dict[str, Any],
        extended: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Форматирует прогноз, группируя записи по дням."""
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
            f"📅 Прогноз для: {self._location_title(location)}",
            SEPARATOR,
            f"\n{SEPARATOR}\n".join(day_blocks),
        ]

        if extended and extended.get("air_quality"):
            air_quality = extended["air_quality"]
            aqi_index = air_quality.get("aqi_index")
            aqi_index_text = f" (AQI {aqi_index})" if aqi_index is not None else ""
            lines.append(SEPARATOR)
            lines.append(f"🌫 Воздух: {air_quality['aqi_label']}{aqi_index_text}")
            lines.append(f"💬 {air_quality['summary']}")

        return "\n".join(lines)

    def _comparison_summary(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Формирует вывод-сравнение по двум городам."""
        if len(entries) < 2:
            return []

        first, second = entries[0], entries[1]
        name1 = self._location_title(first["location"])
        name2 = self._location_title(second["location"])
        temp1 = first["weather"]["temp"]
        temp2 = second["weather"]["temp"]

        summaries: List[str] = []
        if temp1 != temp2:
            warmer, colder = (name1, name2) if temp1 > temp2 else (name2, name1)
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

    def _format_comparison(self, entries: List[Dict[str, Any]]) -> str:
        """Форматирует сравнение погоды в двух городах."""
        lines = ["⚖️ Сравнение погоды", SEPARATOR]

        for entry in entries:
            weather = entry["weather"]
            lines.append(f"🌍 {self._location_title(entry['location'])}")
            lines.append(
                f"  🌡 {format_temperature(weather['temp'])} "
                f"(ощущается как {format_temperature(weather['feels_like'])})"
            )
            lines.append(f"  📋 {translate_weather_description(weather['description'])}")
            lines.append(f"  💧 Влажность: {weather['humidity']}%")
            lines.append(f"  💨 Ветер: {weather['wind_speed']} м/с")

        summary = self._comparison_summary(entries)
        if summary:
            lines.append(SEPARATOR)
            lines.extend(summary)

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Публичные методы
    # ------------------------------------------------------------------ #
    def get_weather_by_city(self, city: str, extended: bool = False) -> Dict[str, Any]:
        """Возвращает текущую погоду по названию города.

        Args:
            city: Название города (например, ``"Moscow"``).
            extended: Если ``True``, добавляет рассвет/закат, давление,
                видимость и полный анализ качества воздуха.

        Raises:
            CityNotFoundError: если город не найден.
        """
        if not city or not city.strip():
            raise CityNotFoundError("Пустой запрос города.")

        city = city.strip()
        geo = self._direct_geocode(city)
        if not geo:
            raise CityNotFoundError(f"Город не найден: {city}")

        place = geo[0]
        lat, lon = float(place["lat"]), float(place["lon"])
        return self._build_weather_response(
            lat=lat,
            lon=lon,
            place=place,
            extended=extended,
            query={"type": "city", "value": city},
        )

    def get_forecast_by_city(self, city: str, extended: bool = False) -> Dict[str, Any]:
        """Возвращает прогноз на 5 дней по названию города.

        Args:
            city: Название города.
            extended: Если ``True``, добавляет анализ качества воздуха.

        Raises:
            CityNotFoundError: если город не найден.
        """
        if not city or not city.strip():
            raise CityNotFoundError("Пустой запрос города.")

        city = city.strip()
        geo = self._direct_geocode(city)
        if not geo:
            raise CityNotFoundError(f"Город не найден: {city}")

        place = geo[0]
        lat, lon = float(place["lat"]), float(place["lon"])

        forecast_data = self._forecast_weather(lat, lon)
        location = self._build_location(place, lat, lon, forecast_data.get("city"))
        entries = self._extract_forecast_entries(forecast_data)

        extended_data: Optional[Dict[str, Any]] = None
        if extended:
            extended_data = {"air_quality": self._analyze_air_quality(self._air_pollution(lat, lon))}

        return {
            "query": {"type": "city", "value": city},
            "location": location,
            "forecast": entries,
            "extended": extended_data,
            "formatted": self._format_forecast_data(entries, location, extended_data),
        }

    def compare_weather_by_cities(self, city1: str, city2: str) -> Dict[str, Any]:
        """Сравнивает текущую погоду в двух городах.

        Args:
            city1: Первый город.
            city2: Второй город.

        Returns:
            Словарь с ключами ``cities`` (список из двух результатов) и
            ``formatted`` (готовый текст сравнения).

        Raises:
            CityNotFoundError: если хотя бы один город не найден.
        """
        entries = [self.get_weather_by_city(city1), self.get_weather_by_city(city2)]
        return {
            "query": {"type": "compare", "value": [city1, city2]},
            "cities": entries,
            "formatted": self._format_comparison(entries),
        }

    def get_weather_by_coordinates(
        self,
        lat: float,
        lon: float,
        extended: bool = False,
    ) -> Dict[str, Any]:
        """Возвращает текущую погоду по координатам.

        Args:
            lat: Широта.
            lon: Долгота.
            extended: Если ``True``, добавляет расширенные данные и анализ воздуха.

        Raises:
            ValueError: если координаты некорректны.
        """
        validate_coordinates(lat, lon)

        reverse = self._reverse_geocode(lat, lon)
        place = reverse[0] if reverse else {}
        return self._build_weather_response(
            lat=lat,
            lon=lon,
            place=place,
            extended=extended,
            query={"type": "coordinates", "value": {"lat": lat, "lon": lon}},
        )

    # ------------------------------------------------------------------ #
    # Общая сборка ответа
    # ------------------------------------------------------------------ #
    def _build_weather_response(
        self,
        lat: float,
        lon: float,
        place: Dict[str, Any],
        extended: bool,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Собирает единый ответ по текущей погоде (для города и координат)."""
        current = self._current_weather(lat, lon)
        fields = self._extract_weather_fields(current)
        location = self._build_location(place, lat, lon, current)

        response: Dict[str, Any] = {
            "query": query,
            "location": location,
            "weather": fields,
            "extended": None,
            "formatted": self._format_basic_weather(fields, location),
        }

        if extended:
            extended_fields = self._extract_extended_fields(current)
            air_quality = self._analyze_air_quality(self._air_pollution(lat, lon))
            response["extended"] = {**extended_fields, "air_quality": air_quality}
            response["formatted"] = self._format_extended_weather(
                fields, extended_fields, air_quality, location
            )

        return response


__all__ = ("OpenWeatherAPI",)
