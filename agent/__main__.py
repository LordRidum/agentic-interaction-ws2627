import os, json, requests, time, uuid, sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from groq import Groq
from pathlib import Path

load_dotenv()

client = Groq(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("MODEL")
DATABASE = os.getenv("DATA_BASE_URL")
LOG_FILE = "agent_log.json"


# ==============================
#  HELPERS
# ==============================

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


def read_data(path=""):
    url = f"{DATABASE}/{path.lstrip('/')}" if path else DATABASE
    r = requests.get(url, timeout=10)
    if not r.ok:
        return False, f"Error: HTTP {r.status_code}"
    return True, r.text[:20000]


# ==============================
#  MODEL CONFIG
# ==============================

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

messages = [{
    "role": "system",
    "content": f"Today is {datetime.now().strftime('%Y-%m-%d')}. "
               "Answer Questions only based on tool data, do not make things up. "
               "Dont guess paths, use the paths from index"
}]


# ==============================
#  CHAT LOOP
# ==============================

def ask(user_input):
    run_id = str(uuid.uuid4())                  # each question gets its own run_id
    log(run_id, "user_task", detail=user_input)
    messages.append({"role": "user", "content": user_input})

    while True:
        start = time.perf_counter()
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools
        )
        model_ms = ms_since(start)
        msg = response.choices[0].message

        if not msg.tool_calls:                  # no tool requested --> final answer
            log(run_id, "final", duration_ms=model_ms, detail=msg.content)
            break

        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {"id": c.id, "type": "function",
                    "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in msg.tool_calls
            ],
        })

        # run each requested tool and hand the result back
        for c in msg.tool_calls:
            args = json.loads(c.function.arguments or "{}")
            log(run_id, "tool_call", tool_name=c.function.name, tool_args=args, duration_ms=model_ms)

            t = time.perf_counter()
            ok, result = read_data(args.get("path", ""))
            log(run_id, "tool_result", ok=ok, tool_name=c.function.name, tool_args=args,
                duration_ms=ms_since(t), detail=None if ok else result)

            messages.append({"role": "tool", "tool_call_id": c.id, "content": result})

    messages.append({"role": "assistant", "content": msg.content})
    return msg.content

def chat():
    while True:
        user_input = input("User: ")

        if user_input.lower() == "exit":
            print("Exiting chat.")
            break

        if user_input.lower() == "clear":
            clear_log()
            del messages[1:]      # Gesprächsverlauf zurücksetzen, System-Prompt bleibt
            print("Log cleared.\n")
            continue              # zurück zum Anfang der Schleife, ask() wird übersprungen

        print(f"AI: {ask(user_input)}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(ask(" ".join(sys.argv[1:])))   # One-Shot: Antwort ausgeben, Programm endet
    else:
        chat()                                # kein Argument: wie bisher