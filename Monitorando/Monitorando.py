import pyautogui
import time
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

# Nome do arquivo de log
LOG_FILE = "Monitoramento.txt"

# Exibe o banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"""
███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗  █████╗ ███╗   ██╗██████╗  ██████╗ 
████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔═══██╗
██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝███████║██╔██╗ ██║██║  ██║██║   ██║
██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗██╔══██║██║╚██╗██║██║  ██║██║   ██║
██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝╚██████╔╝
╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝ 
""")

def log_to_file(content):
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(content + "\n")

def get_active_website():
    try:
        # Obtém o título da janela ativa diretamente
        window_title = pyautogui.getActiveWindow().title
        
        # Lista de navegadores comuns para filtrar
        browsers = ["Mozilla Firefox", "Google Chrome", "Microsoft Edge", "Safari", "Opera"]
        
        # Lista de programas para ignorar (como editores de código)
        ignore_list = ["Visual Studio Code", "PyCharm", "C:\\WINDOWS\\py.exe", "Program Manager"]
        
        # Verifica se a janela ativa é um programa da ignore_list
        for ignore in ignore_list:
            if ignore in window_title:
                return None  # Retorna None para não exibir nada
        
        # Tenta identificar o site apenas se for um navegador
        for browser in browsers:
            if browser in window_title:
                possible_site = window_title.replace(f" - {browser}", "").strip()
                return {"type": "site", "title": possible_site}  # Retorna como site
        
        # Se não for navegador nem ignorado, retorna como programa
        return {"type": "program", "title": window_title}
    except:
        return None  # Retorna None se não houver janela ativa

def main():
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Monitorando o site ativo      Pressione Ctrl+C para parar\n")
    log_to_file("==== INÍCIO DO MONITORAMENTO ====\n")
    last_site = ""
    
    while True:
        result = get_active_website()
        
        # Só exibe se o resultado mudou e não for None
        if result is not None:
            current_title = result["title"]
            if current_title != last_site:
                if result["type"] == "site":
                    message = f"Você está visitando: {current_title}"
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + message)
                elif result["type"] == "program":
                    message = f"Você está usando: {current_title}"
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + message)
                
                log_to_file(message)
                last_site = current_title
        
        # Pequena pausa para não sobrecarregar o sistema
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:        
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nMonitoramento Encerrado.")

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
