import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter import filedialog
import win32evtlog
import win32evtlogutil
import threading
import datetime

LOGS = ["Security", "System", "Application", "Setup"]

class EventViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("EVENT VIEWER - VISUALIZADOR DE LOGS DO WINDOWS")
        self.root.geometry("1550x860")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")

        # ==================== ESTILO HACKER VERDE ====================
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", 
                       background="#0f0f0f", 
                       foreground="#00ff00", 
                       fieldbackground="#0f0f0f",
                       font=("Consolas", 10))
        
        style.configure("Treeview.Heading", 
                       background="#1a1a1a", 
                       foreground="#00ff00", 
                       font=("Consolas", 11, "bold"))
        
        style.map("Treeview", 
                 background=[('selected', '#003300')],
                 foreground=[('selected', '#00ff88')])

        # Título
        title = tk.Label(root, text="EVENT VIEWER - VISUALIZADOR DE LOGS DO WINDOWS", 
                        font=("Consolas", 18, "bold"), 
                        fg="#00ff00", bg="#0a0a0a")
        title.pack(pady=8)

        # Contador de Eventos
        self.count_label = tk.Label(root, text="Eventos carregados: 0", 
                                   font=("Consolas", 12, "bold"), 
                                   fg="#00ff88", bg="#0a0a0a")
        self.count_label.pack(pady=2)

        # Barra superior
        top = tk.Frame(root, bg="#0a0a0a")
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Log:", font=("Consolas", 11), 
                fg="#00ff00", bg="#0a0a0a").pack(side="left")

        self.log_var = tk.StringVar(value="Security")
        self.log_combo = ttk.Combobox(
            top,
            textvariable=self.log_var,
            values=LOGS,
            state="readonly",
            width=25,
            font=("Consolas", 10)
        )
        self.log_combo.pack(side="left", padx=8)

        btn_style = {
            "bg": "#003300", 
            "fg": "#00ff00", 
            "font": ("Consolas", 10, "bold"),
            "width": 14,
            "activebackground": "#004400"
        }

        tk.Button(top, text="CARREGAR", command=self.load_events, **btn_style).pack(side="left", padx=5)
        tk.Button(top, text="LIMPAR", command=self.clear_all, **btn_style).pack(side="left", padx=5)
        tk.Button(top, text="SALVAR EM TXT", command=self.save_to_txt, **btn_style).pack(side="left", padx=5)

        # ========================== TABELA ==========================
        tree_frame = tk.Frame(root, bg="#0a0a0a")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("Nº", "Data/Hora", "Fonte", "EventID", "Tipo")

        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)

        self.tree.column("Nº", width=60, anchor="center")
        self.tree.column("Data/Hora", width=170)
        self.tree.column("Fonte", width=400)
        self.tree.column("EventID", width=100)
        self.tree.column("Tipo", width=140)

        # ==================== CORES POR TIPO DE EVENTO ====================
        self.tree.tag_configure("error", foreground="#ff3333")      # Vermelho para Erros
        self.tree.tag_configure("warning", foreground="#ffaa00")    # Laranja para Avisos
        self.tree.tag_configure("success", foreground="#00ff00")    # Verde normal

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.show_details)

        # Detalhes
        detail_frame = tk.LabelFrame(root, text=" DETALHES DO EVENTO ", 
                                    font=("Consolas", 11, "bold"), 
                                    fg="#00ff00", bg="#0a0a0a")
        detail_frame.pack(fill="both", expand=False, padx=10, pady=8)

        self.details = scrolledtext.ScrolledText(
            detail_frame, 
            height=18,
            font=("Consolas", 10),
            bg="#0a0a0a", 
            fg="#00ff88",
            insertbackground="#00ff00"
        )
        self.details.pack(fill="both", expand=True, padx=8, pady=8)

        self.events = {}

    def get_event_type(self, evt_type):
        mapping = {
            1: "Erro",
            2: "Aviso",
            4: "Informação",
            8: "Sucesso da Auditoria",
            16: "Falha da Auditoria"
        }
        return mapping.get(evt_type, "Desconhecido")

    def get_event_tag(self, event_type_str):
        if "Erro" in event_type_str or "Falha" in event_type_str:
            return "error"
        elif "Aviso" in event_type_str:
            return "warning"
        else:
            return "success"

    def load_events(self):
        threading.Thread(target=self._load_events, daemon=True).start()

    def _load_events(self):
        try:
            log_name = self.log_var.get()
            self.root.after(0, self.clear_tree)

            handle = win32evtlog.OpenEventLog(None, log_name)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            count = 0
            while count < 1000:
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                if not events:
                    break

                for event in events:
                    count += 1
                    if count > 1000:
                        break

                    try:
                        event_id = event.EventID & 0xFFFF
                        tipo = self.get_event_type(event.EventType)
                        tag = self.get_event_tag(tipo)

                        row = (
                            str(count),
                            event.TimeGenerated.Format(),
                            event.SourceName,
                            str(event_id),
                            tipo
                        )

                        self.events[str(count)] = event

                        self.root.after(0, lambda r=row, iid=str(count), t=tag: 
                                      self.tree.insert("", "end", iid=iid, values=r, tags=(t,)))
                    except:
                        continue

            self.root.after(0, lambda: self.count_label.config(
                text=f"Eventos carregados: {len(self.events)}"
            ))

            win32evtlog.CloseEventLog(handle)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Erro", 
                f"Erro ao ler os logs.\nExecute o programa como Administrador.\n\n{e}"
            ))

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.details.delete("1.0", tk.END)

    def clear_all(self):
        self.clear_tree()
        self.events.clear()
        self.count_label.config(text="Eventos carregados: 0")

    def save_to_txt(self):
        if not self.tree.get_children():
            messagebox.showwarning("Aviso", "Nenhum evento carregado para salvar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile=f"Eventos_{self.log_var.get()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"GROK EVENT VIEWER - Exportação de Logs\n")
                f.write(f"Log: {self.log_var.get()}\n")
                f.write(f"Total de Eventos: {len(self.events)}\n")
                f.write(f"Data da Exportação: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 90 + "\n\n")

                for child in self.tree.get_children():
                    values = self.tree.item(child)["values"]
                    evt = self.events.get(child)
                    
                    f.write(f"Nº         : {values[0]}\n")
                    f.write(f"Data/Hora  : {values[1]}\n")
                    f.write(f"Fonte      : {values[2]}\n")
                    f.write(f"EventID    : {values[3]}\n")
                    f.write(f"Tipo       : {values[4]}\n")
                    
                    if evt:
                        try:
                            msg = win32evtlogutil.SafeFormatMessage(evt, self.log_var.get())
                            f.write(f"Mensagem   :\n{msg}\n")
                        except:
                            f.write("Mensagem   : Não disponível\n")
                    
                    f.write("-" * 80 + "\n\n")

            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")

    def show_details(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        evt = self.events.get(selected[0])
        if not evt:
            return

        try:
            msg = win32evtlogutil.SafeFormatMessage(evt, self.log_var.get())
        except:
            msg = "Mensagem não disponível."

        text = f"""[+] EVENTO {evt.EventID & 0xFFFF} - {self.log_var.get().upper()}

Fonte          : {evt.SourceName}
EventID        : {evt.EventID & 0xFFFF}
Categoria      : {evt.EventCategory}
Tipo           : {self.get_event_type(evt.EventType)}
Computador     : {evt.ComputerName}
Data/Hora      : {evt.TimeGenerated.Format()}

{'='*85}
MENSAGEM:
{msg}
{'='*85}
"""

        self.details.delete("1.0", tk.END)
        self.details.insert(tk.END, text)

if __name__ == "__main__":
    root = tk.Tk()
    app = EventViewer(root)
    root.mainloop()
