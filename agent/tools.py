import os, requests
from dotenv import load_dotenv

load_dotenv()

DATABASE = os.getenv("DATA_BASE_URL")


def read_data(path=""):
    url = f"{DATABASE}/{path.lstrip('/')}" if path else DATABASE
    r = requests.get(url, timeout=10)
    if not r.ok:
        return False, f"Error: HTTP {r.status_code}"
    return True, r.text[:20000]


def get_weather(city, date):
    r = requests.get(f"{DATABASE}/weather/{city}/{date}.json", timeout=10)
    if not r.ok:
        return False, f"Error: HTTP {r.status_code}"
    return True, r.text[:20000]


def get_train_connections(destination, date, origin=None):
    if not origin:                              # no start given --> home city of the user
        r = requests.get(f"{DATABASE}/context.json", timeout=10)
        if not r.ok:
            return False, f"Error: HTTP {r.status_code}"
        origin = r.json()["home"].lower()
    r = requests.get(f"{DATABASE}/transit/{origin}/{destination}/{date}.json", timeout=10)
    if not r.ok:
        return False, f"Error: HTTP {r.status_code}"
    return True, r.text[:20000]


functions = {
    "read_data": read_data,
    "get_weather": get_weather,
    "get_train_connections": get_train_connections,
}

tools = [{
    "type": "function",
    "function": {
        "name": "read_data",
        "description": "Reads data from the API. Call with an empty path first to get the index of available paths.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Returns the weather of a city on a day. City in lowercase German name without umlauts (e.g. muenchen, not munich), date as YYYY-MM-DD.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}, "date": {"type": "string"}},
            "required": ["city", "date"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "get_train_connections",
        "description": "Returns the train connections between two cities on a day. Leave out origin if the user names no start, then their home city is used. Cities in lowercase German names without umlauts (e.g. muenchen, not munich), date as YYYY-MM-DD.",
        "parameters": {
            "type": "object",
            "properties": {"origin": {"type": "string"}, "destination": {"type": "string"}, "date": {"type": "string"}},
            "required": ["destination", "date"],
        },
    },
}]