import re
import requests
from bs4 import BeautifulSoup
import webbrowser
from socket import socket, gethostbyname
import sys

print("""

██████╗  ██████╗ ██████╗ ██╗  ██╗    ██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ███████╗███╗   ███╗ █████╗ ██╗██╗     
██╔══██╗██╔═══██╗██╔══██╗██║ ██╔╝    ██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔════╝████╗ ████║██╔══██╗██║██║     
██║  ██║██║   ██║██████╔╝█████╔╝     ██║ █╗ ██║███████║██║   ██║██║███████╗    █████╗  ██╔████╔██║███████║██║██║     
██║  ██║██║   ██║██╔══██╗██╔═██╗     ██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║     
██████╔╝╚██████╔╝██║  ██║██║  ██╗    ╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗
╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝     ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝
                                                                                                                                                                                                                                                                                                   
""")

# Dicionário com servidores WHOIS por TLD
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.gov': 'whois.nic.gov',
}

def google_dork(site_name):
    # Gerar o Google Dork
    query = f"site:{site_name} email"
    
    # Exibir o Google Dork gerado na tela
    print(f"\n\nGoogle Dork gerado: site:{site_name} email")
    
    # Criar a URL de pesquisa do Google
    search_url = f"https://www.google.com/search?q={query}"
    
    # Simular cabeçalhos de um navegador para evitar bloqueios
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Fazer o pedido HTTP para o Google (pode ser bloqueado)
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        # Usar BeautifulSoup para analisar o HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar os links da página de resultados
        links = soup.find_all('a', href=True)
        
        print("\n==============================================")
        print("\nE-mails Encontrados nos links\n")
        found_emails = set()  # Usando um conjunto para evitar duplicatas
        
        # Buscar por e-mails nos links encontrados
        for link in links:
            href = link['href']
            # Verificar se o link contém um e-mail
            if 'mailto:' in href:
                email = href.split('mailto:')[1].strip().lower()  # Normalizar e-mail
                found_emails.add(email)
        
        # Buscar e-mails diretamente no conteúdo da página usando regex
        emails_in_page = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", soup.text)
        
        # Adicionar e-mails encontrados na página ao conjunto
        for email in emails_in_page:
            email_normalizado = email.strip().lower()  # Normalizar e-mail
            found_emails.add(email_normalizado)

        # Exibir os e-mails encontrados
        if found_emails:
            for email in found_emails:
                print(f"Email: {email}")
        else:
            print("\nNenhum email encontrado nos resultados")
    else:
        print("\nErro ao acessar a página de pesquisa do Google")

def whois_query(domain):
    # Determinar o TLD do domínio
    tld = domain.split('.')[-1]
    whois_server = servidores_whois_tdl.get(f'.{tld}', None)
    
    if not whois_server:
        print(f"\nServidor WHOIS não encontrado para o domínio {domain}")
        return

    # Obter o endereço IP do servidor WHOIS
    ip_whois = gethostbyname(whois_server)
    
    # Conectar ao servidor WHOIS
    s = socket()
    s.settimeout(10)
    s.connect((ip_whois, 43))
    
    # Enviar consulta WHOIS
    s.send((domain + "\r\n").encode())
    
    # Receber resposta como bytes
    response = s.recv(4096)
    s.close()
    
    # Tentar decodificar a resposta usando codificação 'latin-1', que pode lidar com caracteres especiais
    try:
        response_text = response.decode('latin-1')
    except UnicodeDecodeError:
        print("\nErro ao decodificar a resposta WHOIS")
        return
    
    # Extrair e-mails da resposta WHOIS usando regex
    emails_in_whois = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response_text)
    
    # Exibir os e-mails encontrados no WHOIS
    if emails_in_whois:
        print("\n==============================================")
        print("\nE-mails Encontrados no WHOIS\n")
        for email in emails_in_whois:
            print(f"Email: {email}")
    else:
        print("\nNenhum email encontrado no WHOIS")

if __name__ == "__main__":
    # Solicitar o nome do website
    site_name = input("\nDigite o nome do website: ")
    
    # Chamar a função para gerar o Google Dork e fazer o scraping
    google_dork(site_name)
    
    # Consultar WHOIS do domínio para encontrar e-mails
    whois_query(site_name)

    # Perguntar ao usuário se deseja abrir o Google em um navegador
    print("\n==============================================")
    user_input = input("\nDeseja acessar o site de pesquisa do Google? (s/n): ").lower()
    
    if user_input == 's':
        # Abrir a busca no Google se a resposta for 's'
        search_url = f"https://www.google.com/search?q=site:{site_name} email"  # Garantir que a URL de pesquisa está correta
        webbrowser.open(search_url)
        print("\nAbrindo o site no seu navegador...")
    else:
        print("\nPesquisa não será aberta.")

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
