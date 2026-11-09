import json
import os
from .config import QUEUE_FILE, STATE_FILE
from .logger import log


def _read(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, path)


def load_queue():
    q = _read(QUEUE_FILE, [])
    return q if isinstance(q, list) else []


def save_queue(queue):
    _write(QUEUE_FILE, queue)


def add_prompt(prompt_text):
    queue = load_queue()
    queue.append(prompt_text)
    save_queue(queue)
    log("FILA", f"Prompt adicionado. Total na fila: {len(queue)}")


def get_next_prompt():
    queue = load_queue()
    if queue:
        prompt = queue.pop(0)
        save_queue(queue)
        return prompt
    return None


def show_queue():
    queue = load_queue()
    if not queue:
        log("FILA", "A fila de prompts está vazia.")
        return
    log("FILA", f"=== PENDENTES ({len(queue)}) ===")
    for idx, p in enumerate(queue, 1):
        preview = p[:60] + "..." if len(p) > 60 else p
        log("FILA", f"{idx}. {preview}")


def load_state():
    s = _read(STATE_FILE, {"active_prompt": None})
    return s if isinstance(s, dict) else {"active_prompt": None}


def save_state(state):
    _write(STATE_FILE, state)
