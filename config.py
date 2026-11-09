import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE_DIR, "prompts_queue.json")
STATE_FILE = os.path.join(BASE_DIR, "state.json")

# Posição do favorito do Claude no navegador (usado se o Claude não estiver visível)
BOOKMARK_POS = (265, 50)

CHECK_INTERVAL = 45        # segundos entre verificações
BUSY_INTERVAL = 15         # segundos entre verificações enquanto o Claude responde
AFTER_ACTION_DELAY = 60    # pausa após enviar algo

# Cores ANSI (console)
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"
