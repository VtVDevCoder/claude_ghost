import time
import random
import re
import subprocess
from datetime import datetime, timedelta
from PIL import ImageGrab
import pytesseract
import pyautogui
import numpy as np
from .config import GREEN, YELLOW, CYAN, RED, MAGENTA, BOLD, RESET

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def human_mouse_move(target_x, target_y):
    current_x, current_y = pyautogui.position()
    dist = np.hypot(target_x - current_x, target_y - current_y)
    duration = max(0.6, dist / 800.0) + random.uniform(0.2, 0.5)
    steps = int(duration * 60)
    
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
        pyautogui.write(char)
        time.sleep(random.uniform(0.08, 0.28))

def find_text_on_screen():
    screenshot = ImageGrab.grab()
    return pytesseract.image_to_string(screenshot)

def parse_return_time(text):
    match = re.search(r'(?:returns at|resets at|until)\s+(\d{1,2}:\d{2}\s*(?:AM|PM))', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def focus_browser_window():
    try:
        subprocess.run(["wmctrl", "-x", "-a", "firefox"], check=True)
        time.sleep(0.8)
        return True
    except Exception:
        return False

def ensure_claude_is_active():
    print(f"{CYAN}[INFO]{RESET} Verificando se o Claude está ativo na tela...")
    focus_browser_window()
    time.sleep(1.0)
    
    screen_text = find_text_on_screen()
    if "claude" not in screen_text.lower() and "messages" not in screen_text.lower():
        print(f"{YELLOW}[AVISO]{RESET} Claude não detectado. Abrindo via favoritos...")
        fav_x, fav_y = 265, 50
        human_mouse_move(fav_x, fav_y)
        time.sleep(random.uniform(0.2, 0.5))
        pyautogui.click()
        time.sleep(3.5)
    else:
        print(f"{GREEN}[OK]{RESET} Claude está visível e ativo.")

def locate_chat_box():
    screen_w, screen_h = pyautogui.size()
    try:
        geom_output = subprocess.check_output(["xdotool", "getactivewindow", "getwindowgeometry", "--shell"]).decode()
        width = int(re.search(r'WIDTH=(\d+)', geom_output).group(1))
        height = int(re.search(r'HEIGHT=(\d+)', geom_output).group(1))
        x_pos = int(re.search(r'X=(\d+)', geom_output).group(1))
        y_pos = int(re.search(r'Y=(\d+)', geom_output).group(1))
        
        box_x = x_pos + (width // 2) + random.randint(-20, 20)
        box_y = y_pos + height - 80 + random.randint(-10, 10)
        return box_x, box_y
    except Exception:
        box_x = (screen_w // 2) + random.randint(-30, 30)
        box_y = screen_h - 100 + random.randint(-10, 10)
        return box_x, box_y

def turn_off_screen():
    print(f"{MAGENTA}[ENERGIA]{RESET} Desligando o monitor para economizar energia...")
    try:
        subprocess.run(["xset", "dpms", "force", "off"], check=True)
    except Exception as e:
        print(f"{RED}[ERRO]{RESET} Falha ao desligar a tela: {e}")

def wake_up_screen():
    print(f"{GREEN}[ENERGIA]{RESET} Acendendo o monitor...")
    try:
        subprocess.run(["xset", "dpms", "force", "on"], check=True)
        pyautogui.move(1, 0)
        pyautogui.move(-1, 0)
    except Exception as e:
        print(f"{RED}[ERRO]{RESET} Falha ao acordar a tela: {e}")
    time.sleep(2.0)

def perform_action(text_to_send):
    ensure_claude_is_active()
    
    bx, by = locate_chat_box()
    human_mouse_move(bx, by)
    time.sleep(random.uniform(0.4, 0.8))
    pyautogui.click()
    time.sleep(random.uniform(0.3, 0.6))
    
    print(f"{CYAN}[LIMPEZA]{RESET} Limpando a barra de texto antes de enviar...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('backspace')
    time.sleep(0.4)
    
    human_type(text_to_send)
    time.sleep(random.uniform(0.5, 1.0))
    pyautogui.press('enter')
    
    print(f"{BOLD}{GREEN}[SUCESSO]{RESET} Enviado para o Claude: '{text_to_send}'\n")
