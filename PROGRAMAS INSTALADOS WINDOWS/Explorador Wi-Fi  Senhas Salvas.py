import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import ctypes
from datetime import datetime

class WifiScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Explorador Wi-Fi - Senhas Salvas")
        self.root.geometry("1580x900")
        self.root.state("zoomed")
      
        self.is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
      
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
      
        self.wifi_tab = ttk.Frame(self.notebook)
        self.passwords_tab = ttk.Frame(self.notebook)
      
        self.notebook.add(self.wifi_tab, text="Redes Wi-Fi")
        self.notebook.add(self.passwords_tab, text="Senhas Salvas")
      
        self.init_wifi_tab()
        self.init_passwords_tab()

    def init_wifi_tab(self):
        tk.Label(self.wifi_tab, text="Explorador de Redes Wi-Fi",
                font=("Segoe UI", 18, "bold")).pack(pady=10)
        
        # Texto atualizado
        tk.Label(self.wifi_tab, text="Duplo clique na linha para copiar SSID + BSSID", 
                fg="blue").pack(pady=2)
      
        frame = tk.Frame(self.wifi_tab)
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame, text="🔄 Atualizar Redes", command=self.scan_wifi).pack(side="left", padx=5)
        ttk.Button(frame, text="💾 Salvar Resultados", command=self.save_scan_results).pack(side="left", padx=5)

        colunas = ("SSID", "BSSID", "Sinal", "Autenticação", "Criptografia")
        self.tree = ttk.Treeview(self.wifi_tab, columns=colunas, show="headings")
        for col in colunas:
            self.tree.heading(col, text=col)
        self.tree.column("SSID", width=280)
        self.tree.column("BSSID", width=180)
        self.tree.column("Sinal", width=100)
        self.tree.column("Autenticação", width=180)
        self.tree.column("Criptografia", width=180)
      
        self.setup_tree(self.tree, self.wifi_tab)
        
        # Duplo clique agora copia SSID + BSSID
        self.tree.bind("<Double-1>", self.copiar_ssid_e_bssid)

    def init_passwords_tab(self):
        tk.Label(self.passwords_tab, text="Senhas Wi-Fi Salvas no PC",
                font=("Segoe UI", 18, "bold")).pack(pady=10)
       
        if not self.is_admin:
            tk.Label(self.passwords_tab, text="⚠️ Execute como ADMINISTRADOR para ver as senhas!",
                    font=("Segoe UI", 10, "bold"), fg="red").pack(pady=5)
       
        tk.Label(self.passwords_tab, text="Redes WiFi Salvas:", 
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(10, 5))

        list_frame = tk.Frame(self.passwords_tab)
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(list_frame, height=15, font=("Consolas", 10), 
                                 yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Botões
        btn_frame = tk.Frame(self.passwords_tab)
        btn_frame.pack(fill="x", padx=20, pady=8)

        ttk.Button(btn_frame, text="🔄 Atualizar Lista", 
                  command=self.refresh_list).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔑 Mostrar Senha", 
                  command=self.show_password).pack(side="left", padx=5)        
        ttk.Button(btn_frame, text="💾 Salvar Senha Selecionada", 
                  command=self.export_single_password).pack(side="left", padx=5)

        # Resultado
        tk.Label(self.passwords_tab, text="Resultado:", 
                font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.result_text = tk.Text(self.passwords_tab, height=6, font=("Consolas", 11), 
                                  bg="#f0f0f0", state="disabled", wrap="word")
        self.result_text.pack(fill="x", padx=20, pady=5)

        self.root.after(300, self.refresh_list)

    def setup_tree(self, tree, parent):
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

    def copiar_ssid_e_bssid(self, event):
        """Duplo clique copia SSID e BSSID formatados"""
        selection = self.tree.selection()
        if selection:
            valores = self.tree.item(selection[0])['values']
            if valores and len(valores) >= 2:
                ssid = valores[0]
                bssid = valores[1]
                texto = f"SSID: {ssid}\n\nBSSID: {bssid}"
                
                self.root.clipboard_clear()
                self.root.clipboard_append(texto)
                self.root.update()

    def scan_wifi(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            resultado = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=bssid"],
                                              text=True, encoding="utf-8", errors="ignore")
            ssid = bssid = sinal = auth = crypto = ""
            for linha in resultado.splitlines():
                linha = linha.strip()
                if m := re.match(r"SSID\s+\d+\s*:\s*(.*)", linha):
                    ssid = m.group(1).strip()
                elif linha.startswith("BSSID"):
                    bssid = linha.split(":", 1)[1].strip()
                elif any(x in linha for x in ["Authentication", "Autenticação"]):
                    auth = linha.split(":", 1)[1].strip()
                elif any(x in linha for x in ["Encryption", "Criptografia"]):
                    crypto = linha.split(":", 1)[1].strip()
                elif any(x in linha for x in ["Signal", "Sinal"]):
                    sinal = linha.split(":", 1)[1].strip()
                    if ssid:
                        self.tree.insert("", "end", values=(ssid, bssid, sinal, auth, crypto))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao escanear redes: {e}")

    def save_scan_results(self):
        if not self.tree.get_children():
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos", "*.*")],
            initialfile=f"wifi_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== SCAN DE REDES WI-FI ===\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write("SSID".ljust(35) + "BSSID".ljust(25) + "Sinal".ljust(10) + 
                       "Autenticação".ljust(25) + "Criptografia\n")
                f.write("-" * 120 + "\n")
                
                for item in self.tree.get_children():
                    values = self.tree.item(item)['values']
                    f.write(f"{str(values[0]).ljust(35)}{str(values[1]).ljust(25)}{str(values[2]).ljust(10)}"
                           f"{str(values[3]).ljust(25)}{values[4]}\n")
            messagebox.showinfo("Sucesso", f"Resultados salvos em:\n{filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    # ====================== FUNÇÕES DE SENHAS ======================
    def get_wifi_profiles(self):
        try:
            command_output = subprocess.check_output('netsh wlan show profiles', 
                                                   shell=True, 
                                                   universal_newlines=True)
            lines = command_output.split('\n')
            ssids = []
            
            for line in lines[9:]:                    
                if ":" in line:
                    tokens = line.split(":")
                    if len(tokens) >= 2:
                        ssid = tokens[1].strip()
                        if ssid:
                            ssids.append(ssid)
            return ssids
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar redes: {e}")
            return []

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        ssids = self.get_wifi_profiles()
        if ssids:
            for ssid in ssids:
                self.listbox.insert(tk.END, ssid)
        else:
            self.listbox.insert(tk.END, "Nenhuma rede encontrada")

    def show_password(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma rede!")
            return
        
        ssid = self.listbox.get(selected[0])
        
        try:
            key_output = subprocess.check_output(
                f'netsh wlan show profiles "{ssid}" key=clear', 
                shell=True, 
                universal_newlines=True
            )
            
            key_content_line = [line for line in key_output.split('\n') 
                              if "Conte£do da Chave" in line or "Key Content" in line]
            
            if key_content_line:
                key_content = key_content_line[0].split(":", 1)[1].strip()
                self.result_text.config(state="normal")
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"SSID: {ssid}\n\nSenha: {key_content}")
                self.result_text.config(state="disabled")
            else:
                messagebox.showinfo("Senha", f"Não foi possível recuperar a senha da rede: {ssid}")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao recuperar senha: {e}")

    def export_single_password(self):
        """Salva o conteúdo que está no campo Resultado"""
        self.result_text.config(state="normal")
        conteudo = self.result_text.get("1.0", tk.END).strip()
        self.result_text.config(state="disabled")

        if not conteudo or "Senha:" not in conteudo:
            messagebox.showwarning("Aviso", "Não há senha mostrada no resultado!")
            return

        try:
            ssid = conteudo.split("SSID: ")[1].split("\n")[0].strip()
        except:
            ssid = "Rede_WiFi"

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os Arquivos", "*.*")],
            initialfile=f"Senha_{ssid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== SENHA WI-FI ===\n\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n\n")
                f.write(conteudo)
                f.write("\n\n====================================\n")
                f.write("Gerado pelo Explorador Wi-Fi")

            messagebox.showinfo("Sucesso", f"Senha salva com sucesso!\n\nArquivo\n {filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WifiScanner(root)
    root.mainloop()
