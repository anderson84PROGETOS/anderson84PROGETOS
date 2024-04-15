import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import dns.resolver
import dns.query
import dns.zone
import warnings

# Desativar avisos de depreciação globalmente
warnings.filterwarnings("ignore", category=DeprecationWarning)

def dns_zone_xfer(domain_name, result_text):
    result_text.config(state=tk.NORMAL)  # Habilitar a edição do campo de texto de resultado
    result_text.delete(1.0, tk.END)  # Limpar o texto anterior
    try:
        ns_answer = dns.resolver.query(domain_name, 'NS')
        for server in ns_answer:
            result_text.insert(tk.END, f"[*] Found NS: {server}\n")
            ip_answer = dns.resolver.query(str(server.target), 'A')
            for ip in ip_answer:
                result_text.insert(tk.END, f"[*] {server.target}   IP: {ip}\n")
                try:
                    zone = dns.zone.from_xfr(dns.query.xfr(str(ip), domain_name))
                    for host in zone:
                        result_text.insert(tk.END, f"[*] Found Host: {host}\n")
                except Exception as e:
                    result_text.insert(tk.END, f"[*] NS {server} refused zone transfer!\n")
                    continue
    except dns.exception.DNSException as e:
        messagebox.showerror("Error", f"Error occurred during DNS query: {e}")
    result_text.config(state=tk.DISABLED)  # Desabilitar a edição do campo de texto de resultado após a conclusão

def execute_zone_transfer():
    domain_name = entry_website.get()
    if domain_name:
        result_text.delete(1.0, tk.END)  # Limpa o texto anterior
        dns_zone_xfer(domain_name, result_text)
    else:
        messagebox.showwarning("Warning", "Please enter a domain name.")

def perform_dns_lookup(query_type, nameserver=None):
    website = entry_website.get()
    ns = entry_ns.get()  # Obter o nome do servidor de nomes (NS) a partir da entrada do usuário
    try:
        # Se o tipo de consulta for "NS", use o último argumento como o servidor de nomes
        if query_type == "NS" and nameserver:
            command = ['nslookup', '-type=ns', website, ns]
        else:
            # Construindo o comando nslookup com o tipo de consulta e, opcionalmente, o servidor de nomes
            command = ['nslookup', '-type=' + query_type]
            if nameserver:
                command.append(nameserver)
            command.append(website)

        # Executando o comando
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Exibindo o resultado com a descrição da consulta DNS
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"Resultado da consulta: {query_type} \n\n{result.stdout}")
        result_text.insert(tk.END, f"\n\nDescrição da consulta: {query_type} \n", 'description')  # Tag de estilo 'description'
        result_text.insert(tk.END, get_query_description(query_type) + '\n', 'description')  # Tag de estilo 'description'
        result_text.config(state=tk.DISABLED)
    except subprocess.CalledProcessError as e:
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"Erro ao obter informações de DNS: {e}")
        result_text.config(state=tk.DISABLED)

def send_http_head_request():
    website = entry_website.get()
    user_agent = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
    try:
        # Executando o comando curl com o cabeçalho HTTP HEAD e o agente do usuário especificado
        result = subprocess.run(['curl', '-I', '-A', user_agent, website], capture_output=True, text=True)
        
        # Exibindo o resultado
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, result.stdout)
        result_text.config(state=tk.DISABLED)
    except subprocess.CalledProcessError as e:
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"Erro ao enviar requisição HTTP HEAD: {e}")
        result_text.config(state=tk.DISABLED)

def get_query_description(query_type):
    # Função para obter a descrição de uma consulta DNS pelo tipo
    query_descriptions = {
        "A": "Mapeia um nome de domínio para um endereço IPv4.",
        "AAAA": "Mapeia um nome de domínio para um endereço IPv6.",
        "ANY": "Retorna todos os registros de todos os tipos conhecidos pelo servidor de nomes. Se o servidor de nomes não tiver nenhuma informação sobre o nome.\n",
        "NS": "Define os servidores de nomes autorizados para um domínio.",
        "PTR": "É usado para fazer uma pesquisa inversa, mapeando um endereço IP para um nome de domínio.",
        "TXT": "Armazena texto associado a um nome de domínio, frequentemente usado para informações de autenticação e políticas de segurança.",
        "MX": "Define os servidores de email que recebem mensagens de email para um domínio.",
        "SOA": "Contém informações sobre a zona de autoridade de um domínio, como o endereço de email do administrador.",
        "DS": "É usado em registros DNSSEC para prover informações de segurança sobre a zona.",
        "SRV": "Define serviços disponíveis em um domínio, frequentemente usados para localizar servidores de chat, voip.",
        "NSEC3": "É um registro de negação de autenticação usado para reforçar a segurança no DNSSEC.",
        "HINFO": "Armazena informações sobre o tipo de hardware e sistema operacional de um host.",
        "CNAME": "Mapeia um nome de domínio para outro nome de domínio, frequentemente usado para criar alias.",
        

    }
    return query_descriptions.get(query_type, "Descrição não disponível")

# Criando a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Zone Transfer DNS")

# Centralizando a janela principal
window_width = 800
window_height = 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_coordinate = (screen_width / 2) - (window_width / 2)
y_coordinate = (screen_height / 2) - (window_height / 2)
root.geometry(f"{window_width}x{window_height}+{int(x_coordinate)}+{int(y_coordinate)}")

# Componentes da interface gráfica
label_website = tk.Label(root, text="Digite o nome do website", font=("TkDefaultFont", 11, "bold"))
label_website.pack()

entry_website = tk.Entry(root, width=50, font=("TkDefaultFont", 11, "bold"))
entry_website.pack(pady=10)

label_ns = tk.Label(root, text="Digite o nome do servidor de nomes (TYPE=NS)", font=("TkDefaultFont", 11, "bold"))
label_ns.pack()

entry_ns = tk.Entry(root, width=50, font=("TkDefaultFont", 11, "bold"))
entry_ns.pack(pady=10)

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# Lista de tipos de consulta DNS
dns_queries = [
    ("A", "Mapeia um nome de domínio para um endereço IPv4."),
    ("AAAA", "Mapeia um nome de domínio para um endereço IPv6."),
    ("ANY", "Retorna todos os registros de todos os tipos conhecidos pelo servidor de nomes. Se o servidor de nomes não tiver nenhuma informação sobre o nome."),
    ("NS", "Define os servidores de nomes autorizados para um domínio."),
    ("PTR", "É usado para fazer uma pesquisa inversa, mapeando um endereço IP para um nome de domínio."),
    ("TXT", "Armazena texto associado a um nome de domínio, frequentemente usado para informações de autenticação e políticas de segurança."),
    ("MX", "Define os servidores de email que recebem mensagens de email para um domínio."),
    ("SOA", "Contém informações sobre a zona de autoridade de um domínio, como o endereço de email do administrador."),
    ("DS", "É usado em registros DNSSEC para prover informações de segurança sobre a zona."),
    ("SRV", "Define serviços disponíveis em um domínio, frequentemente usados para localizar servidores de chat, voip."),
    ("NSEC3", "É um registro de negação de autenticação usado para reforçar a segurança no DNSSEC."),
    ("HINFO", "Armazena informações sobre o tipo de hardware e sistema operacional de um host."),
    ("CNAME", "Mapeia um nome de domínio para outro nome de domínio, frequentemente usado para criar alias.")
]

# Criando botões para cada tipo de consulta DNS
for query_type, description in dns_queries:
    button = tk.Button(button_frame, text=query_type, command=lambda q=query_type: perform_dns_lookup(q), font=("TkDefaultFont", 11, "bold"))
    button.pack(side=tk.LEFT, padx=5)

# Botão adicional para consulta DNS com o tipo "NS"
button_ns = tk.Button(button_frame, text="TYPE=NS", command=lambda: perform_dns_lookup("NS", entry_ns.get()), bg="#03f4fc", font=("TkDefaultFont", 11, "bold"))
button_ns.pack(side=tk.LEFT, padx=5)

# Botão para enviar uma requisição HTTP HEAD
button_http_head = tk.Button(button_frame, text="HTTP HEAD", command=send_http_head_request, bg="#fc9003", font=("TkDefaultFont", 11, "bold"))
button_http_head.pack(side=tk.LEFT, padx=5)

# Botão para realizar a transferência de zona
button_zone_transfer = tk.Button(button_frame, text="Perform Zone Transfer", command=execute_zone_transfer, bg="#00FF00", font=("TkDefaultFont", 11, "bold"))
button_zone_transfer.pack(side=tk.LEFT, padx=5)

scrollbar = tk.Scrollbar(root)
result_text = scrolledtext.ScrolledText(root, height=42, width=145, font=("TkDefaultFont", 11, "bold"))
result_text.pack()

# Configurando a barra de rolagem
scrollbar.config(command=result_text.yview)
result_text.config(yscrollcommand=scrollbar.set)

# Definindo as configurações de estilo para o texto da descrição da consulta DNS
result_text.tag_config('description', foreground='red')

# Impede que o usuário edite o campo de texto de resultado
result_text.config(state=tk.DISABLED)

# Loop principal da interface gráfica
root.mainloop()
