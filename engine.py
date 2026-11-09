import time
import random
import re
import subprocess
from datetime import datetime, timedelta
from PIL import ImageGrab
import pytesseract
import pyautogui
import numpy as np
from . import config as cfg
from .logger import log

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

_RETURN_RE = re.compile(
    r'(?:returns\s+at|resets?\s+at|until|volta\s+(?:às|as)|retorna\s+(?:às|as)|'
    r'reinicia\s+(?:às|as)|at[ée])\s+(\d{1,2}):(\d{2})\s*(AM|PM)?',
    re.IGNORECASE,
)


def human_mouse_move(target_x, target_y):
    current_x, current_y = pyautogui.position()
    dist = float(np.hypot(target_x - current_x, target_y - current_y))
    duration = max(0.6, dist / 800.0) + random.uniform(0.2, 0.5)
    steps = max(1, int(duration * 60))

    for i in range(steps + 1):
        t = i / float(steps)
        ease_t = 1 - (1 - t) ** 3
        jitter_x = random.uniform(-1.5, 1.5) if 0 < t < 1 else 0
        jitter_y = random.uniform(-1.5, 1.5) if 0 < t < 1 else 0
        x = int(current_x + (target_x - current_x) * ease_t + jitter_x)
        y = int(current_y + (target_y - current_y) * ease_t + jitter_y)
        pyautogui.moveTo(x, y)
        time.sleep(duration / steps)


def human_type(text):
    for char in text:
        if char == "\n":
            pyautogui.hotkey("shift", "enter")
        elif char.isascii() and char.isprintable():
            pyautogui.write(char)
        else:
            # pyautogui.write não suporta acentos/Unicode
            try:
                subprocess.run(["xdotool", "type", "--clearmodifiers", "--", char], check=True)
            except Exception:
                log("ERRO", f"Não foi possível digitar o caractere {char!r}")
        time.sleep(random.uniform(0.08, 0.28))


def find_text_on_screen():
    return pytesseract.image_to_string(ImageGrab.grab())


def parse_return_time(text):
    """Retorna (hora24, minuto) ou None."""
    m = _RETURN_RE.search(text)
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3)
    if ampm:
        ampm = ampm.upper()
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if ampm == "PM" else 0)
    if hour > 23 or minute > 59:
        return None
    return hour, minute


def seconds_until(hour, minute):
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def focus_browser_window():
    try:
        subprocess.run(["wmctrl", "-x", "-a", "firefox"], check=True)
        time.sleep(0.8)
        return True
    except Exception:
        return False


def ensure_claude_is_active():
    log("INFO", "Verificando se o Claude está ativo na tela...")
    focus_browser_window()
    time.sleep(1.0)

    screen_text = find_text_on_screen().lower()
    if "claude" not in screen_text and "messages" not in screen_text:
        log("AVISO", "Claude não detectado. Abrindo via favoritos...")
        human_mouse_move(*cfg.BOOKMARK_POS)
        time.sleep(random.uniform(0.2, 0.5))
        pyautogui.click()
        time.sleep(3.5)
    else:
        log("OK", "Claude está visível e ativo.")


def locate_chat_box():
    screen_w, screen_h = pyautogui.size()
    try:
        out = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowgeometry", "--shell"]
        ).decode()
        g = {k: int(v) for k, v in re.findall(r'^(WIDTH|HEIGHT|X|Y)=(\d+)', out, re.M)}
        return (g["X"] + g["WIDTH"] // 2 + random.randint(-20, 20),
                g["Y"] + g["HEIGHT"] - 80 + random.randint(-10, 10))
    except Exception:
        return (screen_w // 2 + random.randint(-30, 30),
                screen_h - 100 + random.randint(-10, 10))


def turn_off_screen():
    log("ENERGIA", "Desligando o monitor para economizar energia...")
    try:
        subprocess.run(["xset", "dpms", "force", "off"], check=True)
    except Exception as e:
        log("ERRO", f"Falha ao desligar a tela: {e}")


def wake_up_screen():
    log("ENERGIA", "Acendendo o monitor...")
    try:
        subprocess.run(["xset", "dpms", "force", "on"], check=True)
        pyautogui.move(1, 0)
        pyautogui.move(-1, 0)
    except Exception as e:
        log("ERRO", f"Falha ao acordar a tela: {e}")
    time.sleep(2.0)


def perform_action(text_to_send):
    ensure_claude_is_active()

    bx, by = locate_chat_box()
    human_mouse_move(bx, by)
    time.sleep(random.uniform(0.4, 0.8))
    pyautogui.click()
    time.sleep(random.uniform(0.3, 0.6))

    log("LIMPEZA", "Limpando a barra de texto antes de enviar...")
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.press("backspace")
    time.sleep(0.4)

    human_type(text_to_send)
    time.sleep(random.uniform(0.5, 1.0))
    pyautogui.press("enter")

    preview = text_to_send if len(text_to_send) <= 80 else text_to_send[:80] + "..."
    log("SUCESSO", f"Enviado para o Claude: '{preview}'")
