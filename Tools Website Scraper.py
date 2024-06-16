import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from socket import socket, AF_INET, SOCK_STREAM
import re
import subprocess
import webbrowser
from tkinter import scrolledtext, messagebox

# Cabeçalhos padrão para Firefox
user_agent_firefox = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
headers_firefox = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': user_agent_firefox
}

# Cabeçalhos padrão para cURL
user_agent_curl = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
headers_curl = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': user_agent_curl
}

# Lista de comandos
commands = [
    "Usando User Agent do Firefox",
    "Cabeçalhos HTTP (cURL)",
    "Transferência de Zona DNS",
    "Exibir IPv4",
    "Exibir robots.txt",
    "Scraper Web",
    "whois.br",
    "whois.com",
    "Name Servers",
]

# Função para exibir resultados
def display_result(text):
    result_text.insert(tk.END, text + "\n")

def fetch_and_process(url, headers, user_agent_name):
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)
    
    result = f"Status da resposta HTTP ({user_agent_name}): {response.status_code}\n"
    result += f"\n============= Cabeçalhos HTTP ({user_agent_name}) =============\n\n"
    for key, value in response.headers.items():
        result += f"{key}: {value}\n"
    
    if user_agent_name != "CURL":
        soup = BeautifulSoup(response.content, 'html.parser')        
        result += f"\n============= Parágrafos ({user_agent_name}) =============\n"        
        paragraphs = soup.find_all('p')
        for para in paragraphs:
            result += para.get_text() + "\n"
        
        result += f"\n\n============= Links ({user_agent_name}) =============\n"
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href:
                result += f"{text}: {href}\n"
        
        result += f"\n============= Títulos ({user_agent_name}) =============\n"
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for title in titles:
            result += title.get_text().strip() + "\n"
        
        result += f"\n============= Imagens ({user_agent_name}) =============\n"
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            alt = img.get('alt')
            if src:
                result += f"Fonte: {src}, Texto alternativo: {alt}\n"
        
        result += f"\n============= Listas ({user_agent_name}) =============\n"
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                result += item.get_text().strip() + "\n"
        
        result += f"\n============= Tabelas ({user_agent_name}) =============\n"
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                col_texts = [col.get_text().strip() for col in cols]
                result += '\t'.join(col_texts) + "\n"
        
        result += f"\n============= Outros Textos ({user_agent_name}) =============\n"
        other_texts = soup.find_all(string=True)
        for text in other_texts:
            if text.parent.name not in ['script', 'style', 'head', 'title', 'meta', '[document]']:
                content = text.strip()
                if content:
                    result += content + "\n"

    display_result(result)

def requisicao_whois(servidor_whois, endereco_host, padrao):
    print("===================== Whois.br =====================\n")
    result = ""
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':
                objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
        else:
            objeto_socket.send(f'{endereco_host}\r\n'.encode())
        
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            result += dados.decode('latin-1')
    objeto_socket.close()
    display_result(result)

def obter_whois_gov(endereco):    
    servidores_whois_tdl = {'.gov': 'whois.nic.gov'}
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        requisicao_whois(servidor_whois_gov, endereco, False)
    else:
        display_result("Servidor WHOIS para domínios .gov não encontrado.")

def obter_whois_br(endereco):
    servidores_whois_tdl = {'.br': 'whois.registro.br'}
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False)

def obter_whois(endereco):
    print("===================== Whois.com =====================\n")
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            display_result(whois_text)

    if response_registro_br.status_code == 200:
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            display_result(result_text)

def dns_transfer(site):
    result = "========================================== Transferência de Zona DNS ==========================================\n\n"
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    for output in output_list_dns:
        result += output

    display_result(result)

def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def exibir_ipv4(site):
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        result = "========================================== Endereços IPv4 Encontrados ==========================================\n\n"
        for ipv4_address in ipv4_addresses:
            result += ipv4_address + "\n"
        display_result(result)
    else:
        display_result("Nenhum Endereço IPv4 encontrado.")

def exibir_robots_txt(site):
    robots_url = urljoin(site, '/robots.txt')
    response = requests.get(robots_url)
    if response.status_code == 200:
        result = response.text
    else:
        result = f"Erro: Não foi possível acessar {robots_url}. Código de status: {response.status_code}"
    display_result(result)

def open_web_browser(url):
    webbrowser.open(url)

# Função para executar o comando selecionado
def execute_command():
    command = command.get()
    site = site.get()

    if command == "Usando User Agent do Firefox":
        fetch_and_process(site, headers_firefox, "Firefox")
    elif command == "Cabeçalhos HTTP (cURL)":
        fetch_and_process(site, headers_curl, "CURL")
    elif command == "Transferência de Zona DNS":
        dns_transfer(site)
    elif command == "Exibir IPv4":
        exibir_ipv4(site)
    elif command == "Exibir robots.txt":
        exibir_robots_txt(site)
    elif command == "Scraper Web":
        web_scraper(site)  # Chama a função web_scraper para realizar o scraping
    elif command == "whois.br":
        obter_whois_br(site)
    elif command == "whois.com":
        obter_whois(site)
    elif command == "Name Servers":
        # Implementar função para exibir Name Servers (se houver)
        pass
    else:
        messagebox.showerror("Erro", "Comando desconhecido")

# Cabeçalhos padrão para Firefox
user_agent_firefox = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
headers_firefox = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': user_agent_firefox
}

# Cabeçalhos padrão para cURL
user_agent_curl = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
headers_curl = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': user_agent_curl
}

# Função para exibir resultados
def display_result(text):
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, text)
    result_text.config(state=tk.DISABLED)

def fetch_and_process(url, headers, user_agent_name):
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)
    
    result = f"Status da resposta HTTP ({user_agent_name}): {response.status_code}\n\n"
    result += f"============= Cabeçalhos HTTP ({user_agent_name}) =============\n\n"
    for key, value in response.headers.items():
        result += f"{key}: {value}\n"
    
    if user_agent_name != "CURL":
        soup = BeautifulSoup(response.content, 'html.parser')
        
        result += f"\n\n============= Parágrafos ({user_agent_name}) =============\n\n"
        paragraphs = soup.find_all('p')
        for para in paragraphs:
            result += para.get_text() + "\n"
        
        result += f"\n\n============= Links ({user_agent_name}) =============\n\n"
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href:
                result += f"{text}: {href}\n"
        
        result += f"\n\n============= Títulos ({user_agent_name}) =============\n\n"
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for title in titles:
            result += title.get_text().strip() + "\n"
        
        result += f"\n\n============= Imagens ({user_agent_name}) =============\n\n"
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            alt = img.get('alt')
            if src:
                result += f"Fonte: {src}, Texto alternativo: {alt}\n"
        
        result += f"\n\n============= Listas ({user_agent_name}) =============\n\n"
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                result += item.get_text().strip() + "\n"
        
        result += f"\n\n============= Tabelas ({user_agent_name}) =============\n\n"
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                col_texts = [col.get_text().strip() for col in cols]
                result += '\t'.join(col_texts) + "\n"
        
        result += f"\n\n============= Outros Textos ({user_agent_name}) =============\n\n"
        other_texts = soup.find_all(string=True)
        for text in other_texts:
            if text.parent.name not in ['script', 'style', 'head', 'title', 'meta', '[document]']:
                content = text.strip()
                if content:
                    result += content + "\n"

    display_result(result)

# whois .br .com .gov
def requisicao_whois(servidor_whois, endereco_host, padrao):
    result = "===================== Whois.br =====================\n"
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':
                objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
        else:
            objeto_socket.send(f'{endereco_host}\r\n'.encode())
        
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            result += dados.decode('latin-1')
    objeto_socket.close()
    display_result(result)

def obter_whois_gov(endereco):    
    servidores_whois_tdl = {'.gov': 'whois.nic.gov'}
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        requisicao_whois(servidor_whois_gov, endereco, False)
    else:
        display_result("Servidor WHOIS para domínios .gov não encontrado.")

def obter_whois_br(endereco):
    servidores_whois_tdl = {'.br': 'whois.registro.br'}
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False)

def obter_whois(endereco):
    result = "===================== Whois.com =====================\n"
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            result += whois_text

    if response_registro_br.status_code == 200:
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            result += result_text

    display_result(result)

# Transferência de Zona DNS
def dns_transfer(site):
    result = "========================================== Transferência de Zona DNS ==========================================\n\n"
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    for output in output_list_dns:
        result += output

    display_result(result)

# ipv4
def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def exibir_ipv4(site):
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        result = "========================================== Endereços IPv4 Encontrados ==========================================\n\n"
        for ipv4_address in ipv4_addresses:
            result += ipv4_address + "\n"
        display_result(result)
    else:
        display_result("Nenhum Endereço IPv4 encontrado.")

# Conteúdo do robots.txt
def exibir_robots_txt(site):
    robots_url = urljoin(site, '/robots.txt')
    response = requests.get(robots_url, headers=headers_firefox)
    if response.status_code == 200:
        display_result(f"============= Conteúdo do robots.txt =============\n\n{response.text}")
    else:
        display_result(f"Não foi possível acessar o robots.txt (Status: {response.status_code})")

# web_scraper
def web_scraper(url):
    response = requests.get(url, headers=headers_firefox)
    if response.status_code != 200:
        display_result("Erro na URL")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    result = f"================= Web Scraper =================\n\n"
    result += f"Foram Encontrados ====>  {len(subdomains)}  Subdomínios\n\n"
    for subdomain in subdomains:
        result += subdomain + "\n"
    
    links = soup.find_all('a', href=True)
    urls = {link['href'] for link in links if link['href'].startswith('http://') or link['href'].startswith('https://') or link['href'].startswith('/')}
    complete_urls = {urljoin(url, link) if link.startswith('/') else link for link in urls}
    internal_urls = {link for link in complete_urls if urlparse(url).netloc in urlparse(link).netloc}
    
    result += f"\n\nForam Encontradas ====>  {len(internal_urls)}   URL internas\n\n"
    for internal_url in internal_urls:
        result += internal_url + "\n"

    display_result(result)

# Função para obter informações de geolocalização
def obter_informacoes_website(endereco):
    user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}", headers=user_agent)
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                result = "============== Informações sobre o website TECNOLOGIAS e geolocalização  ================\n\n" 
                result += f"\nName Servers: {dados['isp']}\n"               
                result += f"\nIP: {dados['query']}\n\n"
                result += f"\nPaís: {dados['country']}\n"
                result += f"\nCidade: {dados['city']}\n"

            if 'lat' in dados and 'lon' in dados:
                result +=f"\n\nLatitude: {dados['lat']}\n"
                result += f"Longitude: {dados['lon']}\n\n"

                # Obtendo informações adicionais usando o Nominatim
                if 'lat' in dados and 'lon' in dados:
                    lat = dados['lat']
                    lon = dados['lon']
                    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'}
                    endereco_completo = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
                    if endereco_completo.status_code == 200:
                        endereco_completo = endereco_completo.json()
                        result += f"\nNome da Rua: {endereco_completo['display_name']}"
                        google_maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                        result += f"\n\nURL do Google Maps: {google_maps_url}"
                        display_result(result)
                        open_map = messagebox.askyesno("Abrir Mapa", "Abrir o mapa do Google com a geolocalização?")
                        if open_map:
                            webbrowser.open(google_maps_url)  # Abrir o Google Maps no navegador
                        return lat, lon
                    else:
                        display_result(f"\nErro ao obter informações do Nominatim: {endereco_completo.status_code}")
                        return None, None
            else:
                display_result("\nNão foi possível obter informações para este endereço.")
                return None, None
        else:
            display_result(f"\nErro ao obter informações do site: {resposta.status_code}")
            return None, None
    except Exception as e:
        display_result(f"\nOcorreu um erro: {e}")
        return None, None       

# Função para lidar com as opções escolhidas
def handle_choice(choice, url):
    site = url.replace('http://', '').replace('https://', '').split('/')[0]

    if choice == '1':
        fetch_and_process(url, headers_firefox, "Firefox")

    elif choice == '2':
        fetch_and_process(url, headers_curl, "CURL")
    
    elif choice == '3':
        dns_transfer(site)

    elif choice == '4':
        exibir_ipv4(site)

    elif choice == '5':
        exibir_robots_txt(url)

    elif choice == '6':
        web_scraper(url)

    elif choice == '7':
        obter_whois_br(site)

    elif choice == '8':
        obter_whois(site)
        if re.search(r'\.gov$', site):
            obter_whois_gov(site)

    elif choice == '9':
        obter_informacoes_website(site)
        
    else:
        display_result("Opção inválida. Tente novamente.")

def on_button_click(choice):
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return
    handle_choice(choice, url)

# Interface Gráfica com Tkinter
root = tk.Tk()
root.title("Tools Website Scraper")
root.wm_state('zoomed')

frame = tk.Frame(root)
frame.pack(pady=5)

url_label = tk.Label(frame, text="Digite a URL do Website", font=("Arial", 11))
url_label.pack(padx=530, pady=0)

url_entry = tk.Entry(frame, width=40, font=("Arial", 11))
url_entry.pack(padx=3, pady=(0, 3))  # Espaçamento inferior de 10 pixels

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

button_texts = [
    " Usando User Agente do Firefox  ",
    " Cabeçalhos HTTP (cURL) ",
    " Transferência de Zona DNS ",
    " Exibir IPv4 ",
    " Exibir robots.txt ",
    " Scraper Web ",
    " whois.br ",
    " whois.com ",
    " Name Servers "
]

# Criação dos botões com seus respectivos comandos
for i, text in enumerate(button_texts, start=1):
    button = tk.Button(button_frame, text=text, command=lambda i=i: on_button_click(str(i)))
    #button.pack(fill=tk.X)
    button.pack(side=tk.LEFT, padx=10)

# Área de texto para exibir os resultados
result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=125, height=46, font=("Arial", 12))
result_text.pack(padx=60, pady=5, anchor=tk.E)  # Posiciona à direita

result_text.config(state=tk.DISABLED)

# Inicia o loop principal da interface gráfica
root.mainloop()
