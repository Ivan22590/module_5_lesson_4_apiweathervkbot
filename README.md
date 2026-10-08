# 🌤 VK Weather Bot

Production-ready погодный бот ВКонтакте на **VKBottle** с backend-модулем для **OpenWeatherMap API**.

Бот показывает текущую погоду, прогноз на 5 дней, погоду по геолокации и расширенную
аналитику с оценкой качества воздуха. Проект разделён на независимый backend
(`weather_api`) и frontend-слой бота (`weather_vk_bot`), что упрощает поддержку
и дальнейшее расширение.

---

## ✨ Возможности

- 🌤 **Погода сейчас** — температура, ощущаемая температура, влажность, ветер, облачность.
- 📅 **Прогноз на 5 дней** — сгруппирован по дням с диапазоном температур и описанием.
- 🇷🇺 **Погодные условия на русском** — описания OpenWeatherMap переводятся на русский
  («overcast clouds» → «пасмурно», «light rain» → «небольшой дождь» и т.д.).
- 📍 **Геолокация** — кнопка VK `location` или ручной ввод координат (`55.7558, 37.6173`).
- 🌫 **Расширенный режим** — рассвет/закат, давление (в т.ч. на уровне моря и земли),
  видимость и полный анализ качества воздуха.
- 💬 **Анализ воздуха** — AQI-индекс, метка категории, список загрязнителей и
  человекочитаемый вывод на русском.
- ⌨️ **Кнопочное меню** с навигацией «Назад» / «Главное меню».
- 🧠 **FSM-состояния** для сценариев диалога.
- 🖥 **CLI** для использования backend без бота.

---

## 🏗 Структура проекта

```
.
├── OpenWeatherAPI.py            # Фасад: from OpenWeatherAPI import OpenWeatherAPI
├── weather_api/                 # Backend (OpenWeatherMap)
│   ├── __init__.py
│   ├── config.py                # dotenv, API-ключ, константы endpoint-ов
│   ├── exceptions.py            # OpenWeatherAPIError, CityNotFoundError, APIConnectionError
│   ├── utils.py                 # K→°C, парсинг координат, timestamp→время
│   ├── client.py                # Класс OpenWeatherAPI (запросы, аналитика, форматтеры)
│   └── cli.py                   # Точка входа CLI
├── weather_vk_bot/              # Frontend (VKBottle)
│   ├── __init__.py
│   ├── main.py                  # Точка входа бота
│   ├── bot.py                   # Класс VKWeatherBot (роуты, middleware, Long Poll)
│   ├── keyboards/
│   │   ├── main_keyboard.py     # Главное меню
│   │   └── navigation_keyboard.py
│   ├── services/
│   │   ├── state_manager.py     # FSM-состояния
│   │   ├── formatter.py         # Оформление сообщений
│   │   └── weather_service.py   # Связка VKBottle ↔ OpenWeatherAPI
│   └── handlers/
│       ├── menu.py
│       ├── weather.py
│       ├── forecast.py
│       ├── geo.py
│       ├── help.py
│       └── fallback.py          # Запасной ответ на нераспознанный ввод
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🚀 Установка и запуск

### 1. Требования

- Python **3.11+**
- Токен сообщества ВКонтакте (Long Poll API включён)
- API-ключ OpenWeatherMap

### 2. Виртуальное окружение и зависимости

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Настройка окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```dotenv
OPEN_WEATHER_API_KEY=your_openweather_api_key
VK_BOT_TOKEN=your_vk_group_token
```

- **API-ключ OpenWeatherMap** — https://home.openweathermap.org/api_keys
- **Токен сообщества ВК** — Управление сообществом → Настройки → Работа с API → Создать ключ.
  В настройках Long Poll API включите событие **Входящие сообщения**.

> ⚠️ Файл `.env` содержит секреты и добавлен в `.gitignore`. Не коммитьте его.

### 4. Запуск бота

```powershell
.\.venv\Scripts\python.exe -m weather_vk_bot.main
```

или как обычный скрипт:

```powershell
.\.venv\Scripts\python.exe weather_vk_bot\main.py
```

---

## 🖥 Использование CLI

Backend можно использовать без бота:

```powershell
# Текущая погода по городу
python -m weather_api.cli --city Moscow

# Расширенный режим (давление, рассвет/закат, анализ воздуха)
python -m weather_api.cli --city Moscow --extended

# Прогноз на 5 дней
python -m weather_api.cli --city Moscow --forecast

# Погода по координатам
python -m weather_api.cli --coords "55.7558, 37.6173" --extended
```

### Использование как библиотеки

```python
from OpenWeatherAPI import OpenWeatherAPI, CityNotFoundError

with OpenWeatherAPI() as api:
    weather = api.get_weather_by_city("Moscow", extended=True)
    print(weather["formatted"])

    air = weather["extended"]["air_quality"]
    print(air["aqi_label"], air["summary"])
```

---

## 🤖 Сценарии бота

| Действие             | Кнопка / ввод              | Состояние FSM            | Метод backend                          |
| -------------------- | -------------------------- | ------------------------ | -------------------------------------- |
| Погода сейчас        | 🌤 Погода сейчас            | `WAITING_CITY`           | `get_weather_by_city`                  |
| Прогноз 5 дней       | 📅 Прогноз 5 дней           | `WAITING_FORECAST_CITY`  | `get_forecast_by_city`                 |
| Геолокация           | 📍 Геолокация / координаты  | `WAITING_GEO`            | `get_weather_by_coordinates`           |
| Расширенный режим    | 🌫 Расширенный режим        | `WAITING_EXTENDED`       | `get_weather_by_city(extended=True)`   |
| Справка              | ℹ️ Помощь                   | —                        | —                                      |
| Навигация            | ⬅️ Назад / 🏠 Главное меню  | —                        | —                                      |

Координаты принимаются в форматах:

```
55.7558,37.6173
55.7558 37.6173
```

---

## 🌫 Логика оценки качества воздуха

Метод `OpenWeatherAPI._analyze_air_quality` оценивает каждый загрязнитель
по фиксированной шкале и берёт худшую категорию.

| Загрязнитель | Good     | Fair       | Moderate    | Poor        | Very Poor |
| ------------ | -------- | ---------- | ----------- | ----------- | --------- |
| SO2          | < 20     | < 80       | < 250       | < 350       | ≥ 350     |
| NO2          | < 40     | < 70       | < 150       | < 200       | ≥ 200     |
| PM10         | < 20     | < 50       | < 100       | < 200       | ≥ 200     |
| PM2.5        | < 10     | < 25       | < 50        | < 75        | ≥ 75      |
| O3           | < 60     | < 100      | < 140       | < 180       | ≥ 180     |
| CO           | < 4400   | < 9400     | < 12400     | < 15400     | ≥ 15400   |

Результат анализа содержит:

- `aqi_index` — индекс AQI из ответа API
- `aqi_label` — категория (`Good` / `Fair` / `Moderate` / `Poor` / `Very Poor`)
- `pollutants` — детализация по каждому загрязнителю
- `exceeded_pollutants` — загрязнители выше нормы
- `summary` — человекочитаемый вывод на русском

Пример вывода в боте:

```
🌫 Воздух: Fair (AQI 2)
📊 Загрязнители:
• O3: 75.10 (Fair)
💬 Качество воздуха: Fair. Незначительно повышен уровень загрязнителей.
   Повышенные загрязнители: O3.
```

---

## 🔌 Используемые endpoint-ы OpenWeatherMap

| Назначение          | Endpoint                            |
| ------------------- | ----------------------------------- |
| Current Weather     | `/data/2.5/weather`                 |
| 5 Day Forecast      | `/data/2.5/forecast`                |
| Air Pollution       | `/data/2.5/air_pollution`           |
| Direct Geocoding    | `/geo/1.0/direct`                   |
| Reverse Geocoding   | `/geo/1.0/reverse`                  |

---

## 🧩 Архитектура

- **`weather_api`** — независимый backend. Не зависит от VKBottle, пригоден для
  повторного использования. Возвращает структурированные данные и готовый текст.
- **`weather_vk_bot.services.weather_service`** — единственное место связи с backend;
  превращает технические исключения в понятные сообщения для пользователя.
- **`weather_vk_bot.services.formatter`** — только оформление текста.
- **`weather_vk_bot.services.state_manager`** — только работа с состояниями.
- **`weather_vk_bot.handlers`** — только пользовательские сценарии.

---

## 🛡 Обработка ошибок

- **Город не найден** → `CityNotFoundError` → «Город «…» не найден…»
- **API недоступен** → `APIConnectionError` → «Сервис погоды недоступен…»
- **Неверные координаты** → «Не удалось распознать координаты…»
- **Пустой ввод** → «Пустой ввод…»
- **Ошибка геолокации** → «Не удалось определить координаты…»

Все секреты берутся из переменных окружения, используется `try/except` и `logging`.

---

## 🩺 Если бот не отвечает

Проверьте по порядку:

1. **Long Poll включён и события активны.** Управление сообществом → Настройки →
   Работа с API → Long Poll API: включите его и отметьте события **Входящие сообщения**
   (`message_new`) и **Действия с сообщениями** (`message_event`) для callback-кнопок.
2. **В сообществе включена кнопка «Начать».** Тогда первым сообщением пользователя будет
   команда `start` — бот её обрабатывает и показывает меню.
3. **Бот отвечает на любой ввод.** Для сообщений, не совпавших ни с одним сценарием,
   предусмотрен запасной обработчик (`handlers/fallback.py`) — он показывает подсказку
   и главное меню, поэтому клавиатура появляется всегда.
4. **Токен актуален.** Если `VK_BOT_TOKEN` отозван или неверен, бот не запустится —
   смотрите логи при старте.
5. **Смотрите логи.** В консоли выводятся входящие сообщения (`LoggingMiddleware`)
   и ошибки обработки.

---

## 🔮 Идеи для развития

Архитектура подготовлена под:

- подписки и уведомления о погоде;
- ежедневные прогнозы;
- сохранённые (избранные) города;
- предупреждения о плохом качестве воздуха;
- мультиязычность;
- UV Index, Historical API, Alerts (заготовки endpoint-ов уже есть в `client.py`).

---

## 📄 Лицензия

Учебный проект. Данные предоставлены [OpenWeatherMap](https://openweathermap.org/).
