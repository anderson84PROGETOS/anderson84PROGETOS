import scapy.all as scapy
from ipaddress import ip_network
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from mac_vendor_lookup import MacLookup
import webbrowser
import time

# Histórico de dispositivos já encontrados
device_history = {}

def get_ip_range_from_network(network_address):
    """Função para obter o intervalo de IPs de uma rede no formato CIDR (ex: 192.168.0.1/24)."""
    try:
        network = ip_network(network_address, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError:
        return []

def get_ip_range_from_range(ip_range):
    """Função para gerar um intervalo de IPs a partir do formato start-end (ex: 192.168.0.1-254)."""
    ips = []
    for range_item in ip_range.split(","):
        start_ip, end_ip = range_item.split("-")
        start_ip_parts = list(map(int, start_ip.split(".")))
        end_ip_parts = list(map(int, end_ip.split(".")))

        if len(start_ip_parts) != 4 or len(end_ip_parts) != 4:
            raise ValueError("Formato inválido de IP. Certifique-se de que ambos os IPs tenham 4 octetos.")
        
        for i in range(start_ip_parts[3], end_ip_parts[3] + 1):
            ips.append(".".join([str(start_ip_parts[0]), str(start_ip_parts[1]), str(start_ip_parts[2]), str(i)]))
    return ips

def scan_ip(ip, results, mac_lookup):
    # Criando um pacote ARP
    arp_request = scapy.ARP(pdst=str(ip))
    # Criando um pacote Ethernet
    ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    # Combinando os pacotes ARP e Ethernet
    packet = ether / arp_request
    # Enviando o pacote e recebendo a resposta
    answered = scapy.srp(packet, timeout=0.5, verbose=0)[0]

    # Processando as respostas
    for sent, received in answered:
        # Obtenha o fabricante a partir do endereço MAC
        try:
            vendor = mac_lookup.lookup(received.hwsrc)
        except KeyError:
            vendor = "Desconhecido"

        # Verificar se o IP já está no histórico
        status = "Online"

        # Adicionando o endereço IP, o endereço MAC, o fabricante e o status aos resultados
        results.append((received.psrc, received.hwsrc, vendor, status))

        # Atualizar o histórico de dispositivos
        device_history[received.psrc] = received.hwsrc

def scan_network(ip_range, progress_bar, progress_label):
    # Criando uma lista para armazenar os resultados do escaneamento
    results = []

    # Inicializando o MacLookup
    mac_lookup = MacLookup()
    mac_lookup.update_vendors()  # Atualizar o banco de dados de fornecedores

    # Calculando o número total de IPs para a barra de progresso
    total_ips = len(ip_range)
    progress_step = 100 / total_ips

    threads = []

    # Percorrendo todos os endereços IP no intervalo
    for i, ip in enumerate(ip_range, start=1):
        # Criar e iniciar uma nova thread para escanear o IP atual
        thread = threading.Thread(target=scan_ip, args=(ip, results, mac_lookup))
        threads.append(thread)
        thread.start()

        # Atualizando a barra de progresso
        progress_bar['value'] += progress_step
        progress_label.config(text=f"Escaneando: {ip}")
        root.update_idletasks()

    # Aguardar todas as threads terminarem
    for thread in threads:
        thread.join()

    return results

def start_scan():
    # Obtendo o intervalo de IP selecionado
    network_address = ip_range_combobox.get()

    try:
        # Verificar se o formato é CIDR (ex: 192.168.0.1/24)
        if "/" in network_address:
            ip_range = get_ip_range_from_network(network_address)
        
        # Verificar se é um formato de intervalo de IPs com um ou mais ranges (ex: 192.168.0.1-254, 192.168.56.1-254)
        elif "-" in network_address:
            ip_range = get_ip_range_from_range(network_address)
        else:
            result_label.config(text="Formato de rede inválido!")
            return
    except ValueError:
        result_label.config(text="Endereço de rede inválido!")
        return

    # Verificar se a lista de IPs está vazia, em caso afirmativo, mostrar mensagem de erro
    if not ip_range:
        result_label.config(text="Não foi possível gerar o intervalo de IPs.")
        return

    # Realizando o escaneamento de rede
    progress_bar['value'] = 0    
    progress_label.config(text="Iniciando escaneamento...")    
    scan_results = scan_network(ip_range, progress_bar, progress_label)

    # Imprimindo os resultados do escaneamento
    result_label.config(text="Escaneamento concluído!")

    # Limpa a árvore antes de adicionar novos resultados
    for row in hosts_tree.get_children():
        hosts_tree.delete(row)

    # Adicionando os resultados ao Treeview
    for ip, mac, vendor, status in scan_results:
        hosts_tree.insert("", tk.END, values=(ip, mac, vendor, status))

def save_results():
    # Abrindo o diálogo para escolher o local e nome do arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                           filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                                           title="Salvar Resultados")
    if file_path:
        with open(file_path, "w") as file:
            # Escrevendo os cabeçalhos no arquivo
            file.write("Endereço IP\t        Endereço MAC\t\t        Fabricante\t        Status\n")
            for row in hosts_tree.get_children():
                values = hosts_tree.item(row, "values")
                file.write("\t\t".join(values) + "\n")
        result_label.config(text=f"Resultados salvos em {file_path}")

def open_ip_in_browser(event):
    # Obtém o item selecionado e o IP associado a ele
    selected_item = hosts_tree.focus()  # Obtém o item selecionado
    if selected_item:  # Se houver um item selecionado
        ip = hosts_tree.item(selected_item, 'values')[0]  # O IP é o primeiro valor
        url = f"http://{ip}"  # Usando o IP diretamente para abrir no navegador
        webbrowser.open(url)  # Abre o IP no navegador

# Criando a janela principal
root = tk.Tk()
root.title("Scanner Network")
root.geometry("1200x920")

# Criando o campo de entrada para o endereço da rede
entry_label = tk.Label(root, text="Escolha o Intervalo de IP", font=("TkDefaultFont", 11, "bold"))
entry_label.pack(pady=5)

# Criando o Combobox para selecionar o intervalo de IP
ip_range_combobox = ttk.Combobox(root, width=30, font=("TkDefaultFont", 11, "bold"))
ip_range_combobox['values'] = [
    "192.168.0.1/24",        
    "192.168.100.1/24",            
]

ip_range_combobox.set("192.168.0.1/24")  # Valor padrão
ip_range_combobox.pack(pady=5)

# Criando o botão para iniciar o escaneamento
scan_button = tk.Button(root, text="Iniciar Escaneamento", command=start_scan, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
scan_button.pack(pady=10)

# Criando o botão para salvar os resultados
save_button = tk.Button(root, text="Salvar Resultados", command=save_results, bg="#07edf5", font=("TkDefaultFont", 11, "bold"))
save_button.pack(pady=10)

# Criando o botão para fechar a aplicação
close_button = tk.Button(root, text="Fechar Tudo", command=root.quit, bg="#f52323", font=("TkDefaultFont", 11, "bold"))
close_button.pack(pady=10)

# Criando a barra de progresso
progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.pack(pady=5)

# Criando o rótulo para mostrar o progresso
progress_label = tk.Label(root, text="", font=("TkDefaultFont", 11, "bold"))
progress_label.pack(pady=5)

# Configurando o estilo do Treeview
style = ttk.Style()
style.configure("Treeview", font=("TkDefaultFont", 11))  # Aplica fonte a todos os itens do Treeview
style.configure("Treeview.Heading", font=("TkDefaultFont", 11, "bold"))

# Criando a árvore para exibir os resultados
hosts_tree = ttk.Treeview(root, columns=("IP", "MAC", "Fabricante", "Status"), show="headings")
hosts_tree.heading("IP", text="Endereço IP", anchor=tk.W)
hosts_tree.heading("MAC", text="Endereço MAC", anchor=tk.W)
hosts_tree.heading("Fabricante", text="Fabricante", anchor=tk.W)
hosts_tree.heading("Status", text="Status", anchor=tk.W)
hosts_tree.pack(pady=10)

# Ajustar largura das colunas
hosts_tree.column("IP", width=300, anchor=tk.W)
hosts_tree.column("MAC", width=300, anchor=tk.W)
hosts_tree.column("Fabricante", width=300, anchor=tk.W)
hosts_tree.column("Status", width=100, anchor=tk.W)

# Ajustar altura da árvore
hosts_tree.configure(height=25)

# Criando o rótulo para exibir mensagens de resultado
result_label = tk.Label(root, text="", font=("TkDefaultFont", 11, "bold"))
result_label.pack(pady=5)

# Adicionando evento de clique duplo para abrir o IP no Google
hosts_tree.bind("<Double-1>", open_ip_in_browser)

# Executando o loop principal da interface gráfica
root.mainloop()
