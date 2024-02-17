import re
import requests

print("""

    ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗    ██╗ ██████╗ 
    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗   ██║██╔═══██╗
    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝   ██║██║   ██║
    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗   ██║██║   ██║
    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║██╗██║╚██████╔╝
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝╚═╝ ╚═════╝ 
                                                                       
                                                                                                        
""")

def extract_emails(text):
    # Expressão regular para encontrar endereços de e-mail
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Encontrar todos os endereços de e-mail no texto usando a expressão regular
    emails = re.findall(email_regex, text)

    return emails

def search_domain(domain, api_key):
    url_api = f'https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}'
    response = requests.get(url_api)
    data = response.json()
    if data['data']['emails']:
        return [email['value'] for email in data['data']['emails']]
    else:
        return []

def save_api_key(api_key):
    with open('api_key.txt', 'w') as file:
        file.write(api_key)

def load_api_key():
    try:
        with open('api_key.txt', 'r') as file:
            api_key = file.read().strip()
    except FileNotFoundError:
        api_key = ''
    return api_key

if __name__ == "__main__":
    # Perguntar ao usuário se deseja alterar a API Key
    print("\n cria um arquivo chamado api_key.txt coloque a chava API dentro do arquivo ==> api_key.txt")
    change_api_key = input("\nDeseja Trocar a API Key? (s/n) Nao Tem API acesse o site: https://hunter.io/users/sign_in |Tiver API Só Apertar[ENTER]: ").lower()
    if change_api_key == 's':
        api_key = input("Digite a nova API Key: ")
        print(f"api_key = {api_key}")
        save_api_key(api_key)
    else:
        api_key = load_api_key()
        if not api_key:
            api_key = ''  # Chave padrão
            print("API Key não encontrada. Usando chave padrão.")
        else:
            print(f"api_key = {api_key}")

    # Solicitar ao usuário a URL do website
    url = input("\nDigite a URL do website (incluindo 'http://' ou 'https://'): ")

    # Verificar se a URL fornecida começa com 'http://' ou 'https://'
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url

    # Obter o conteúdo HTML do site
    response = requests.get(url)
    html_content = response.text

    # Extrair endereços de e-mail do conteúdo HTML
    extracted_emails = extract_emails(html_content)

    # Imprimir os endereços de e-mail extraídos
    print("\n↓ Endereços de e-mail encontrados no site ↓\n")
    for email in extracted_emails:
        print(email)

    # Extrair endereços de e-mail associados ao domínio
    domain = url.split('/')[2]
    domain_emails = search_domain(domain, api_key)
    if domain_emails:
        print("\n↓ Endereços de e-mail associados ao domínio ↓\n")
        for email in domain_emails:
            print(email)
    else:
        print("\nNenhum endereço de e-mail associado ao domínio foi encontrado")

input("\nFIM APERTE ENTER PARA SAIR\n")
