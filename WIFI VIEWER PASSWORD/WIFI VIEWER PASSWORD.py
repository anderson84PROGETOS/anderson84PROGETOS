import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime

def scan_wifi():
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, "🔍 Buscando redes salvas...\n\n")
    
    try:
        profiles = subprocess.check_output(
            'netsh wlan show profiles', 
            shell=True,
            universal_newlines=True
        )
        
        clean_profiles = [line for line in profiles.split('\n') 
                         if "<Nenhum>" not in line and "pol¡tica de grupo" not in line]
        
        clean_output = "\n".join(clean_profiles)      
        text_area.insert(tk.END, clean_output)        
        names = []
        for line in profiles.split('\n'):
            line = line.strip()
            if "Todos os Perfis de Usu" in line or "All User Profile" in line:
                try:
                    name = line.split(":", 1)[1].strip()
                    names.append(name)
                except:
                    pass

        text_area.insert(tk.END, f"\n📋 Redes Encontradas: {len(names)}\n\n")
        
        results = {}
        for ssid in names:
            try:
                output = subprocess.check_output(
                    f'netsh wlan show profile name="{ssid}" key=clear',
                    shell=True,
                    universal_newlines=True
                )
                password = None
                for line in output.split('\n'):
                    if any(k in line for k in ["Conteúdo da Chave", "Key Content", "Conte£do da Chave"]):
                        password = line.split(":", 1)[1].strip()
                        break
                
                if password:
                    text_area.insert(tk.END, f"✅ {ssid:<20}  → 🔑  {password}\n")
                    results[ssid] = password
                else:
                    text_area.insert(tk.END, f"✅ {ssid:<20}  → 🔑  (sem senha ou aberta)\n")
            except:
                text_area.insert(tk.END, f"❌ {ssid:<20} → Erro\n")
        
        text_area.insert(tk.END, "\n" + "="*60 + "\n")
        text_area.insert(tk.END, "RESUMO FINAL\n")
        text_area.insert(tk.END, "="*60 + "\n\n")
        
        for ssid, pwd in results.items():
            text_area.insert(tk.END, f"{ssid:<20}  🔑   {pwd}\n")
        
        return results

    except Exception as e:
        text_area.insert(tk.END, f"ERRO GERAL: {e}\n")
        return {}

def start_scan():
    btn_scan.config(state="disabled")
    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

def run_scan():
    results = scan_wifi()
    root.results = results
    btn_scan.config(state="normal")

def save_txt():
    if not hasattr(root, 'results') or not root.results:
        messagebox.showwarning("Aviso", "Execute o scan primeiro!")
        return
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"senhas_wifi_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("🔍 Buscando redes salvas\n\n")
            f.write("Perfis na interface Wi-Fi\n")
            f.write("---------------------------------\n")
            f.write("Perfis do usuário\n")
            f.write("---------------------------------\n")
            
            # Salva as redes encontradas
            for ssid in root.results.keys():
                f.write(f"Todos os Perfis de Usuários: {ssid}\n")
            
            f.write(f"\n📋 Redes Encontradas: {len(root.results)}\n\n")
            
            # Resultados com senha
            for ssid, pwd in root.results.items():
                if pwd == "(sem senha ou aberta)":
                    f.write(f"✅ {ssid:<20} → 🔑  (sem senha ou aberta)\n")
                else:
                    f.write(f"✅ {ssid:<20} → 🔑  {pwd}\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("RESUMO FINAL\n")
            f.write("="*60 + "\n\n")
            
            # Resumo limpo
            for ssid, pwd in root.results.items():
                f.write(f"{ssid:<20} 🔑  {pwd}\n")
            
            f.write("\n" + "="*60 + "\n\n")
            f.write(f"Arquivo gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        
        messagebox.showinfo("Sucesso", f"Arquivo .txt salvo!\n\n{filename}")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar .txt\n{e}")


def save_json():
    if not hasattr(root, 'results') or not root.results:
        messagebox.showwarning("Aviso", "Execute o scan primeiro!")
        return
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"senhas_wifi_{timestamp}.json"
        
        data = {
            "mensagem": "🔍 Buscando redes salvas",
            "redes_encontradas": len(root.results),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "perfis": [
                {"rede": ssid, "senha": pwd} for ssid, pwd in root.results.items()
            ],
            "resumo": dict(root.results)
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        messagebox.showinfo("Sucesso", f"Arquivo .json salvo!\n\n{filename}")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar .json\n{e}")

# ==================== INTERFACE ====================
root = tk.Tk()
root.title("WIFI VIEWER PASSWORD")
root.geometry("910x910")
#root.state("zoomed")
root.configure(bg="#0a0a0a")

# Título
tk.Label(root, text="WIFI VIEWER PASSWORD", font=("Consolas", 26, "bold"), fg="#00ff41", bg="#0a0a0a").pack(pady=8)

# ==================== BOTÕES ====================
top_frame = tk.Frame(root, bg="#0a0a0a")
top_frame.pack(pady=10)

btn_scan = tk.Button(top_frame, text="▶ INICIAR SCAN", command=start_scan, width=22, font=("Segoe UI", 10, "bold"), bg="#28A745", fg="black", activebackground="#218838", activeforeground="black")
btn_scan.pack(side="left", padx=8)

tk.Button(top_frame, text="💾 Salvar como .TXT", command=save_txt, width=22, font=("Segoe UI", 10, "bold"), bg="#007BFF", fg="black", activebackground="#0056B3", activeforeground="black").pack(side="left", padx=8)

tk.Button(top_frame, text="💾 Salvar como .JSON", command=save_json, width=22, font=("Segoe UI", 10, "bold"), bg="#FD7E14", fg="black", activebackground="#E96B00", activeforeground="white").pack(side="left", padx=8)

# Área de texto
text_area = scrolledtext.ScrolledText(
    root,
    width=100,      # largura em caracteres
    height=40,      # altura em linhas
    font=("Consolas", 11),
    bg="#000000",
    fg="#00ff41"
)
text_area.pack(padx=20, pady=15)

# Rodapé
tk.Label(root, text="Execute o programa como Administrador", font=("Consolas", 9), fg="#008800", bg="#0a0a0a").pack(pady=5)

root.results = {}

root.mainloop() 
