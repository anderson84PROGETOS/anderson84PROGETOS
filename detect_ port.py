import tkinter as tk
from tkinter import ttk
import socket
import threading
from tkinter import filedialog  # Importe o módulo para lidar com a caixa de diálogo do sistema de arquivos

def scan_ports():
    target_ip = entry.get()
    start_port = int(start_port_entry.get())
    end_port = int(end_port_entry.get())

    open_ports = []
    total_ports = end_port - start_port + 1

    def update_progress():
        try:
            target_ip = socket.gethostbyname(entry.get())
            device_list.insert(0, f"IP do Website: {target_ip}")
            # Adicionar uma linha em branco
            device_list.insert(tk.END, "")
        except socket.gaierror:
            device_list.insert(0, "Não foi possível obter o IP do Website")

        for port in range(start_port, end_port + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target_ip, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
                try:
                    # Tente obter o nome do serviço associado à porta
                    service_info = socket.getservbyport(port)
                    if port == 22 and service_info == 'ssh':
                        device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: SSH")
                    elif port == 21 and service_info == 'ftp':
                        device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: ftp")
                    elif port == 23 and service_info == 'telnet':
                        device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: Telnet")
                    elif port == 25 and service_info == 'smtp':
                        device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: smtpd")    
                    elif port == 53 and service_info == 'domain':
                        device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: DNS")                            
                    else:
                        device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: {service_info}")
                    try:
                        # Tente se conectar ao serviço e receber os dados de banner
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        sock.connect((target_ip, port))
                        banner = sock.recv(1024).decode('utf-8').strip()
                        device_list.insert(tk.END, f"  Serviço: {banner}")
                        sock.close()
                    except (socket.timeout, UnicodeDecodeError):
                        device_list.insert(tk.END, "  Serviço: Desconhecido")
                except (OSError, KeyError):
                    device_list.insert(tk.END, f"Porta {port} - Status: Aberta - Serviço: Desconhecido")
                # Adicionar uma linha em branco
                device_list.insert(tk.END, "")

            progress = (port - start_port + 1) / total_ports * 100
            progress_var.set(progress)  # Atualiza o valor da barra de progresso
            window.update()

        if not open_ports:
            device_list.insert(tk.END, "Nenhuma porta aberta encontrada")

    # Limpe a lista de dispositivos
    device_list.delete(0, tk.END)

    # Cria uma thread para executar a verificação de portas sem bloquear a interface
    scan_thread = threading.Thread(target=update_progress)
    scan_thread.start()

def clear_listbox():
    device_list.delete(0, tk.END)

def save_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            for item in device_list.get(0, tk.END):
                file.write(item + "\n")

window = tk.Tk()
window.wm_state('zoomed')
window.title("Port Scanner")

frame = ttk.LabelFrame(window, text="Scan Ports")
frame.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W + tk.E)

label_ip = ttk.Label(frame, text="Digite o nome do Website:")
label_ip.grid(row=0, column=0, padx=10, pady=10)

entry = ttk.Entry(frame, width=50)
entry.grid(row=0, column=1, padx=10, pady=10)

label_start_port = ttk.Label(frame, text="Port inicial:")
label_start_port.grid(row=1, column=1, padx=(300, 0), pady=10)

start_port_entry = ttk.Entry(frame, width=10)
start_port_entry.grid(row=1, column=2, padx=10, pady=10)

label_end_port = ttk.Label(frame, text="Port final:")
label_end_port.grid(row=1, column=3, padx=10, pady=10)

end_port_entry = ttk.Entry(frame, width=10)
end_port_entry.grid(row=1, column=4, padx=10, pady=10)

scan_button = ttk.Button(frame, text="Scan Ports", command=scan_ports)
scan_button.grid(row=1, column=5, padx=10, pady=10)

clear_all_button = ttk.Button(frame, text='Clear All', command=clear_listbox)
clear_all_button.grid(row=2, column=5, padx=10, pady=10)

save_results_button = ttk.Button(frame, text="Salvar Resultados", command=save_results)
save_results_button.grid(row=3, column=5, padx=10, pady=10)

# Aumentar o tamanho da fonte no Listbox
font = ('Helvetica', 12)

# Aumentar o número de linhas na Listbox
device_list = tk.Listbox(window, width=95, font=font, height=38)
device_list.grid(row=2, column=0, padx=10, pady=10, columnspan=6)

# Barra de progresso
progress_var = tk.DoubleVar()
style = ttk.Style()
style.theme_use('default')
style.configure('green.Horizontal.TProgressbar', background='#00FF00')
progress_bar = ttk.Progressbar(window, orient=tk.HORIZONTAL, mode='determinate', variable=progress_var, style='green.Horizontal.TProgressbar', length=500)
progress_bar.place(x=207, y=207)

window.mainloop()
