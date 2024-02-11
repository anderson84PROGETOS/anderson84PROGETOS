import socket
import tkinter as tk
from tkinter import messagebox

# Função para enviar solicitação HEAD
def send_head_request(site, portas, output_text):
    for porta in portas:
        try:
            porta = int(porta.strip())  # Remove espaços em branco
            with socket.create_connection((site, porta), timeout=5) as conn:
                conn.sendall(b"HEAD / HTTP/1.1\r\nHost: " + site.encode() + b"\r\nConnection: close\r\n\r\n")
                response = conn.recv(4096).decode()
                output_text.insert(tk.END, f"\nResposta da porta {porta}\n\n{response}")
        except Exception as e:
            output_text.insert(tk.END, f"\nAcesso Proibido:403 Forbidden ao acessar a porta {porta}: {e}")

def enviar_solicitacao():
    site = site_entry.get()
    portas_input = porta_entry.get()

    if not site:
        messagebox.showerror("Erro", "Você não forneceu um nome de site válido.")
        return

    portas = portas_input.split(',')  # Separa a entrada em uma lista de portas

    for porta in portas:
        try:
            porta = int(porta.strip())  # Remove espaços em branco
            if porta < 1 or porta > 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Número de porta inválido.")
            return

    send_head_request(site, portas, output_text)

# Configuração da interface gráfica
root = tk.Tk()
root.title("Envio de Solicitação HEAD")
root.wm_state('zoomed')

site_label = tk.Label(root, text="Digite o Nome do Website", font=("TkDefaultFont", 12, "bold"))
site_label.pack(pady=1)

site_entry = tk.Entry(root, width=30, font=("TkDefaultFont", 12, "bold"))
site_entry.pack(pady=3)

porta_label = tk.Label(root, text="Número Portas 1 a 65535 (ex: 21, 22, 23 ou só uma Porta 80 )", font=("TkDefaultFont", 12, "bold"))
porta_label.pack()

porta_entry = tk.Entry(root, width=50, font=("TkDefaultFont", 12, "bold"))
porta_entry.pack()

enviar_button = tk.Button(root, text="Enviar Solicitação", command=enviar_solicitacao, bg="#0cf2e3", font=("TkDefaultFont", 11, "bold"))
enviar_button.pack(pady=10)

output_text = tk.Text(root, width=130, height=40, font=("TkDefaultFont", 12, "bold"))
output_text.pack()

root.mainloop()
