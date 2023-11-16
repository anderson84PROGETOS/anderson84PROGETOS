import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading

class PortScannerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Scanner de Portas")

        # Criar e posicionar os widgets na janela
        self.label_host = tk.Label(master, text="Host:", font=('TkDefaultFont', 11, 'bold'))
        self.label_host.grid(row=0, column=0, padx=5, pady=10, sticky=tk.E)

        self.entry_host = tk.Entry(master, font=('TkDefaultFont', 12, 'bold'))
        self.entry_host.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        self.label_start_port = tk.Label(master, text="Porta Inicial:", font=('TkDefaultFont', 11, 'bold'))
        self.label_start_port.grid(row=1, column=0, padx=5, pady=10, sticky=tk.E)

        self.entry_start_port = tk.Entry(master, font=('TkDefaultFont', 11, 'bold'))
        self.entry_start_port.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        self.label_end_port = tk.Label(master, text="Porta Final:", font=('TkDefaultFont', 11, 'bold'))
        self.label_end_port.grid(row=2, column=0, padx=5, pady=10, sticky=tk.E)

        self.entry_end_port = tk.Entry(master, font=('TkDefaultFont', 11, 'bold'))
        self.entry_end_port.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        self.scan_button = tk.Button(master, text="Escanear Portas", command=self.scan_ports, background='#00FFFF', font=('TkDefaultFont', 11, 'bold'))
        self.scan_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Botão para Limpar
        self.clear_button = tk.Button(master, text="Limpar", command=self.clear_results, background='#fa6e37', font=('TkDefaultFont', 11, 'bold'))
        self.clear_button.grid(row=6, column=0, columnspan=2, pady=10)

        # Barra de Progresso
        self.progress_var = tk.DoubleVar()
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('green.Horizontal.TProgressbar', background='#00FF00')
        self.progress_bar = ttk.Progressbar(master, orient=tk.HORIZONTAL, mode='determinate', variable=self.progress_var, style='green.Horizontal.TProgressbar', length=668)
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)

        self.result_text = scrolledtext.ScrolledText(master, width=110, height=32, fg='black', font=('TkDefaultFont', 12, 'bold'))
        self.result_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)

    def scan_ports(self):
        host = self.entry_host.get()
        start_port = int(self.entry_start_port.get())
        end_port = int(self.entry_end_port.get())

        # Limpar a área de resultados antes de iniciar uma nova varredura
        self.result_text.delete(1.0, tk.END)

        # Criar uma nova thread para a varredura
        scan_thread = threading.Thread(target=self.scan_ports_thread, args=(host, start_port, end_port))
        scan_thread.start()

    def scan_ports_thread(self, host, start_port, end_port):
        open_ports = []

        for port in range(start_port, end_port + 1):
            # Verificar outras portas
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
                # Exibir o resultado após cada verificação
                result_str = f"As seguintes portas estão abertas:  {port}\n"
                self.result_text.insert(tk.END, result_str)
            sock.close()

            # Atualizar a barra de progresso
            progress_value = (port - start_port + 1) / (end_port - start_port + 1) * 100
            self.progress_var.set(progress_value)
            self.master.update_idletasks()

        if not open_ports:
            result_str = "Nenhuma porta aberta encontrada.\n"
            self.result_text.insert(tk.END, result_str)

    def clear_results(self):
        # Limpar a área de resultados e a barra de progresso
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_state('zoomed')
    app = PortScannerApp(root)
    root.mainloop()
