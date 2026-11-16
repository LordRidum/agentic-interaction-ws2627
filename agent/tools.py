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
}]