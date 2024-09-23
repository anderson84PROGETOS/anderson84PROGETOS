import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from scapy.all import sniff, wrpcap
import threading

# Variável global para controle da captura
capturing = False
captured_packets = []  # Lista para armazenar pacotes capturados

# Função de callback para processar pacotes capturados
def packet_callback(packet):
    global captured_packets
    packet_info = packet.summary() + "\n\n"
    text_area.insert(tk.END, packet_info)
    text_area.see(tk.END)  # Rolagem automática para o final
    captured_packets.append(packet)  # Adiciona o pacote à lista

# Função para capturar pacotes
def capture_packets():
    global capturing
    capturing = True   
    while capturing:
        # Captura pacotes TCP e UDP, incluindo TLS e QUIC (HTTP/3)
        sniff(iface=None, prn=packet_callback, filter="tcp or (udp and port 443)", store=0, timeout=1)

# Função para iniciar a captura em uma nova thread
def start_capture():
    start_button.config(bg="orange", state="disabled")  # Muda a cor do botão e desabilita
    stop_button.config(state="normal")  # Habilita o botão de parar
    capture_thread = threading.Thread(target=capture_packets)
    capture_thread.daemon = True  # Permite que o thread seja encerrado quando a janela for fechada
    capture_thread.start()

# Função para parar a captura
def stop_capture():
    global capturing
    capturing = False
    start_button.config(bg="#13f007", state="normal")  # Restaura a cor do botão e habilita
    stop_button.config(state="disabled")  # Desabilita o botão de parar

# Função para salvar o conteúdo da área de texto
def save_content():
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                   filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(text_area.get(1.0, tk.END))  # Salva todo o texto
            messagebox.showinfo("Sucesso", "Conteúdo salvo com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")

# Função para salvar pacotes no formato PCAPNG
def save_pcapng():
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".pcapng", 
                                                   filetypes=[("PCAPNG files", "*.pcapng"), ("All files", "*.*")])
        if file_path:
            wrpcap(file_path, captured_packets)  # Salva os pacotes capturados no arquivo PCAPNG
            messagebox.showinfo("Sucesso", "Pacotes salvos com sucesso no formato PCAPNG!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("Captura de Pacotes")

# Botão para iniciar a captura
start_button = tk.Button(root, text="Iniciar Captura", command=start_capture, bg="#13f007")
start_button.pack(pady=5)

# Botão para parar a captura
stop_button = tk.Button(root, text="Parar Captura", command=stop_capture, state="disabled", bg="#f3f70f")
stop_button.pack(pady=5)

# Botão para salvar conteúdo
save_button = tk.Button(root, text="Salvar Texto", command=save_content, bg="#fa8787")
save_button.pack(pady=5)

# Botão para salvar pacotes no formato PCAPNG
save_pcapng_button = tk.Button(root, text="Salvar PCAPNG", command=save_pcapng, bg="#03f4fc")
save_pcapng_button.pack(pady=5)

# Área de texto para exibir pacotes
text_area = scrolledtext.ScrolledText(root, width=150, height=48)
text_area.pack(padx=10, pady=10)

# Iniciar o loop da interface gráfica
root.mainloop()
