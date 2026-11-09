from . import config as c

_COLORS = {"INFO": c.CYAN, "OK": c.GREEN, "AVISO": c.YELLOW, "ERRO": c.RED,
           "ALERTA": c.RED, "ESPERA": c.YELLOW, "ENERGIA": c.MAGENTA,
           "FILA": c.CYAN, "AÇÃO": c.GREEN, "LIMPEZA": c.CYAN, "SUCESSO": c.GREEN}


def _console(level, msg):
    print(f"{_COLORS.get(level, '')}[{level}]{c.RESET} {msg}")


_handler = _console


def set_handler(fn):
    global _handler
    _handler = fn or _console


def log(level, msg):
    _handler(level, msg)
