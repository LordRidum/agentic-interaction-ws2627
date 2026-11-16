import os, json, time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL")
LOG_FILE = "agent_log.json"


def log(run_id, event, ok=True, tool_name=None, tool_args=None, duration_ms=None, detail=None):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "event": event,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "ok": ok,
        "model": MODEL,
        "duration_ms": duration_ms,
        "detail": detail,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def clear_log():
    if os.path.exists(LOG_FILE):
        Path(LOG_FILE).write_text("")


def ms_since(start):
    return round((time.perf_counter() - start) * 1000)