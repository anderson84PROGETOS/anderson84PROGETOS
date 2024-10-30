import subprocess
import re
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox

# Função para escanear redes Wi-Fi usando netsh e formatar a saída
def scan_wifi_windows():
    output_text.delete(1.0, tk.END)  # Limpa a saída anterior
    output_text.insert(tk.END, "Escaneando redes Wi-Fi disponíveis no Windows")
    try:
        # Executa o comando e define a codificação para cp850
        result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='cp850')
        
        # Divide a saída em blocos, um para cada rede Wi-Fi
        redes = result.split("\n\n")
        
        # Regex para extrair informações necessárias
        padrao_ssid = re.compile(r"SSID \d+ : (.+)\n")
        padrao_bssid = re.compile(r"BSSID \d+\s+: (.+)\n")
        padrao_sinal = re.compile(r"Sinal\s+: (\d+)%\n")
        padrao_tipo_radio = re.compile(r"Tipo de rádio\s+: (.+)\n")
        padrao_canal = re.compile(r"Canal\s+: (\d+)")
        padrao_autenticacao = re.compile(r"Autenticação\s+: (.+)\n")
        padrao_criptografia = re.compile(r"Criptografia\s+: (.+)\n")

        # Dicionário para mapear criptografias técnicas para tipos comuns
        tipos_criptografia = {
            "WEP": "WEP",
            "TKIP": "WPA",
            "CCMP": "WPA2",
            "GCMP": "WPA3"
        }

        # Loop para processar cada rede Wi-Fi detectada
        for rede in redes:
            ssid = padrao_ssid.search(rede)
            bssid = padrao_bssid.search(rede)
            sinal = padrao_sinal.search(rede)
            tipo_radio = padrao_tipo_radio.search(rede)
            canal = padrao_canal.search(rede)
            autenticacao = padrao_autenticacao.search(rede)
            criptografia = padrao_criptografia.search(rede)
            
            # Exibindo a rede formatada
            if ssid:
                output_text.insert(tk.END, f"SSID: {ssid.group(1)}\n\n")
            if bssid:
                output_text.insert(tk.END, f"BSSID: {bssid.group(1)}\n\n")
            if sinal:
                output_text.insert(tk.END, f"Sinal: {sinal.group(1)}%\n\n")
            if tipo_radio:
                output_text.insert(tk.END, f"Tipo de rádio: {tipo_radio.group(1)}\n\n")
            if canal:
                output_text.insert(tk.END, f"Canal: {canal.group(1)}\n\n")
            if autenticacao:
                output_text.insert(tk.END, f"Autenticação: {autenticacao.group(1)}\n\n")
            if criptografia:
                # Mapeia o tipo de criptografia para um tipo mais comum
                tipo_segurança = tipos_criptografia.get(criptografia.group(1), criptografia.group(1))
                output_text.insert(tk.END, f"Criptografia (Segurança): {tipo_segurança}\n")
                
            # Separador entre redes
            output_text.insert(tk.END, "\n\n\n\n\n")
    
    except subprocess.CalledProcessError as e:
        output_text.insert(tk.END, f"Erro ao executar netsh: {e}\n")

# Função para salvar os resultados em um arquivo .txt
def save_results():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        try:
            with open(file_path, "w") as file:
                file.write(output_text.get(1.0, tk.END))
            messagebox.showinfo("Sucesso", f"Resultados salvos em {file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")

# Configuração da interface gráfica
app = tk.Tk()
app.title("Scanner de Redes Wi-Fi")
app.geometry("1250x950")
app.wm_state('zoomed')

# Botão para iniciar o escaneamento
scan_button = tk.Button(app, text="Escanear Redes Wi-Fi", command=scan_wifi_windows, font=("TkDefaultFont", 11, "bold"), bg='#29eb0c')
scan_button.pack(pady=10)

# Botão para salvar resultados
save_button = tk.Button(app, text="Salvar Resultados", command=save_results, font=("TkDefaultFont", 11, "bold"), bg='#eb0c38')
save_button.pack(pady=10)

# Caixa de texto para exibir os resultados
output_text = scrolledtext.ScrolledText(app, width=100, height=43, font=("TkDefaultFont", 12))
output_text.pack()

# Execução da interface gráfica
app.mainloop()
