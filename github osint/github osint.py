from email.mime import base
import json
import requests
import binascii
import re
from requests.auth import HTTPBasicAuth
import sys
import base64
from colorama import init, Fore, Style

# Variáveis globais
saida_json = {}
saida = []
emails_encontrados = []

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ███████╗██╗███╗   ██╗████████╗
██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║   ██║███████╗██║██╔██╗ ██║   ██║   
██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║   ██║╚════██║██║██║╚██╗██║   ██║   
╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╔╝███████║██║██║ ╚████║   ██║   
 ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝ 
""")

def encontrar_repos_do_usuario(nome_usuario):
    try:
        resposta = requests.get(f'https://api.github.com/users/{nome_usuario}/repos?per_page=100&sort=pushed').text
        repos = re.findall(r'"full_name":"%s/(.*?)",.*?"fork":(.*?),' % nome_usuario, resposta)
        repos_nao_forkados = []
        for repo in repos:
            if repo[1] == 'false':
                repos_nao_forkados.append(repo[0])
        return repos_nao_forkados
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao buscar repositórios: {e}")
        return []

def encontrar_email_do_contribuidor(nome_usuario, repo, contribuidor):
    try:
        resposta = requests.get(f'https://github.com/{nome_usuario}/{repo}/commits?author={contribuidor}', 
                               auth=HTTPBasicAuth(nome_usuario, '')).text
        ultimo_commit = re.search(r'href="/%s/%s/commit/(.*?)"' % (nome_usuario, repo), resposta)
        commit_id = ultimo_commit.group(1) if ultimo_commit else 'dummy'
        detalhes_commit = requests.get(f'https://github.com/{nome_usuario}/{repo}/commit/{commit_id}.patch', 
                                      auth=HTTPBasicAuth(nome_usuario, '')).text
        email = re.search(r'<(.*)>', detalhes_commit)
        if email:
            emails_encontrados.append(email.group(1))
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao buscar email do contribuidor: {e}")

def encontrar_email_do_usuario(nome_usuario):
    repos = encontrar_repos_do_usuario(nome_usuario)
    for repo in repos:
        encontrar_email_do_contribuidor(nome_usuario, repo, nome_usuario)

def encontrar_chaves_publicas_do_usuario(nome_usuario):
    try:
        resposta_gpg = requests.get(f'https://github.com/{nome_usuario}.gpg').text
        resposta_ssh = requests.get(f'https://github.com/{nome_usuario}.keys').text
        if "hasn't uploaded any GPG keys" not in resposta_gpg:
            saida.append(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[+] Chaves_GPG : https://github.com/{nome_usuario}.gpg')
            saida_json['Chaves_GPG'] = f'https://github.com/{nome_usuario}.gpg'
            regex_pgp = re.compile(r"-----BEGIN [^-]+-----([A-Za-z0-9+\/=\s]+)-----END [^-]+-----", re.MULTILINE)
            correspondencias = regex_pgp.findall(resposta_gpg)
            if correspondencias:
                b64 = base64.b64decode(correspondencias[0])
                hx = binascii.hexlify(b64)
                id_chave = hx.decode()[48:64]
                saida.append(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[+] ID_chave_GPG : {id_chave}')
                saida_json['ID_chave_GPG'] = id_chave
                emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", b64.decode('Latin-1'))
                for email in emails:
                    emails_encontrados.append(email)
        if resposta_ssh.strip():
            saida.append(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[+] Chaves_SSH : https://github.com/{nome_usuario}.keys')
            saida_json['Chaves_SSH'] = f'https://github.com/{nome_usuario}.keys'
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao buscar chaves públicas: {e}")

def encontrar_info_do_usuario(nome_usuario):
    try:
        url = f'https://api.github.com/users/{nome_usuario}'
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            for i in dados:
                if i in ['login', 'id', 'avatar_url', 'name', 'blog', 'location', 'twitter_username', 
                         'email', 'company', 'bio', 'public_gists', 'public_repos', 'followers', 
                         'following', 'created_at', 'updated_at']:
                    if dados[i] is not None and dados[i] != '':
                        if i == 'email':
                            emails_encontrados.append(dados[i])
                        saida_json[i] = dados[i]
                        saida.append(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[+] {i} : {dados[i]}')
            saida_json['public_gists'] = f'https://gist.github.com/{nome_usuario}'
            saida.append(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[+] public_gists : https://gist.github.com/{nome_usuario}')
            return True
        elif resposta.status_code == 404:
            saida_json['erro'] = 'nome de usuário não existe'
            return False
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro na API: Status {resposta.status_code}")
            return False
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao buscar informações do usuário: {e}")
        return False

def encontrar_usuario_por_email(email):
    try:
        url = f'\nhttps://api.github.com/search/users?q={email}+in:email'
        resposta = requests.get(url)
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados.get('total_count', 0) > 0:
                nome_usuario = dados['items'][0]['login']
                saida.append(Fore.LIGHTGREEN_EX + Style.BRIGHT + f'\n[+] nome_usuario : {nome_usuario}')
                saida_json['nome_usuario'] = nome_usuario
                # Busca informações adicionais do usuário, incluindo email
                usuario_existe = encontrar_info_do_usuario(nome_usuario)
                if usuario_existe:
                    encontrar_email_do_usuario(nome_usuario)
                    encontrar_chaves_publicas_do_usuario(nome_usuario)
            else:
                saida.append(Fore.LIGHTRED_EX + Style.BRIGHT + f'\n[-] nome_usuario : Não encontrado')
                saida_json['nome_usuario'] = 'Não encontrado'
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro na API: Status {resposta.status_code}")
            saida.append(Fore.LIGHTRED_EX + Style.BRIGHT + f'\n[-] nome_usuario : Erro na busca')
            saida_json['nome_usuario'] = 'Erro na busca'
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao buscar usuário por email: {e}")
        saida.append(Fore.LIGHTRED_EX + Style.BRIGHT + f'\n[-] nome_usuario : Erro na busca')
        saida_json['nome_usuario'] = 'Erro na busca'

def principal():
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Escolha uma opção\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "u - Buscar por nome de usuário do GitHub   exemplo: 32123132")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "e - Buscar por email")
    
    escolha = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite sua escolha (u/e): ").strip().lower()

    if escolha == 'u':
        nome_usuario = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o nome de usuário do GitHub: ").strip()
        print("")
        if not nome_usuario:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: O nome de usuário não pode estar vazio")
            sys.exit(1)
            
        usuario_existe = encontrar_info_do_usuario(nome_usuario)
        if usuario_existe:
            encontrar_email_do_usuario(nome_usuario)
            encontrar_chaves_publicas_do_usuario(nome_usuario)
            for dado in saida:
                print(dado)
            if emails_encontrados:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + '\n[+] email :', end='')
                for email in list(set(emails_encontrados)):
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f'{email}', end='')
                print()
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + 'Nome de usuário não existe')

    elif escolha == 'e':
        email = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o endereço de email: ").strip()
        if not email:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: O email não pode estar vazio")
            sys.exit(1)
        encontrar_usuario_por_email(email)
        for dado in saida:
            print(dado)
        if emails_encontrados:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + '\n[+] email :', end='')
            for email in list(set(emails_encontrados)):
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f'\n {email}', end='')
            print()

    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Erro: Escolha inválida. Por favor, digite 'u' ou 'e'.")
        sys.exit(1)

if __name__ == '__main__':
    principal()
    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
