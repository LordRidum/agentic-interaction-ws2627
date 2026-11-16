import os, json, time, uuid, sys
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

from .logger import log, clear_log, ms_since
from .tools import read_data, tools

load_dotenv()

client = Groq(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("MODEL")
MAX_STEPS = 10      # max model calls per question, prevents endless tool loops


messages = [{
    "role": "system",
    "content": f"Today is {datetime.now().strftime('%Y-%m-%d')}. "
               "Answer Questions only based on tool data, do not make things up. "
               "Dont guess paths, start by reading the index and only use paths from its endpoints."
}]


# ==============================
#  AGENT
# ==============================

def ask(user_input):
    run_id = str(uuid.uuid4())                  # each question gets its own run_id
    log(run_id, "user_task", detail=user_input)
    messages.append({"role": "user", "content": user_input})

    for _ in range(MAX_STEPS):
        start = time.perf_counter()
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools
        )
        model_ms = ms_since(start)
        msg = response.choices[0].message

        if not msg.tool_calls:                  # no tool requested --> final answer
            log(run_id, "final", duration_ms=model_ms, detail=msg.content)
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

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

    # step limit reached without a final answer
    answer = f"Stopped: no final answer after {MAX_STEPS} steps."
    log(run_id, "final", ok=False, detail=answer)
    messages.append({"role": "assistant", "content": answer})
    return answer

def chat():
    while True:
        user_input = input("User: ")

        if user_input.lower() == "exit":
            print("Exiting chat.")
            break

        if user_input.lower() == "clear":
            clear_log()
            del messages[1:]
            print("Log cleared.\n")
            continue              # skip to next iteration

        print(f"AI: {ask(user_input)}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(ask(" ".join(sys.argv[1:])))   # One-Shot-Answer
    else:
        chat()                               