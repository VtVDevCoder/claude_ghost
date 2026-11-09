import time
import random
import sys
import subprocess
from datetime import datetime, timedelta
from .config import GREEN, YELLOW, CYAN, RED, MAGENTA, BOLD, RESET
from .queue_manager import add_prompt, get_next_prompt, show_queue, load_queue, load_state, save_state
from .engine import find_text_on_screen, parse_return_time, turn_off_screen, wake_up_screen, perform_action, ensure_claude_is_active

def run_classic_loop(allow_screen_off: bool):
    print(f"\n{BOLD}{GREEN}[MODO CLÁSSICO: SÓ CONTINUE INICIADO]{RESET} (Desligar tela: {'Sim' if allow_screen_off else 'Não'})\n")
    
    while True:
        ensure_claude_is_active()
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{CYAN}[{timestamp}]{RESET} Verificando status de cota na tela...")
        
        screen_text = find_text_on_screen()
        time_str = parse_return_time(screen_text)
        
        if time_str:
            print(f"{RED}[ALERTA]{RESET} Limite atingido! Horário de retorno: {BOLD}{time_str}{RESET}")
            
            now = datetime.now()
            target_time = datetime.strptime(time_str, "%I:%M %p").replace(
                year=now.year, month=now.month, day=now.day
            )
            if target_time < now:
                target_time += timedelta(days=1)
            
            human_fuzz_delay = random.randint(65, 180)
            wait_seconds = (target_time - now).total_seconds() + human_fuzz_delay
            
            print(f"{YELLOW}[ESPERA]{RESET} Aguardando {BOLD}{int(wait_seconds // 60)}{RESET} minutos...")
            
            if allow_screen_off and wait_seconds > 120:
                turn_off_screen()
                time.sleep(max(0, wait_seconds - 15))
                wake_up_screen()
                time.sleep(15)
            else:
                while wait_seconds > 0:
                    sleep_chunk = min(60, wait_seconds)
                    time.sleep(sleep_chunk)
                    wait_seconds -= sleep_chunk
            
            print(f"{GREEN}[AÇÃO]{RESET} Retornando ao workspace e enviando 'continue'...")
            perform_action("continue")
            time.sleep(120)
        else:
            print(f"{GREEN}[OK]{RESET} Sem limites. Nova verificação em 45 segundos...\n")
            time.sleep(45)

def run_queue_loop(allow_screen_off: bool):
    print(f"\n{BOLD}{GREEN}[MODO COM FILA DE PROMPTS INTELIGENTE INICIADO]{RESET} (Desligar tela: {'Sim' if allow_screen_off else 'Não'})\n")
    
    while True:
        ensure_claude_is_active()
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{CYAN}[{timestamp}]{RESET} Verificando status de cota na tela...")
        
        screen_text = find_text_on_screen()
        time_str = parse_return_time(screen_text)
        state = load_state()
        
        if time_str:
            print(f"{RED}[ALERTA]{RESET} Limite atingido! Horário de retorno: {BOLD}{time_str}{RESET}")
            
            now = datetime.now()
            target_time = datetime.strptime(time_str, "%I:%M %p").replace(
                year=now.year, month=now.month, day=now.day
            )
            if target_time < now:
                target_time += timedelta(days=1)
            
            human_fuzz_delay = random.randint(65, 180)
            wait_seconds = (target_time - now).total_seconds() + human_fuzz_delay
            
            print(f"{YELLOW}[ESPERA]{RESET} Aguardando {BOLD}{int(wait_seconds // 60)}{RESET} minutos...")
            
            if allow_screen_off and wait_seconds > 120:
                turn_off_screen()
                time.sleep(max(0, wait_seconds - 15))
                wake_up_screen()
                time.sleep(15)
            else:
                while wait_seconds > 0:
                    sleep_chunk = min(60, wait_seconds)
                    time.sleep(sleep_chunk)
                    wait_seconds -= sleep_chunk
            
            print(f"{GREEN}[AÇÃO]{RESET} Retornando ao workspace após limite...")
            # Se atingiu limite, significa que a resposta foi cortada. Mandamos 'continue' para terminar a resposta atual.
            perform_action("continue")
            time.sleep(120)
        else:
            # Sem limites no momento. Verificamos se havia um prompt ativo anterior que acabou de terminar
            if state.get("active_prompt"):
                print(f"{GREEN}[FILA]{RESET} Resposta completa finalizada para o prompt anterior! Avançando na fila...")
                save_state({"active_prompt": None})
            
            # Se não há prompt ativo, pega o próximo da fila se existir
            if not state.get("active_prompt"):
                queue = load_queue()
                if queue:
                    next_p = get_next_prompt()
                    save_state({"active_prompt": next_p})
                    print(f"{CYAN}[FILA]{RESET} Lançando novo prompt da fila: {next_p}")
                    perform_action(next_p)
                    time.sleep(60)
                else:
                    print(f"{GREEN}[OK]{RESET} Fila vazia e sem limites. Nova verificação em 45 segundos...\n")
                    time.sleep(45)
            else:
                print(f"{GREEN}[OK]{RESET} Aguardando conclusão da resposta atual...\n")
                time.sleep(45)

def ask_screen_preference():
    print(f"\n{BOLD}Configuração de Energia:{RESET}")
    print("1. Desligar a tela automaticamente durante as esperas longas")
    print("2. Manter a tela ligada o tempo todo")
    sub_choice = input(f"{CYAN}Escolha (1 ou 2): {RESET}").strip()
    return sub_choice == "1"

def menu():
    while True:
        print(f"\n{BOLD}{MAGENTA}=== Claude Ghost Configuration Panel v10 ==={RESET}")
        print("1. Modo Clássico (Apenas 'Continue' automático)")
        print("2. Modo com Fila de Prompts (Lança prompt e usa 'continue' até concluir)")
        print("3. Adicionar Prompt à Fila")
        print("4. Ver Fila de Prompts")
        print("5. Sair")
        
        choice = input(f"\n{CYAN}Escolha uma opção (1 a 5): {RESET}").strip()
        
        if choice == "1":
            allow_off = ask_screen_preference()
            run_classic_loop(allow_screen_off=allow_off)
            break
        elif choice == "2":
            allow_off = ask_screen_preference()
            run_queue_loop(allow_screen_off=allow_off)
            break
        elif choice == "3":
            prompt_text = input(f"{CYAN}Digite o texto do prompt a adicionar na fila: {RESET}").strip()
            if prompt_text:
                add_prompt(prompt_text)
            else:
                print(f"{RED}Prompt vazio, não adicionado.{RESET}")
        elif choice == "4":
            show_queue()
        elif choice == "5":
            print(f"{CYAN}Saindo... Até mais!{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}[ERRO] Opção inválida. Tente novamente.{RESET}")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[!] Execução interrompida pelo usuário (Ctrl + C).{RESET}")
        try:
            subprocess.run(["xset", "dpms", "force", "on"], check=True)
        except:
            pass
        print(f"{CYAN}Monitor reativado com segurança. Até mais!{RESET}\n")
        sys.exit(0)
