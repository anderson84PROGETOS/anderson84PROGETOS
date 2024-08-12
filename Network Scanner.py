import scapy.all as scapy
from ipaddress import ip_network
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from mac_vendor_lookup import MacLookup

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

        # Adicionando o endereço IP, o endereço MAC e o fabricante aos resultados
        results.append((received.psrc, received.hwsrc, vendor))

def scan_network(network, progress_bar, progress_label):
    # Criando uma lista para armazenar os resultados do escaneamento
    results = []

    # Inicializando o MacLookup
    mac_lookup = MacLookup()
    mac_lookup.update_vendors()  # Atualizar o banco de dados de fornecedores

    # Calculando o número total de IPs na rede para a barra de progresso
    total_ips = network.num_addresses
    progress_step = 100 / total_ips

    threads = []

    # Percorrendo todos os endereços IP na rede
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
    # Endereço de rede a ser escaneado
    network_address = entry.get()

    try:
        # Convertendo o endereço de rede em um objeto de rede
        network = ip_network(network_address, strict=False)
    except ValueError:
        result_label.config(text="Endereço de rede inválido!")
        return

    # Realizando o escaneamento de rede
    progress_bar['value'] = 0    
    progress_label.config(text="Iniciando escaneamento...")    
    scan_results = scan_network(network, progress_bar, progress_label)

    # Imprimindo os resultados do escaneamento
    result_label.config(text="Escaneamento concluído!")

    # Limpa a árvore antes de adicionar novos resultados
    for row in hosts_tree.get_children():
        hosts_tree.delete(row)

    # Adicionando os resultados ao Treeview
    for ip, mac, vendor in scan_results:
        hosts_tree.insert("", tk.END, values=(ip, mac, vendor))

def save_results():
    # Abrindo o diálogo para escolher o local e nome do arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                           filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                                           title="Salvar Resultados")
    if file_path:
        with open(file_path, "w") as file:
            # Escrevendo os cabeçalhos no arquivo
            file.write("Endereço IP\t        Endereço MAC\t\t        Fabricante\n")
            for row in hosts_tree.get_children():
                values = hosts_tree.item(row, "values")
                file.write("\t\t".join(values) + "\n")
        result_label.config(text=f"Resultados salvos em {file_path}")

# Criando a janela principal
root = tk.Tk()
root.title("Network Scanner")

# Criando o campo de entrada para o endereço da rede
entry_label = tk.Label(root, text="Endereço de Rede", font=("TkDefaultFont", 11, "bold"))
entry_label.pack(pady=5)
entry = tk.Entry(root, width=30, font=("TkDefaultFont", 11, "bold"))  # Definindo a largura do campo de entrada
entry.insert(0, "192.168.0.0/24")  # Valor padrão
entry.pack(pady=5)

# Criando o botão para iniciar o escaneamento
scan_button = tk.Button(root, text="Iniciar Escaneamento", command=start_scan, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
scan_button.pack(pady=10)

# Criando o botão para salvar os resultados
save_button = tk.Button(root, text="Salvar Resultados", command=save_results, bg="#07edf5", font=("TkDefaultFont", 11, "bold"))
save_button.pack(pady=10)

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
hosts_tree = ttk.Treeview(root, columns=("IP", "MAC", "Fabricante"), show="headings")
hosts_tree.heading("IP", text="Endereço IP", anchor=tk.W)
hosts_tree.heading("MAC", text="Endereço MAC", anchor=tk.W)
hosts_tree.heading("Fabricante", text="Fabricante", anchor=tk.W)
hosts_tree.pack(pady=10)

# Ajustar largura das colunas
hosts_tree.column("IP", width=350, anchor=tk.W)
hosts_tree.column("MAC", width=350, anchor=tk.W)
hosts_tree.column("Fabricante", width=350, anchor=tk.W)

# Ajustar altura da árvore
hosts_tree.configure(height=25)

# Criando o rótulo para exibir mensagens de resultado
result_label = tk.Label(root, text="", font=("TkDefaultFont", 11, "bold"))
result_label.pack(pady=5)

# Executando o loop principal da interface gráfica
root.mainloop()
