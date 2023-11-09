import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import subprocess

def perform_dns_query_and_zone_transfer():
    domain_name = domain_name_entry.get()
    query_output.delete(1.0, tk.END)  # Limpa a área de texto de saída
    query_output.configure(bg='white')  # Define a cor de fundo para branco

    # Execute o comando 'nslookup' para a consulta DNS
    dns_query_commands = ['A', 'CNAME', 'HINFO', 'MB', 'MINFO', 'MG', 'MR', 'MX', 'NS', 'PTR', 'SOA', 'TXT', 'UINFO', 'WKS']

    for command in dns_query_commands:
        dns_query_command = ['nslookup', '-q=' + command, domain_name]
        dns_query_result = subprocess.run(dns_query_command, capture_output=True, text=True, shell=True)
        
        # Exiba o resultado na área de texto de saída
        query_output.insert(tk.END, f'\n ↓↓ Resultados da consulta "{command}" ↓↓\n')
        query_output.insert(tk.END, dns_query_result.stdout)

def clear_results():
    query_output.delete(1.0, tk.END)  # Limpa a área de texto
    query_output.configure(bg='white')  # Define a cor de fundo para branco

# Cria a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Consulta DNS e Transferência de Zona")

# Cria uma aba para a consulta DNS
dns_tab = ttk.Frame(root)
dns_tab.pack()

# Cria um rótulo para o nome de domínio personalizado
domain_name_label = ttk.Label(dns_tab, text="Nome de Domínio", font=('TkDefaultFont', 12, 'bold'))
domain_name_label.pack()

# Cria uma entrada para o nome de domínio com tamanho maior
domain_name_entry = ttk.Entry(dns_tab, width=40, font=('TkDefaultFont', 12, 'bold'))
domain_name_entry.pack()

# Cria um botão para realizar a consulta DNS e a transferência de zona
query_button = ttk.Button(dns_tab, text="Consultar DNS e Transferência de Zona", command=perform_dns_query_and_zone_transfer)
query_button.pack(pady=10)

# Cria uma área de texto para exibir a saída da consulta DNS e da transferência de zona
query_output = scrolledtext.ScrolledText(dns_tab, width=120, height=40, font=('TkDefaultFont', 12, 'bold'))
query_output.pack()

# Cria um botão "Limpar Resultados" com fundo vermelho
clear_button = tk.Button(root, text="Limpar resultados", font=("Arial", 12), command=clear_results, bg="#f54254")
clear_button.pack(pady=10)

# Inicia a interface gráfica
root.mainloop()
