import tkinter as tk
from tkinter import ttk
import socket
import threading

def scan_ports():
    target_ip = entry.get()
    start_port = int(start_port_entry.get())
    end_port = int(end_port_entry.get())

    open_ports = []
    total_ports = end_port - start_port + 1

    progress_var.set(0)  # Inicializa o valor da barra de progresso

    def update_progress():
        try:
            target_ip = socket.gethostbyname(entry.get())
            device_list.insert(0, f"IP do Website: {target_ip}")
        except socket.gaierror:
            device_list.insert(0, "Não foi possível obter o IP do Website")

        for port in range(start_port, end_port + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target_ip, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
            progress = (port - start_port + 1) / total_ports * 100
            progress_var.set(progress)  # Atualiza o valor da barra de progresso

        device_list.delete(1, tk.END)
        if open_ports:
            for port in open_ports:
                device_list.insert(tk.END, f"Porta aberta: {port}")
            
        else:
            device_list.insert(tk.END, "Nenhuma porta aberta encontrada")

    # Cria uma thread para executar a verificação de portas sem bloquear a interface
    scan_thread = threading.Thread(target=update_progress)
    scan_thread.start()

def clear_listbox():
    device_list.delete(0, tk.END)

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
label_start_port.grid(row=1, column=1, padx=(300, 0), pady=10)  # Ajustado o valor de padx

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

# Aumentar o tamanho da fonte no Listbox
font = ('Helvetica', 12)  # Altere o tamanho da fonte conforme necessário

# Aumentar o número de linhas na Listbox
device_list = tk.Listbox(window, width=95, font=font, height=38)  # Defina o valor de height para o número desejado de linhas
device_list.grid(row=2, column=0, padx=10, pady=10, columnspan=6)

# Barra de progresso
progress_var = tk.DoubleVar()
style = ttk.Style()
style.theme_use('default')
style.configure('green.Horizontal.TProgressbar', background='#00FF00')
progress_bar = ttk.Progressbar(window, orient=tk.HORIZONTAL, mode='determinate', variable=progress_var, style='green.Horizontal.TProgressbar', length=500)
progress_bar.place(x=160, y=160)

window.mainloop()

