import socket
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess

def obter_provedor_internet():
    url = url_entry.get()
    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL.")
        return
    
    try:
        # Extrai o hostname da URL fornecida
        hostname = url.split("//")[-1].split("/")[0]
        
        # Obtém o endereço IP do hostname
        ip_address = socket.gethostbyname(hostname)
        
        # Define os cabeçalhos, incluindo o User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        }

        # Tenta acessar a URL fornecida para obter os cabeçalhos HTTP
        response = requests.get(url, headers=headers)
        
        # Usa um serviço de geolocalização para obter informações sobre o IP
        geo_response = requests.get(f"http://ip-api.com/json/{ip_address}", headers=headers)
        geo_data = geo_response.json()

        if geo_response.status_code == 200 and geo_data['status'] == 'success':
            # Exibe o provedor de Internet (ISP)
            isp_info = f"Provedor de Internet: {geo_data['isp']}\n"
        else:
            isp_info = "Não foi possível obter as informações do provedor de Internet.\n"

        # Exibe os cabeçalhos HTTP da resposta
        headers_info = "\n".join(f"{key}: {value}" for key, value in response.headers.items())

        # Atualiza o texto na caixa de texto rolável
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.INSERT, f"======================================================= Provedor de Internet ==========================================================\n\n\n{isp_info}\n")
        result_text.insert(tk.INSERT, "\n======================================================= Cabeçalhos HTTP ===========================================================\n\n")
        result_text.insert(tk.INSERT, headers_info)
        result_text.config(state=tk.DISABLED)
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            error_info = "Erro 403: Acesso proibido. Detalhes dos cabeçalhos HTTP:\n"
            error_info += "\n".join(f"{key}: {value}" for key, value in e.response.headers.items())
            messagebox.showerror("Erro HTTP", error_info)
        else:
            messagebox.showerror("Erro HTTP", f'Erro ao conectar-se ao {url}: {e.response.status_code}')
    except Exception as e:
        messagebox.showerror("Erro", f'Erro ao conectar-se ao {url}: {e}')

def dns_transferencia_zona():
    site = url_entry.get().replace('http://', '').replace('https://', '').split('/')[0]
    if not site:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    try:
        # Executa o comando 'nslookup' e captura a saída
        output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
        
        # Divide a saída em linhas e extrai os servidores DNS
        lines = output_dns.stdout.splitlines()
        servers = [line.split()[-1] for line in lines if 'nameserver' in line]
        
        if not servers:
            messagebox.showwarning("Aviso", "Nenhum servidor DNS encontrado para a URL fornecida.")
            return

        # Conjunto para armazenar e verificar duplicatas de saída
        unique_outputs = set()

        # Itera sobre cada servidor DNS e executa o comando 'nslookup -type=any'
        for server in servers:
            output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
            # Verifica se a saída já foi armazenada
            if output.stdout not in unique_outputs:
                unique_outputs.add(output.stdout)

        # Atualiza o texto na caixa de texto rolável com a saída única do nslookup
        result_text.config(state=tk.NORMAL)
        result_text.insert(tk.INSERT, "\n\n======================================================= Transferência de Zona DNS ====================================================\n\n")
        for output in unique_outputs:
            result_text.insert(tk.INSERT, f"{output}\n")
        result_text.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao realizar a transferência de zona DNS: {e}")

# Configuração da interface gráfica
root = tk.Tk()
root.wm_state('zoomed')
root.title("Provedor de Internet e Cabeçalhos HTTP Transferência de Zona DNS")

tk.Label(root, text="Digite a URL do website", font=("TkDefaultFont", 12)).pack(pady=5)
url_entry = tk.Entry(root, width=30, font=("TkDefaultFont", 12))
url_entry.pack(pady=5)

tk.Button(root, text="Obter Informações", command=obter_provedor_internet, font=("TkDefaultFont", 12), bg="#0bfc03").pack(pady=5)
tk.Button(root, text="Transferência de Zona DNS", command=dns_transferencia_zona, font=("TkDefaultFont", 12), bg="#03fcf8").pack(pady=5)

result_text = scrolledtext.ScrolledText(root, width=130, height=43, state=tk.DISABLED, font=("TkDefaultFont", 12))
result_text.pack(pady=5)

root.mainloop()
