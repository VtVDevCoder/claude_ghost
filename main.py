import sys
import subprocess

from .config import CYAN, RED, YELLOW, MAGENTA, BOLD, RESET
from .queue_manager import add_prompt, show_queue
from .runner import Runner, MODE_CLASSIC, MODE_QUEUE


def ask_screen_preference():
    print(f"\n{BOLD}Configuração de Energia:{RESET}")
    print("1. Desligar a tela automaticamente durante as esperas longas")
    print("2. Manter a tela ligada o tempo todo")
    return input(f"{CYAN}Escolha (1 ou 2): {RESET}").strip() == "1"


def _run(mode):
    r = Runner(mode, ask_screen_preference())
    r.start()
    while r.is_alive():
        r.join(0.5)


def menu():
    while True:
        print(f"\n{BOLD}{MAGENTA}=== Claude Ghost Configuration Panel v10 ==={RESET}")
        print("1. Modo Clássico (Apenas 'Continue' automático)")
        print("2. Modo com Fila de Prompts")
        print("3. Adicionar Prompt à Fila")
        print("4. Ver Fila de Prompts")
        print("5. Sair")
        choice = input(f"\n{CYAN}Escolha uma opção (1 a 5): {RESET}").strip()

        if choice == "1":
            _run(MODE_CLASSIC)
            break
        elif choice == "2":
            _run(MODE_QUEUE)
            break
        elif choice == "3":
            text = input(f"{CYAN}Digite o texto do prompt: {RESET}").strip()
            if text:
                add_prompt(text)
            else:
                print(f"{RED}Prompt vazio, não adicionado.{RESET}")
        elif choice == "4":
            show_queue()
        elif choice == "5":
            sys.exit(0)
        else:
            print(f"{RED}[ERRO] Opção inválida.{RESET}")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Interrompido (Ctrl+C).{RESET}")
        try:
            subprocess.run(["xset", "dpms", "force", "on"], check=True)
        except Exception:
            pass
        sys.exit(0)
