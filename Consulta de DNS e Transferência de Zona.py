import tkinter as tk
from tkinter import scrolledtext, messagebox
import dns.resolver
import dns.zone
import socket
import subprocess  # Adicionando a importação do módulo subprocess

def perform_dns_lookup(query_type, nameserver=None):
    website = entry_website.get()
    
    try:
        # Se o tipo de consulta for "NS", use o último argumento como o servidor de nomes
        if query_type == "NS" and nameserver:
            command = ['nslookup', '-type=ns', website,]
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

def consultar_transferencia_zona():
    domain_name = entry_website.get()  # Obtendo o nome do domínio
    
    # Definir o cabeçalho de agente do usuário
    user_agent = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
    
    # Criar um resolver personalizado
    resolver = dns.resolver.Resolver()
    
    # Configurar o cabeçalho de agente do usuário no resolver
    resolver.headers = {'User-Agent': user_agent}
    
    try:
        # Perform 'nslookup' command for the first query
        query1 = resolver.resolve(domain_name, 'NS')
        nameservers = [ns.to_text() for ns in query1]
    except dns.resolver.NXDOMAIN:
        messagebox.showerror("Erro", f"O domínio {domain_name} não foi encontrado")
        return
    except dns.exception.DNSException as e:
        messagebox.showerror("Erro DNS", str(e))
        return
    
    # Print the output of the first query
    nameservers_text = "\n".join(nameservers)
    output_text.set(nameservers_text)
    
    # Flag to check if zone transfer is found
    zone_transfer_found = False
    
    # Collecting zone transfer data
    zone_text = ""
    
    # Iterate over all nameservers to perform zone transfer
    for nameserver in nameservers:
        try:
            # Check if the input is an IP address, if not, resolve it to an IP address
            try:
                socket.inet_pton(socket.AF_INET, nameserver)
                nameserver_ip = nameserver
            except socket.error:
                nameserver_ip = socket.gethostbyname(nameserver)
    
            zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain_name))
            zone_transfer_found = True
            zone_text += f"\n\n↓↓ Saída da consulta de transferência de zona para o servidor:  {nameserver} \n\n\n"
            for name, node in zone.nodes.items():
                try:
                    zone_text += f"{name} {node.to_text(name)}\n"
                except AttributeError:
                    zone_text += f"NoData exception for {name}\n"
        except dns.exception.FormError as e:
            pass  # Ignore FormError
        except dns.exception.DNSException as e:
            pass  # Ignore other DNS exceptions
    
    # Check if zone transfer is not found and print a message
    if zone_transfer_found:
        # Concatenating all results into a single string
        all_results = f"Resultado da consulta de DNS\n\n{nameservers_text}\n\n{zone_text}"
        
        # Displaying the concatenated results
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, all_results)
        result_text.config(state=tk.DISABLED)
    else:
        messagebox.showinfo("Informação", "Transferência de Zona não Encontrada")

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
        "CNAME": "Mapeia um nome de domínio para outro nome de domínio, frequentemente usado para criar alias.",
        "HINFO": "Armazena informações sobre o tipo de hardware e sistema operacional de um host.",
    }
    return query_descriptions.get(query_type, "Descrição não disponível")

# Criando a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Consulta de DNS e Transferência de Zona")

# Criar e posicionar widgets
label_website = tk.Label(root, text="Digite o nome do website", font=("TkDefaultFont", 11, "bold"))
label_website.pack(pady=(10, 0))

entry_website = tk.Entry(root, width=50, font=("TkDefaultFont", 11, "bold"))
entry_website.pack(pady=(0, 10))

frame_dns = tk.Frame(root)
frame_dns.pack()

button_frame_dns = tk.Frame(frame_dns)
button_frame_dns.pack()

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
    ("CNAME", "Mapeia um nome de domínio para outro nome de domínio, frequentemente usado para criar alias."),
    ("HINFO", "Armazena informações sobre o tipo de hardware e sistema operacional de um host."),
]

# Criando botões para cada tipo de consulta DNS
for index, (query_type, description) in enumerate(dns_queries):
    button = tk.Button(button_frame_dns, text=query_type, command=lambda q=query_type: perform_dns_lookup(q), font=("TkDefaultFont", 11, "bold"))
    button.grid(row=0, column=index, padx=5)

# Botão para enviar uma requisição HTTP HEAD
button_http_head = tk.Button(button_frame_dns, text="HTTP HEAD", command=send_http_head_request, bg="#fc9003", font=("TkDefaultFont", 11, "bold"))
button_http_head.grid(row=0, column=len(dns_queries), padx=5)

# Botão para transferência de zona
transferencia_button = tk.Button(button_frame_dns, text="Transferência de Zona", command=consultar_transferencia_zona, bg="#00FF00", font=("TkDefaultFont", 11, "bold"))
transferencia_button.grid(row=0, column=len(dns_queries)+1, padx=5)

# Widget para exibir resultados
scrollbar_dns = tk.Scrollbar(root)
result_text = scrolledtext.ScrolledText(root, height=43, width=130, font=("TkDefaultFont", 12, "bold"))
result_text.pack(pady=10)

# Configurando a barra de rolagem
scrollbar_dns.config(command=result_text.yview)
result_text.config(yscrollcommand=scrollbar_dns.set)

# Definindo as configurações de estilo para o texto da descrição da consulta DNS
result_text.tag_config('description', foreground='red')

# Impede que o usuário edite o campo de texto de resultado
result_text.config(state=tk.DISABLED)

# Criando frame para a consulta de transferência de zona
frame_transferencia = tk.Frame(root)
frame_transferencia.pack(padx=10, pady=10)

output_text = tk.StringVar()
output_label = tk.Label(frame_transferencia, textvariable=output_text, wraplength=500, justify="left")
output_label.grid(row=1, column=0, columnspan=3, pady=10)

# Iniciar a aplicação
root.mainloop()
