import tkinter as tk
from tkinter import messagebox, Text

import dns.resolver
import dns.zone
import socket

def consultar_dns():
    domain_name = entry_domain.get()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']  # Use a default DNS server, or replace with your preferred DNS server

    try:
        query1 = resolver.resolve(domain_name, 'NS')
        nameservers = [ns.to_text() for ns in query1]
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, '\n↓↓ Servidores DNS ↓↓\n\n' + '\n'.join(nameservers) + '\n')
    except dns.resolver.NXDOMAIN:
        messagebox.showinfo("Erro", f'O domínio {domain_name} não foi encontrado.')
        return
    except dns.exception.DNSException as e:
        messagebox.showinfo("Erro DNS", f"Erro DNS: {e}")
        return

    nameserver = entry_nameserver.get()
    try:
        try:
            socket.inet_pton(socket.AF_INET, nameserver)
            nameserver_ip = nameserver
        except socket.error:
            nameserver_ip = socket.gethostbyname(nameserver)

        zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain_name))
        result_text.insert(tk.END, '\n↓↓ Saída da consulta de transferência de zona ↓↓\n\n')
        for name, node in zone.nodes.items():
            try:
                result_text.insert(tk.END, f"{name} {node.to_text(name)}\n")
            except AttributeError:
                result_text.insert(tk.END, f"NoData exception for {name}\n")
    except Exception as e:
        pass  # Evita a exibição de mensagens de erro ao conectar ao servidor DNS

def limpar_resultados():
    result_text.delete(1.0, tk.END)

def copiar_texto():
    root.clipboard_clear()
    root.clipboard_append(result_text.get(1.0, tk.END))
    root.update()

# Cria a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("Consulta DNS")

# Cria os elementos na janela
label_domain = tk.Label(root, text="Digite o nome do website que deseja consultar:", fg='black', font=('TkDefaultFont', 11, 'bold'))
entry_domain = tk.Entry(root, width=50, font=('TkDefaultFont', 11, 'bold'))
label_nameserver = tk.Label(root, text="Insira um servidor de nomes para a transferência de zona:", fg='black', font=('TkDefaultFont', 11, 'bold'))
entry_nameserver = tk.Entry(root, width=50, font=('TkDefaultFont', 11, 'bold'))
button_consultar = tk.Button(root, text="Consultar", command=consultar_dns, bg='#00FFFF', fg='black', font=('TkDefaultFont', 11, 'bold'))
button_limpar = tk.Button(root, text="Limpar Resultados", command=limpar_resultados, bg='#FF0000', font=('TkDefaultFont', 11, 'bold'))
button_copiar = tk.Button(root, text="Copiar Tudo", command=copiar_texto, bg='#07f29c')
result_text = Text(root, height=38, width=155, fg='black', font=('TkDefaultFont', 11, 'bold'))

# Organiza os elementos na janela
label_domain.pack(pady=5)
entry_domain.pack(pady=5)
label_nameserver.pack(pady=5)
entry_nameserver.pack(pady=5)
button_consultar.pack(pady=10)
button_limpar.pack(pady=5)
button_copiar.pack(pady=5)
result_text.pack()

# Inicia o loop principal da aplicação
root.mainloop()
