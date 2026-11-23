import os, json, time, uuid, sys
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from .logger import log, clear_log, ms_since
from .tools import functions, tools

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
MODEL = os.getenv("MODEL")
MAX_STEPS = 10


messages = [{
    "role": "system",
    "content": f"Today is {datetime.now().strftime('%Y-%m-%d')}. "
               "Answer Questions only based on tool data, do not make things up. "
               "Your answer must be based exclusively on the retrieved data: no general knowledge, "
               "tips, advice or assumptions (e.g. station names, transfer points, booking hints). "
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
        try:
            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=tools
            )
        except Exception as e:                  # API error, rate limit, invalid tool call ...
            answer = f"Error: model request failed ({e})"
            log(run_id, "error", ok=False, duration_ms=ms_since(start), detail=str(e))
            messages.append({"role": "assistant", "content": answer})
            return answer
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
            t = time.perf_counter()
            args = c.function.arguments                # raw string, in case parsing fails
            try:
                args = json.loads(args or "{}")
                # tool_call: duration = model time to produce the call
                log(run_id, "tool_call", tool_name=c.function.name, tool_args=args, duration_ms=model_ms)

                t = time.perf_counter()
                ok, result = functions[c.function.name](**args)
                # tool_result: duration = tool execution time
                log(run_id, "tool_result", ok=ok, tool_name=c.function.name, tool_args=args,
                    duration_ms=ms_since(t), detail=None if ok else result)
            except Exception as e:              # invalid JSON, network error ...
                result = f"Error: {e}"
                log(run_id, "error", ok=False, tool_name=c.function.name, tool_args=args,
                    duration_ms=ms_since(t), detail=str(e))

            # always answer the tool call, so the model can react to errors
            messages.append({"role": "tool", "tool_call_id": c.id, "content": result})

    # step limit reached without a final answer
    error = f"StepLimitError: Step limit reached after {MAX_STEPS} model calls."
    log(run_id, "error", ok=False, detail=error)
    messages.append({"role": "assistant", "content": error})
    raise RuntimeError(error)

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

        try:
            print(f"\nAI: {ask(user_input)}\n")
        except RuntimeError as e:
            print(f"\n{e}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            print(f"\n{ask(' '.join(sys.argv[1:]))}\n")   # One-Shot-Answer
        except RuntimeError as e:
            print(f"\n{e}\n", file=sys.stderr)
            sys.exit(1)
    else:
        chat()                               