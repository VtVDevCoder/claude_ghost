import json
import os
from .config import QUEUE_FILE, STATE_FILE, GREEN, YELLOW, RED, CYAN, RESET, BOLD

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)

def add_prompt(prompt_text):
    queue = load_queue()
    queue.append(prompt_text)
    save_queue(queue)
    print(f"{GREEN}[FILA]{RESET} Prompt adicionado com sucesso! Total na fila: {BOLD}{len(queue)}{RESET}")

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
        print(f"{YELLOW}[FILA]{RESET} A fila de prompts está vazia.")
    else:
        print(f"\n{CYAN}=== FILA DE PROMPTS PENDENTES ({len(queue)}) ==={RESET}")
        for idx, p in enumerate(queue, 1):
            preview = p[:60] + "..." if len(p) > 60 else p
            print(f" {BOLD}{idx}.{RESET} {preview}")
        print()

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"active_prompt": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active_prompt": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)
