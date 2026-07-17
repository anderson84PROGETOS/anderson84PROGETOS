import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
from datetime import datetime
import os
import hashlib
import webbrowser

class MonitorLentidao:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 Monitor de Lentidão em Tempo Real 🔎")
        self.root.geometry("1480x740")
        self.root.state("zoomed")
        self.root.minsize(1380, 680)
        self.root.configure(bg="#1e1e1e")

        self.paused = False
        self.auto_atualizando = False
        self.contador = 5
        self.contador_label = None

        # Título
        titulo = tk.Label(self.root, text="Monitor de Lentidão - Tempo Real", 
                         font=("Arial", 18, "bold"), fg="#00ff00", bg="#1e1e1e")
        titulo.pack(pady=10)

        # Frame superior
        frame_topo = tk.Frame(self.root, bg="#1e1e1e")
        frame_topo.pack(fill="x", padx=15, pady=5)

        self.label_status = tk.Label(frame_topo, text="Pressione 'Atualizar Agora' para começar", 
                                    fg="#ffff00", bg="#1e1e1e", font=("Arial", 10))
        self.label_status.pack(side="left", padx=5)

        # Contador
        self.contador_label = tk.Label(frame_topo, text="Próxima atualização em: 5s", 
                                      fg="#00ffff", bg="#1e1e1e", font=("Arial", 11, "bold"))
        self.contador_label.pack(side="left", padx=20)

        # Botões
        btn_frame = tk.Frame(frame_topo, bg="#1e1e1e")
        btn_frame.pack(side="right")

        self.btn_pause = tk.Button(btn_frame, text="⏸ Pausar", command=self.toggle_pause,
                                  bg="#444", fg="white", font=("Arial", 9), width=10, state="disabled")
        self.btn_pause.pack(side="left", padx=5)

        self.btn_atualizar = tk.Button(btn_frame, text="🔄 Atualizar Agora", command=self.iniciar_atualizacao,
                                      bg="#0066cc", fg="white", font=("Arial", 9), width=18)
        self.btn_atualizar.pack(side="left", padx=5)

        self.btn_salvar = tk.Button(btn_frame, text="💾 Salvar TXT", command=self.salvar_resultados,
                                   bg="#228b22", fg="white", font=("Arial", 9), width=15)
        self.btn_salvar.pack(side="left", padx=5)

        # ==================== TABELA ====================
        frame_tabela = tk.Frame(self.root, bg="#1e1e1e")
        frame_tabela.pack(fill="both", expand=True, padx=15, pady=8)

        colunas = ("Programa", "PID", "CPU%", "Memória%", "Memória MB", "Disco KB/s", 
                  "Disco%", "Status", "Threads", "Criado", "SHA-256", "Caminho")

        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings")
        
        self.tree.heading("Programa", text="Programa")
        self.tree.heading("PID", text="PID")
        self.tree.heading("CPU%", text="CPU%")
        self.tree.heading("Memória%", text="Memória%")
        self.tree.heading("Memória MB", text="Memória MB")
        self.tree.heading("Disco KB/s", text="Disco KB/s")
        self.tree.heading("Disco%", text="Disco%")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Threads", text="Threads")
        self.tree.heading("Criado", text="Criado")
        self.tree.heading("SHA-256", text="SHA-256")
        self.tree.heading("Caminho", text="Caminho Completo")

        self.tree.column("Programa", width=220, anchor="w")
        self.tree.column("PID", width=70, anchor="center")
        self.tree.column("CPU%", width=80, anchor="center")
        self.tree.column("Memória%", width=90, anchor="center")
        self.tree.column("Memória MB", width=100, anchor="center")
        self.tree.column("Disco KB/s", width=100, anchor="center")
        self.tree.column("Disco%", width=80, anchor="center")
        self.tree.column("Status", width=90, anchor="center")
        self.tree.column("Threads", width=70, anchor="center")
        self.tree.column("Criado", width=110, anchor="center")
        self.tree.column("SHA-256", width=450, anchor="w")
        self.tree.column("Caminho", width=1000, anchor="w")

        v_scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)

        # Menu e binds
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="🔍 Abrir no VirusTotal", command=self.abrir_virustotal)

        self.tree.bind("<Button-3>", self.mostrar_menu)
        self.tree.bind("<Double-1>", self.abrir_pasta)

        # Rodapé
        rodape = tk.Label(
            self.root,
            text="Atualização automática a cada 5 segundos • Botão direito → VirusTotal • 💾 Salvar TXT",
            bg="#2b2b2b",
            fg="#c0c0c0",
            font=("Arial", 9),
            relief="sunken",
            anchor="center"
        )
        rodape.pack(side="bottom", fill="x", ipady=6)

        # Estilo
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d")

        self.root.bind("<Escape>", lambda e: self.root.quit())
        self.root.protocol("WM_DELETE_WINDOW", self.root.quit())

    def salvar_resultados(self):
        try:
            items = self.tree.get_children()
            if not items:
                messagebox.showinfo("Aviso", "Não há dados na tabela para salvar.")
                return

            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
                title="Salvar relatório como",
                initialfile=f"monitor_lentidao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if not filepath:
                return

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=== MONITOR DE LENTIDÃO - RELATÓRIO ===\n\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(f"Total de processos: {len(items)}\n\n")
                f.write("=" * 90 + "\n\n")

                for idx, item in enumerate(items, 1):
                    valores = self.tree.item(item, "values")
                    
                    f.write(f"[{idx:02d}] {'='*80}\n")
                    f.write(f"Programa     : {valores[0]}\n")
                    f.write(f"PID          : {valores[1]}\n")
                    f.write(f"CPU%         : {valores[2]}\n")
                    f.write(f"Memória%     : {valores[3]}\n")
                    f.write(f"Memória MB   : {valores[4]}\n")
                    f.write(f"Disco KB/s   : {valores[5]}\n")
                    f.write(f"Disco%       : {valores[6]}%\n")
                    f.write(f"Status       : {valores[7]}\n")
                    f.write(f"Threads      : {valores[8]}\n")
                    f.write(f"Criado       : {valores[9]}\n")
                    f.write(f"SHA-256      : {valores[10]}\n")
                    f.write(f"Caminho      : {valores[11]}\n")
                    f.write("=" * 90 + "\n\n")

                f.write("=== FIM DO RELATÓRIO ===\n")

            messagebox.showinfo("✅ Sucesso", f"Relatório salvo com sucesso!\n\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.config(text="▶ Retomar", bg="#d35400")
        else:
            self.btn_pause.config(text="⏸ Pausar", bg="#444")

    def iniciar_atualizacao(self):
        self.btn_atualizar.config(state="disabled")
        self.auto_atualizando = True
        self.btn_pause.config(state="normal")
        self.contador = 5
        self._realizar_atualizacao()

    def atualizar_contador(self):
        if not self.auto_atualizando or self.paused:
            return
        if self.contador > 0:
            self.contador -= 1
            self.contador_label.config(text=f"Próxima atualização em: {self.contador}s")
            self.root.after(1000, self.atualizar_contador)
        else:
            self.contador = 5
            self._realizar_atualizacao()

    def _realizar_atualizacao(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            processos = self.obter_processos()

            for proc in processos:
                tag = "alta" if proc[2] > 25 else "media" if proc[2] > 10 else "normal"
                self.root.after(0, lambda p=proc, t=tag: self.tree.insert("", "end", values=p, tags=(t,)))

            self.root.after(0, lambda: self.tree.tag_configure("alta", background="#440000", foreground="#ff7777"))
            self.root.after(0, lambda: self.tree.tag_configure("media", background="#333300", foreground="#ffff77"))
            self.root.after(0, lambda: self.tree.tag_configure("normal", background="#2d2d2d", foreground="white"))

            self.root.after(0, lambda: self.label_status.config(
                text=f"Atualizado • {len(processos)} processos • {datetime.now().strftime('%H:%M:%S')}", 
                fg="#00ff88"))
        except Exception as e:
            self.root.after(0, lambda: self.label_status.config(text=f"Erro: {str(e)}", fg="red"))
        finally:
            self.root.after(0, lambda: self.btn_atualizar.config(state="normal"))
            self.root.after(0, self.atualizar_contador)

    def obter_processos(self, top=25):
        processos = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                         'memory_info', 'io_counters', 'status', 'num_threads', 
                                         'create_time', 'exe']):
            try:
                info = proc.info
                memoria_mb = info.get('memory_info').rss / (1024**2) if info.get('memory_info') else 0
                io = info.get('io_counters')
                
                disco_kb = (io.read_bytes + io.write_bytes) / 1024 if io else 0
                
                # === ESTIMATIVA DE PORCENTAGEM DE DISCO ===
                disco_percent = 0.0
                if io and (io.read_bytes > 0 or io.write_bytes > 0):
                    activity = (io.read_bytes + io.write_bytes) / 1024 / 1024
                    disco_percent = min(95.0, round(activity % 100, 1))

                criado = datetime.fromtimestamp(info['create_time']).strftime('%H:%M:%S') if info.get('create_time') else '-'
                caminho = info.get('exe', 'Não disponível') or 'Não disponível'
                
                sha256 = self.calcular_sha256(caminho)

                processos.append((
                    info['name'][:45],
                    info['pid'],
                    round(info.get('cpu_percent', 0), 1),
                    round(info.get('memory_percent', 0), 1),
                    round(memoria_mb, 1),
                    round(disco_kb, 1),
                    disco_percent,
                    info.get('status', '-'),
                    info.get('num_threads', 0),
                    criado,
                    sha256,
                    caminho
                ))
            except:
                continue

        processos.sort(key=lambda x: x[2], reverse=True)
        return processos[:top]

    def calcular_sha256(self, filepath):
        if not os.path.isfile(filepath):
            return "Não disponível"
        try:
            with open(filepath, "rb") as f:
                hash_sha = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha.update(chunk)
            return hash_sha.hexdigest()
        except:
            return "Não calculado"

    def mostrar_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def abrir_virustotal(self):
        selection = self.tree.selection()
        if not selection:
            return
        valores = self.tree.item(selection[0], "values")
        if len(valores) > 10:
            hash_val = valores[10]
            if hash_val not in ["Não disponível", "Não calculado"]:
                url = f"https://www.virustotal.com/gui/file/{hash_val}"
                try:
                    webbrowser.open(url)
                except:
                    messagebox.showerror("Erro", "Não foi possível abrir o navegador.")
            else:
                messagebox.showinfo("Aviso", "Hash não disponível para este arquivo.")

    def abrir_pasta(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        col = self.tree.identify_column(event.x)
        valores = self.tree.item(item, "values")
        
        if col == "#12" and len(valores) > 11:
            caminho = valores[11]
            if os.path.exists(caminho) and caminho != "Não disponível":
                try:
                    pasta = os.path.dirname(caminho)
                    if os.path.exists(pasta):
                        os.startfile(pasta)
                except:
                    pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MonitorLentidao()
    app.run()
