import asyncio
import json

from weather_vk_bot.bot import VKWeatherBot

SENT = []


class FakeMessages:
    def get_set_params(self, locals_):
        return {k: v for k, v in locals_.items() if k != "self" and v is not None}

    async def send(self, **kwargs):
        SENT.append(kwargs.get("message"))
        return [{}]


class FakeAPI:
    def __init__(self):
        self.messages = FakeMessages()


WEATHER = {
    "weather": {
        "description": "clear sky",
        "temp": 20,
        "feels_like": 19,
        "humidity": 40,
        "wind_speed": 3.0,
        "clouds": 5,
    },
    "location": {"name": "Moscow", "country": "RU"},
    "extended": None,
}


class StubService:
    def get_weather(self, city):
        return WEATHER

    def get_extended_weather(self, city):
        return WEATHER

    def get_forecast(self, city):
        return {"location": WEATHER["location"], "forecast": [], "extended": None}

    def get_weather_by_coordinates(self, lat, lon, extended=False):
        print(f"   [service] coordinates lat={lat} lon={lon}")
        return WEATHER

    @staticmethod
    def parse_coordinates(text):
        from weather_api.utils import parse_coordinates

        return parse_coordinates(text)


def make_event(text="", payload=None, peer_id=777, geo=None):
    message = {
        "date": 1791480000,
        "from_id": peer_id,
        "id": 1,
        "conversation_message_id": 1,
        "out": 0,
        "peer_id": peer_id,
        "text": text,
        "random_id": 0,
        "attachments": [],
        "fwd_messages": [],
        "important": False,
        "is_hidden": False,
        "version": 1000000,
    }
    if payload is not None:
        message["payload"] = payload
    if geo is not None:
        message["geo"] = geo
    return {
        "type": "message_new",
        "object": {"message": message, "client_info": {}},
        "group_id": 241826011,
        "event_id": "x",
    }


GEO = {"type": "point", "coordinates": {"latitude": 55.7558, "longitude": 37.6173}}


async def main():
    bot = VKWeatherBot("dummy", weather_service=StubService())
    api = FakeAPI()

    async def send(name, text="", payload=None, geo=None):
        SENT.clear()
        await bot.bot.router.route(make_event(text, payload, geo=geo), api)
        peer = await bot.bot.state_dispenser.get(777)
        state = peer.state if peer else None
        first = SENT[0].splitlines()[0] if SENT else "<NO RESPONSE>"
        print(f"{name:30} -> {first:32} | state={state}")
        return SENT[0] if SENT else ""

    await send("geo button", "📍 Геолокация", '{"cmd":"geo"}')
    await send("geo attachment", geo=GEO)
    await send("geo + payload", geo=GEO, payload='{"cmd":"geo"}')
    await send("geo button again", "📍 Геолокация", '{"cmd":"geo"}')
    await send("coords text", "55.7558, 37.6173")


asyncio.run(main())
