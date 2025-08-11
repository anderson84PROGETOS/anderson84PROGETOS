import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import csv
from urllib.parse import quote_plus
from datetime import datetime
import time

class InstagramInvestigatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Investigator")
        self.root.geometry("850x600")
        self.current_data = None
        self.setup_gui()

    def setup_gui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Input frame
        input_frame = ttk.LabelFrame(self.main_frame, text="Input", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Username input
        ttk.Label(input_frame, text="Username (sem @):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.username_entry = ttk.Entry(input_frame, width=80)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        # Session ID input
        ttk.Label(input_frame, text="Session ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sessionid_entry = ttk.Entry(input_frame, width=80, show="*")
        self.sessionid_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        # Buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(button_frame, text="Investigar", command=self.investigate).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Ver Tutorial", command=self.show_tutorial).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Exportar Dados", command=self.export_data).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Sair", command=self.root.quit).grid(row=0, column=3, padx=5)

        # Results text area
        self.results_text = tk.Text(self.main_frame, height=20, width=80, wrap=tk.WORD)
        self.results_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.results_text['yscrollcommand'] = scrollbar.set

        # Configure text tags for styling
        self.results_text.tag_configure("header", foreground="purple", font=("Arial", 12, "bold"))
        self.results_text.tag_configure("success", foreground="green")
        self.results_text.tag_configure("warning", foreground="orange")
        self.results_text.tag_configure("error", foreground="red")
        self.results_text.tag_configure("#0606bf", foreground="#0606bf")
        self.results_text.tag_configure("bold", font=("Arial", 10, "bold"))

        # Make text area read-only
        self.results_text.config(state=tk.DISABLED)

    def update_text(self, message, tag=None):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, message + "\n", tag)
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see(tk.END)
        self.root.update()

    def show_tutorial(self):
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("Tutorial: Obter Session ID")
        tutorial_window.geometry("700x300")

        tutorial_text = tk.Text(tutorial_window, height=15, width=60, wrap=tk.WORD)
        tutorial_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tutorial_window, orient=tk.VERTICAL, command=tutorial_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tutorial_text['yscrollcommand'] = scrollbar.set

        tutorial_content = """
📋 Como obter o Session ID do Instagram:

1. Abra o Instagram no navegador e faça login
2. Pressione F12 para abrir as ferramentas de desenvolvedor
3. Vá na aba "Application" ou "Aplicação"
4. No menu lateral, clique em "Cookies" → "https://www.instagram.com"
5. Procure por "sessionid" e copie o valor

⚠️ IMPORTANTE: Mantenha seu session ID seguro e não compartilhe!
"""
        tutorial_text.insert(tk.END, tutorial_content)
        tutorial_text.config(state=tk.DISABLED)

    def get_user_id(self, username, session_id):
        headers = {"User-Agent": "iphone_ua", "x-ig-app-id": "936619743392459"}
        url = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
        
        try:
            response = requests.get(url, headers=headers, cookies={'sessionid': session_id}, timeout=30)
            if response.status_code == 404:
                return {"id": None, "error": "Usuário não encontrado"}
            data = response.json()
            user_id = data["data"]["user"]["id"]
            return {"id": user_id, "error": None}
        except requests.exceptions.RequestException as e:
            return {"id": None, "error": f"Erro de rede: {str(e)}"}
        except json.JSONDecodeError:
            return {"id": None, "error": "Rate limit atingido ou resposta inválida"}
        except KeyError:
            return {"id": None, "error": "Formato de resposta inválido"}

    def get_user_info(self, user_id, session_id):
        headers = {'User-Agent': 'Instagram 64.0.0.14.96'}
        url = f'https://i.instagram.com/api/v1/users/{user_id}/info/'
        
        try:
            response = requests.get(url, headers=headers, cookies={'sessionid': session_id}, timeout=30)
            if response.status_code == 429:
                return {"user": None, "error": "Rate limit atingido"}
            response.raise_for_status()
            data = response.json()
            user_info = data.get("user")
            if not user_info:
                return {"user": None, "error": "Usuário não encontrado"}
            user_info["userID"] = user_id  # Fixed: Proper assignment of user_id
            return {"user": user_info, "error": None}
        except requests.exceptions.RequestException as e:
            return {"user": None, "error": f"Erro de rede: {str(e)}"}
        except json.JSONDecodeError:
            return {"user": None, "error": "Resposta inválida"}

    def advanced_lookup(self, username):
        data_payload = "signed_body=SIGNATURE." + quote_plus(json.dumps(
            {"q": username, "skip_recovery": "1"}, separators=(",", ":")
        ))
        headers = {
            "Accept-Language": "en-US",
            "User-Agent": "Instagram 101.0.0.15.120",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-App-ID": "124024574287414",
            "Accept-Encoding": "gzip, deflate",
            "Host": "i.instagram.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data_payload))
        }
        
        try:
            response = requests.post('https://i.instagram.com/api/v1/users/lookup/',
                                   headers=headers, data=data_payload, timeout=30)
            data = response.json()
            return {"user": data, "error": None}
        except requests.exceptions.RequestException as e:
            return {"user": None, "error": f"Erro de rede: {str(e)}"}
        except json.JSONDecodeError:
            return {"user": None, "error": "Rate limit"}

    def investigate(self):
        username = self.username_entry.get().strip()
        session_id = self.sessionid_entry.get().strip()

        if not username or not session_id:
            messagebox.showerror("Erro", "Username e Session ID são obrigatórios!")
            return

        if username.startswith('@'):
            username = username[1:]
            self.update_text("   @ removido automaticamente", "warning")

        if not username.replace('_', '').replace('.', '').isalnum():
            messagebox.showerror("Erro", "Username inválido! Use apenas letras, números, pontos e underscores.")
            return

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)
        self.update_text(f"🔍 Iniciando investigação de: @{username}", "header")

        try:
            # Step 1: Get user ID
            self.update_text("⏳ Obtendo ID do usuário...", "#0606bf")
            user_id_data = self.get_user_id(username, session_id)
            if user_id_data.get("error"):
                raise Exception(user_id_data["error"])
            user_id = user_id_data["id"]
            self.update_text(f"✅ ID encontrado: {user_id}", "success")
            time.sleep(1)

            # Step 2: Get detailed user info
            self.update_text("⏳ Coletando informações detalhadas...", "#0606bf")
            info_data = self.get_user_info(user_id, session_id)
            if info_data.get("error"):
                raise Exception(info_data["error"])
            user_info = info_data["user"]
            self.update_text("✅ Informações básicas coletadas", "success")
            time.sleep(1)

            # Step 3: Advanced lookup
            self.update_text("⏳ Realizando lookup avançado...", "#0606bf")
            advanced_data = self.advanced_lookup(username)
            if not advanced_data.get("error"):
                self.update_text("✅ Lookup avançado concluído", "success")
            else:
                self.update_text("⚠️ Lookup avançado falhou (rate limit)", "warning")

            # Combine data
            combined_data = {**user_info, **advanced_data.get("user", {})}
            self.current_data = combined_data
            self.display_results(combined_data)

        except Exception as e:
            self.update_text(f"❌ Falha na investigação: {str(e)}", "error")

    def display_results(self, data):
        self.update_text("="*70, "header")
        self.update_text("📊 RESULTADOS DA INVESTIGAÇÃO", "header")
        self.update_text("="*70, "header")
        self.update_text("\n👤 INFORMAÇÕES BÁSICAS:", "bold")
        self.update_text(f"   Username: {data.get('username', 'N/A')}", "success")
        self.update_text(f"   User ID: {data.get('userID', 'N/A')}", "success")
        self.update_text(f"   Nome Completo: {data.get('full_name', 'N/A')}", "success")
        self.update_text(f"   Verificado: {'Sim' if data.get('is_verified') else 'Não'}", 
                        "success" if data.get('is_verified') else "error")
        self.update_text(f"   Conta Business: {'Sim' if data.get('is_business') else 'Não'}", 
                        "success" if data.get('is_business') else "error")
        self.update_text(f"   Conta Privada: {'Sim' if data.get('is_private') else 'Não'}", 
                        "error" if data.get('is_private') else "success")

        self.update_text("\n📈 ESTATÍSTICAS:", "bold")
        self.update_text(f"   Seguidores: {data.get('follower_count', 'N/A'):,}", "#0606bf")
        self.update_text(f"   Seguindo: {data.get('following_count', 'N/A'):,}", "#0606bf")
        self.update_text(f"   Posts: {data.get('media_count', 'N/A'):,}", "#0606bf")
        self.update_text(f"   Vídeos IGTV: {data.get('total_igtv_videos', 'N/A')}", "#0606bf")

        self.update_text("\n📞 INFORMAÇÕES DE CONTATO:", "bold")
        if data.get('public_email'):
            self.update_text(f"   Email Público: {data['public_email']}", "success")
        if data.get('public_phone_number'):
            phone = f"+{data.get('public_phone_country_code', '')} {data['public_phone_number']}"
            self.update_text(f"   Telefone Público: {phone}", "success")
        if data.get('obfuscated_email'):
            self.update_text(f"   Email Ofuscado: {data['obfuscated_email']}", "warning")
        if data.get('obfuscated_phone'):
            self.update_text(f"   Telefone Ofuscado: {data['obfuscated_phone']}", "warning")
        self.update_text(f"   WhatsApp Vinculado: {'Sim' if data.get('is_whatsapp_linked') else 'Não'}", 
                        "success" if data.get('is_whatsapp_linked') else "error")

        self.update_text("\n🔗 OUTRAS INFORMAÇÕES:", "bold")
        if data.get('external_url'):
            self.update_text(f"   URL Externa: {data['external_url']}", "#0606bf")
        if data.get('biography'):
            bio = data['biography'][:100] + "..." if len(data.get('biography', '')) > 100 else data.get('biography', '')
            self.update_text(f"   Biografia: {bio}", "#0606bf")
        if data.get('hd_profile_pic_url_info', {}).get('url'):
            self.update_text(f"   Foto de Perfil: {data['hd_profile_pic_url_info']['url']}", "#0606bf")

        self.update_text("\n"+"="*70, "header")
        self.update_text(f"⏰ Investigação concluída em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "header")
        self.update_text("="*70, "header")

    def export_data(self):
        if not self.current_data:
            messagebox.showwarning("Aviso", "Nenhuma investigação realizada ainda!")
            return

        format_choice = messagebox.askquestion("Exportar Dados", "Deseja exportar em JSON? (Sim = JSON, Não = CSV)")
        format_type = 'json' if format_choice == 'yes' else 'csv'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        username = self.current_data.get('username', 'unknown')
        default_filename = f"instagram_{username}_{timestamp}.{format_type}"
        
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
            elif format_type == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Campo', 'Valor'])
                    for key, value in self.current_data.items():
                        if isinstance(value, dict):
                            continue
                        writer.writerow([key, str(value)])
            self.update_text(f"✅ Dados exportados para: {file_path}", "success")
        except Exception as e:
            self.update_text(f"❌ Erro ao exportar: {str(e)}", "error")

def main():
    root = tk.Tk()
    app = InstagramInvestigatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
