import re
import threading
import time

from . import config as cfg
from .engine import (find_text_on_screen, parse_return_time, seconds_until,
                     turn_off_screen, wake_up_screen, perform_action,
                     ensure_claude_is_active)
from .logger import log
from .queue_manager import load_queue, get_next_prompt, load_state, save_state

MODE_CLASSIC = "classic"
MODE_QUEUE = "queue"


class Stopped(Exception):
    pass


def _words(text):
    return set(re.findall(r"\w{3,}", text.lower()))


def _similar(a, b, threshold=0.97):
    if not a and not b:
        return True
    return len(a & b) / max(1, len(a | b)) >= threshold


class Runner(threading.Thread):
    def __init__(self, mode, allow_screen_off, on_status=None, on_countdown=None):
        super().__init__(daemon=True)
        self.mode = mode
        self.allow_screen_off = allow_screen_off
        self.stop_event = threading.Event()
        self.on_status = on_status or (lambda s: None)
        self.on_countdown = on_countdown or (lambda s: None)
        self._last_words = None

    def stop(self):
        self.stop_event.set()

    def _sleep(self, seconds, countdown=False):
        end = time.monotonic() + seconds
        while True:
            left = end - time.monotonic()
            if left <= 0:
                break
            if self.stop_event.wait(min(1.0, left)):
                raise Stopped()
            if countdown:
                self.on_countdown(int(left))
        if countdown:
            self.on_countdown(0)

    def _wait_for_reset(self, hour, minute):
        import random
        wait = seconds_until(hour, minute) + random.randint(65, 180)
        log("ESPERA", f"Aguardando {int(wait // 60)} minutos...")
        self.on_status("Aguardando reset da cota")
        screen_off = self.allow_screen_off and wait > 120
        try:
            if screen_off:
                turn_off_screen()
                self._sleep(max(0, wait - 15), countdown=True)
            else:
                self._sleep(wait, countdown=True)
        finally:
            if screen_off:
                wake_up_screen()
        self._sleep(15 if screen_off else 0)

    def _handle_limit(self, ret):
        h, m = ret
        log("ALERTA", f"Limite atingido! Horário de retorno: {h:02d}:{m:02d}")
        self._wait_for_reset(h, m)
        log("AÇÃO", "Retornando ao workspace e enviando 'continue'...")
        self.on_status("Enviando 'continue'")
        perform_action("continue")
        self._last_words = None
        self._sleep(120)

    def run(self):
        self.on_status("Iniciado")
        try:
            if self.mode == MODE_QUEUE:
                self._loop_queue()
            else:
                self._loop_classic()
        except Stopped:
            log("INFO", "Execução interrompida.")
        except Exception as e:
            log("ERRO", f"{type(e).__name__}: {e}")
        finally:
            self.on_countdown(0)
            self.on_status("Parado")

    def _loop_classic(self):
        log("OK", "MODO CLÁSSICO iniciado.")
        while True:
            self.on_status("Verificando cota")
            ensure_claude_is_active()
            ret = parse_return_time(find_text_on_screen())
            if ret:
                self._handle_limit(ret)
            else:
                log("OK", f"Sem limites. Nova verificação em {cfg.CHECK_INTERVAL}s...")
                self.on_status("Monitorando")
                self._sleep(cfg.CHECK_INTERVAL)

    def _loop_queue(self):
        log("OK", "MODO FILA iniciado.")
        while True:
            self.on_status("Verificando cota")
            ensure_claude_is_active()
            text = find_text_on_screen()
            ret = parse_return_time(text)
            state = load_state()

            if ret:
                self._handle_limit(ret)
                continue

            if state.get("active_prompt"):
                # Resposta concluída = tela estável entre duas verificações
                cur = _words(text)
                if self._last_words is not None and _similar(self._last_words, cur):
                    log("FILA", "Resposta finalizada. Avançando na fila...")
                    save_state({"active_prompt": None})
                    self._last_words = None
                    continue
                self._last_words = cur
                log("OK", "Aguardando conclusão da resposta atual...")
                self.on_status("Claude respondendo")
                self._sleep(cfg.BUSY_INTERVAL)
                continue

            if load_queue():
                nxt = get_next_prompt()
                save_state({"active_prompt": nxt})
                log("FILA", "Lançando novo prompt da fila.")
                self.on_status("Enviando prompt")
                perform_action(nxt)
                self._last_words = None
                self._sleep(cfg.AFTER_ACTION_DELAY)
            else:
                log("OK", f"Fila vazia e sem limites. Nova verificação em {cfg.CHECK_INTERVAL}s...")
                self.on_status("Fila vazia")
                self._sleep(cfg.CHECK_INTERVAL)
