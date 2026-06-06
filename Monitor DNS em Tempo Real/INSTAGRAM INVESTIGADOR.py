import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import csv
from urllib.parse import quote_plus
from datetime import datetime

class InstagramInvestigatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("INSTAGRAM INVESTIGADOR")
        self.root.geometry("1080x940")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")
        self.current_data = None
        
        self.setup_hacker_style()
        self.setup_gui()

    def setup_hacker_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background="#0a0a0a", foreground="#00ff41")
        style.configure("TFrame", background="#0a0a0a")
        style.configure("TLabelframe", background="#0a0a0a", foreground="#00ff41")
        style.configure("TLabelframe.Label", background="#0a0a0a", foreground="#00ff41", 
                       font=("Consolas", 11, "bold"))
        style.configure("TLabel", background="#0a0a0a", foreground="#00ff41", font=("Consolas", 10))
        style.configure("TEntry", fieldbackground="#1a1a1a", foreground="#00ff41", insertcolor="#00ff41")
        self.root.option_add('*Font', 'Consolas 10')

    def setup_gui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(pady=8)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Container centralizado
        center_frame = ttk.Frame(self.main_frame)
        center_frame.grid(row=0, column=0, sticky="n")
        center_frame.columnconfigure(0, weight=1)

        # === INPUT FRAME ===
        input_frame = ttk.LabelFrame(center_frame, text="🔍 LINHA DE INVESTIGAÇÃO 🔎", padding="15")
        input_frame.grid(row=0, column=0, pady=10, sticky="ew")
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Username (sem @):").grid(row=0, column=0, pady=8, padx=8, sticky=tk.E)
        self.username_entry = ttk.Entry(input_frame, width=70)
        self.username_entry.grid(row=0, column=1, pady=8, padx=8, sticky=(tk.W, tk.E))

        ttk.Label(input_frame, text="Session ID:").grid(row=1, column=0, pady=8, padx=8, sticky=tk.E)
        self.sessionid_entry = ttk.Entry(input_frame, width=70, show="*")
        self.sessionid_entry.grid(row=1, column=1, pady=8, padx=8, sticky=(tk.W, tk.E))

        # === BUTTONS ===
        button_frame = ttk.Frame(center_frame)
        button_frame.grid(row=1, column=0, pady=15)

        btn_style = {"font": ("Consolas", 11, "bold"), "width": 18, "height": 2}

        tk.Button(button_frame, text="INVESTIGAR", bg="#05fc32", fg="black", 
                  command=self.investigate, **btn_style).grid(row=0, column=0, padx=5)
        
        tk.Button(button_frame, text="VER TUTORIAL", bg="#ffcc00", fg="black", 
                  command=self.show_tutorial, **btn_style).grid(row=0, column=1, padx=5)
        
        tk.Button(button_frame, text="EXPORTAR DADOS", bg="#00ccff", fg="black", 
                  command=self.export_data, **btn_style).grid(row=0, column=2, padx=5)
        
        # Novo botão SALVAR TXT
        tk.Button(button_frame, text="SALVAR TXT", bg="#c48909", fg="black", 
                  command=self.save_to_txt, **btn_style).grid(row=0, column=3, padx=5)
        
        tk.Button(button_frame, text="SAIR", bg="#ff3300", fg="black", 
                  command=self.root.quit, **btn_style).grid(row=0, column=4, padx=5)

        # === TERMINAL OUTPUT ===
        result_frame = ttk.LabelFrame(center_frame, text="TERMINAL OUTPUT", padding="10")
        result_frame.grid(row=2, column=0, pady=10, sticky="ew")

        self.results_text = tk.Text(result_frame, height=40, width=140, wrap=tk.WORD,
                                    bg="#0a0a0a", fg="#00ff41", font=("Consolas", 10),
                                    insertbackground="#00ff41", selectbackground="#00ff88")
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text['yscrollcommand'] = scrollbar.set

        # Tags
        self.results_text.tag_configure("header", foreground="#00ff41", font=("Consolas", 12, "bold"))
        self.results_text.tag_configure("success", foreground="#00ff88")
        self.results_text.tag_configure("warning", foreground="#ffaa00")
        self.results_text.tag_configure("error", foreground="#ff4444")
        self.results_text.tag_configure("info", foreground="#44ffff")
        self.results_text.tag_configure("bold", font=("Consolas", 10, "bold"))
        self.results_text.config(state=tk.DISABLED)

    def save_to_txt(self):
        if not self.current_data:
            messagebox.showwarning("Aviso", "Nenhuma investigação realizada ainda!")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        username = self.current_data.get('username', 'unknown')
        default_filename = f"IG_INVESTIGATOR_{username}_{timestamp}.txt"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("INSTAGRAM INVESTIGATOR v2.0 - RELATÓRIO\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Alvo: @{self.current_data.get('username')}\n\n")

                f.write("INFORMAÇÕES BÁSICAS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Username      : @{self.current_data.get('username')}\n")
                f.write(f"User ID       : {self.current_data.get('userID')}\n")
                f.write(f"Nome          : {self.current_data.get('full_name')}\n")
                f.write(f"Verificado    : {'Sim' if self.current_data.get('is_verified') else 'Não'}\n")
                f.write(f"Privado       : {'Sim' if self.current_data.get('is_private') else 'Não'}\n\n")

                f.write("ESTATÍSTICAS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Seguidores    : {self.current_data.get('follower_count', 0):,}\n")
                f.write(f"Seguindo      : {self.current_data.get('following_count', 0):,}\n")
                f.write(f"Publicações   : {self.current_data.get('media_count', 0):,}\n\n")

                f.write("CONTATO\n")
                f.write("-" * 40 + "\n")
                if self.current_data.get('public_email'):
                    f.write(f"Email         : {self.current_data['public_email']}\n")
                if self.current_data.get('public_phone_number'):
                    f.write(f"Telefone      : +{self.current_data.get('public_phone_country_code','')} {self.current_data['public_phone_number']}\n")
                if self.current_data.get('external_url'):
                    f.write(f"Link Externo  : {self.current_data['external_url']}\n")
                if self.current_data.get('biography'):
                    f.write(f"Bio           : {self.current_data['biography']}\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("Relatório gerado pelo Instagram Investigator v2.0")

            self.update_text(f"💾 Relatório salvo em TXT: {file_path}", "success")
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n{file_path}")
        except Exception as e:
            self.update_text(f"❌ Erro ao salvar TXT: {e}", "error")
            messagebox.showerror("Erro", f"Falha ao salvar arquivo: {e}")

    def update_text(self, message, tag=None):
        self.results_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self.results_text.insert(tk.END, line, tag)
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see(tk.END)
        self.root.update_idletasks()

    def show_tutorial(self):
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("Tutorial - Obter Session ID")
        tutorial_window.geometry("780x420")
        tutorial_window.configure(bg="#0a0a0a")

        text = tk.Text(tutorial_window, bg="#0a0a0a", fg="#00ff41", font=("Consolas", 11), wrap=tk.WORD)
        text.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        content = """📋 COMO OBTER O SESSION ID (sessionid)

1. Abra o Instagram no navegador (Chrome/Firefox)
2. Faça login na sua conta
3. Pressione F12 → aba "Application" ou "Aplicação"
4. No menu esquerdo: Cookies → https://www.instagram.com
5. Procure pela chave "sessionid"
6. Copie o valor longo

⚠️ ATENÇÃO:
• Nunca compartilhe seu sessionid
• Use uma conta secundária para testes
• O sessionid expira eventualmente"""

        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)

    # ==================== MÉTODOS DE BUSCA ====================
    def get_user_id(self, username, session_id):
        headers = {"User-Agent": "iphone_ua", "x-ig-app-id": "936619743392459"}
        url = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
        try:
            response = requests.get(url, headers=headers, cookies={'sessionid': session_id}, timeout=30)
            if response.status_code == 404:
                return {"id": None, "error": "Usuário não encontrado"}
            data = response.json()
            return {"id": data["data"]["user"]["id"], "error": None}
        except Exception as e:
            return {"id": None, "error": str(e)}

    def get_user_info(self, user_id, session_id):
        headers = {'User-Agent': 'Instagram 64.0.0.14.96'}
        url = f'https://i.instagram.com/api/v1/users/{user_id}/info/'
        try:
            response = requests.get(url, headers=headers, cookies={'sessionid': session_id}, timeout=30)
            response.raise_for_status()
            data = response.json()
            user_info = data.get("user")
            if user_info:
                user_info["userID"] = user_id
            return {"user": user_info, "error": None}
        except Exception as e:
            return {"user": None, "error": str(e)}

    def advanced_lookup(self, username):
        data_payload = "signed_body=SIGNATURE." + quote_plus(json.dumps(
            {"q": username, "skip_recovery": "1"}, separators=(",", ":")))
        headers = {
            "User-Agent": "Instagram 101.0.0.15.120",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-App-ID": "124024574287414",
        }
        try:
            response = requests.post('https://i.instagram.com/api/v1/users/lookup/',
                                   headers=headers, data=data_payload, timeout=30)
            return {"user": response.json(), "error": None}
        except:
            return {"user": None, "error": "Falha no lookup avançado"}

    def investigate(self):
        username = self.username_entry.get().strip()
        session_id = self.sessionid_entry.get().strip()

        if not username or not session_id:
            messagebox.showerror("Erro", "Username e Session ID são obrigatórios!")
            return

        if username.startswith('@'):
            username = username[1:]

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)

        self.update_text("═" * 90, "header")
        self.update_text("🚀 INICIANDO INVESTIGAÇÃO", "header")
        self.update_text("═" * 90, "header")
        self.update_text("\n")

        try:
            self.update_text(f"Alvo: @{username}\n", "info")
            self.update_text("Obtendo User ID\n", "bold")
            user_id_data = self.get_user_id(username, session_id)
            if user_id_data.get("error"):
                raise Exception(user_id_data["error"])
            user_id = user_id_data["id"]
            self.update_text(f"✅ User ID: {user_id}", "success")

            self.update_text("\nColetando informações completas\n", "bold")
            info_data = self.get_user_info(user_id, session_id)
            if info_data.get("error"):
                raise Exception(info_data["error"])

            user_info = info_data["user"]
            self.update_text("✅ Informações básicas obtidas", "success")

            self.update_text("\nExecutando lookup avançado", "bold")
            advanced_data = self.advanced_lookup(username)

            combined_data = {**user_info, **(advanced_data.get("user") or {})}
            self.current_data = combined_data

            self.display_results(combined_data)
        except Exception as e:
            self.update_text(f"❌ FALHA: {str(e)}", "error")

    def display_results(self, data):
        self.update_text("\n" + "═" * 101, "header")
        self.update_text("📊 RELATÓRIO FINAL", "header")
        self.update_text("═" * 90 + "\n", "header")
        
        self.update_text("👤 INFORMAÇÕES BÁSICAS 👤\n", "bold")
        self.update_text(f" Username → @{data.get('username')}", "success")
        self.update_text(f" User ID → {data.get('userID')}", "success")
        self.update_text(f" Nome → {data.get('full_name')}", "success")
        self.update_text(f" Verificado → {'✅ Sim' if data.get('is_verified') else '❌ Não'}", 
                        "success" if data.get('is_verified') else "error")
        self.update_text(f" Privado → {'🔒 Sim' if data.get('is_private') else '🌍 Não'}", 
                        "error" if data.get('is_private') else "success")

        self.update_text("\n\n📈 ESTATÍSTICAS 📈", "bold")
        self.update_text("\n")
        self.update_text(f" Seguidores → {data.get('follower_count', 0):,}", "info")
        self.update_text(f" Seguindo → {data.get('following_count', 0):,}", "info")
        self.update_text(f" Publicações → {data.get('media_count', 0):,}", "info")

        self.update_text("\n\n📞 CONTATO", "bold")
        self.update_text("\n")
        if data.get('public_email'):
            self.update_text(f" Email → {data['public_email']}", "success")
        if data.get('public_phone_number'):
            self.update_text(f" Telefone → +{data.get('public_phone_country_code','')} {data['public_phone_number']}", "success")

        if data.get('external_url'):
            self.update_text(f"\n🔗 Link Externo → {data['external_url']}", "info")
        if data.get('biography'):
            bio = data['biography'][:150] + "..." if len(data.get('biography','')) > 150 else data.get('biography','')
            self.update_text(f"\n📝 Bio: {bio}", "info")

        self.update_text("\n" + "═" * 100, "header")
        self.update_text(f"✅ INVESTIGAÇÃO CONCLUÍDA • {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "header")

    def export_data(self):
        if not self.current_data:
            messagebox.showwarning("Aviso", "Nenhuma investigação realizada ainda!")
            return

        format_choice = messagebox.askquestion("Exportar", "Deseja exportar em JSON? (Sim = JSON, Não = CSV)")
        format_type = 'json' if format_choice == 'yes' else 'csv'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        username = self.current_data.get('username', 'unknown')
        default_filename = f"IG_INVESTIGATOR_{username}_{timestamp}.{format_type}"

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            initialfile=default_filename,
            filetypes=[(f"{format_type.upper()} files", f"*.{format_type}"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, indent=2, ensure_ascii=False)
            else:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Campo', 'Valor'])
                    for key, value in self.current_data.items():
                        if not isinstance(value, (dict, list)):
                            writer.writerow([key, str(value)])
            self.update_text(f"💾 Dados exportados com sucesso: {file_path}", "success")
        except Exception as e:
            self.update_text(f"❌ Erro na exportação: {e}", "error")


def main():
    root = tk.Tk()
    app = InstagramInvestigatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
