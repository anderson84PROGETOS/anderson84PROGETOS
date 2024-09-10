import scapy.all as scapy
from ipaddress import ip_network
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from mac_vendor_lookup import AsyncMacLookup
import webbrowser
import asyncio

# Função assíncrona para buscar o fabricante
async def async_lookup_mac(mac_address, mac_lookup):
    try:
        return await mac_lookup.lookup(mac_address)
    except KeyError:
        return "Desconhecido"

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
        # Obtendo o fabricante a partir do endereço MAC
        vendor = asyncio.run(async_lookup_mac(received.hwsrc, mac_lookup))
        
        # Adicionando o endereço IP, o endereço MAC, o fabricante aos resultados
        results.append((received.psrc, received.hwsrc, vendor, "Ativo 👨‍💻"))

def scan_network(network, progress_bar, progress_label):
    results = []
    mac_lookup = AsyncMacLookup()

    # Inicializando o banco de dados de fornecedores
    asyncio.run(mac_lookup.update_vendors())

    # Calculando o número total de IPs na rede para a barra de progresso
    total_ips = network.num_addresses
    progress_step = 100 / total_ips

    threads = []
    for i, ip in enumerate(network, start=1):
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
    network_address = entry.get()
    try:
        network = ip_network(network_address, strict=False)
    except ValueError:
        result_label.config(text="Endereço de rede inválido!")
        return

    progress_bar['value'] = 0    
    progress_label.config(text="Iniciando escaneamento...")    
    scan_results = scan_network(network, progress_bar, progress_label)
    result_label.config(text="Escaneamento concluído!")

    for row in hosts_tree.get_children():
        hosts_tree.delete(row)

    for ip, mac, vendor, status in scan_results:
        hosts_tree.insert("", tk.END, values=(status, ip, mac, vendor))

def save_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                                             title="Salvar Resultados")
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("Status\t\tEndereço IP\t\tEndereço MAC\t\t\tFabricante\n\n")
            for row in hosts_tree.get_children():
                values = hosts_tree.item(row, "values")
                file.write("\t\t".join(values) + "\n")
        result_label.config(text=f"Resultados salvos em {file_path}")


def open_link(event):
    selected_item = hosts_tree.selection()[0]
    ip_address = hosts_tree.item(selected_item, "values")[1]
    webbrowser.open(f"http://{ip_address}")

# Criando a janela principal
root = tk.Tk()
root.title("Network Scanner")
root.geometry("1120x830")

# Interface gráfica
entry_label = tk.Label(root, text="Endereço de Rede", font=("TkDefaultFont", 11, "bold"))
entry_label.pack(pady=5)
entry = tk.Entry(root, width=30, font=("TkDefaultFont", 11, "bold"))
entry.insert(0, "192.168.0.1/24")
entry.pack(pady=5)

scan_button = tk.Button(root, text="Iniciar Escaneamento", command=start_scan, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
scan_button.pack(pady=10)

save_button = tk.Button(root, text="Salvar Resultados", command=save_results, bg="#07edf5", font=("TkDefaultFont", 11, "bold"))
save_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.pack(pady=5)

progress_label = tk.Label(root, text="", font=("TkDefaultFont", 11, "bold"))
progress_label.pack(pady=5)

style = ttk.Style()
style.configure("Treeview", font=("TkDefaultFont", 11))
style.configure("Treeview.Heading", font=("TkDefaultFont", 11, "bold"))

# Adicionando colunas (Status, IP, MAC, Fabricante)
hosts_tree = ttk.Treeview(root, columns=("Status", "IP", "MAC", "Fabricante"), show="headings")
hosts_tree.heading("Status", text="Status", anchor=tk.W)
hosts_tree.heading("IP", text="Endereço IP", anchor=tk.W)
hosts_tree.heading("MAC", text="Endereço MAC", anchor=tk.W)
hosts_tree.heading("Fabricante", text="Fabricante", anchor=tk.W)
hosts_tree.pack(pady=10)

# Configurando a largura das colunas para organizar melhor os dados
hosts_tree.column("Status", width=100, anchor=tk.W)
hosts_tree.column("IP", width=200, anchor=tk.W)
hosts_tree.column("MAC", width=200, anchor=tk.W)
hosts_tree.column("Fabricante", width=380, anchor=tk.W)
hosts_tree.configure(height=25)

result_label = tk.Label(root, text="", font=("TkDefaultFont", 11, "bold"))
result_label.pack(pady=5)

hosts_tree.bind("<Double-1>", open_link)

root.mainloop()
