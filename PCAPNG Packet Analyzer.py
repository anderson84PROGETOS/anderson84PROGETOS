import os
import tkinter as tk
from tkinter import filedialog, messagebox
from scapy.all import rdpcap
import requests

def get_ips_from_packet(packet):
    """Extrai IPs de um pacote."""
    ips = set()
    if packet.haslayer('IP'):
        src_ip = packet['IP'].src
        dst_ip = packet['IP'].dst
        ips.add(src_ip)
        ips.add(dst_ip)
    return ips

def load_file():
    """Abre uma caixa de diálogo para selecionar o arquivo .pcapng e processa os IPs."""
    file_name = filedialog.askopenfilename(
        title="Selecione o arquivo .pcapng",
        filetypes=[("Arquivos PCAPNG", "*.pcapng")]
    )
    
    if not file_name:
        return
    
    try:
        if not os.path.isfile(file_name):
            raise FileNotFoundError(f"Arquivo {file_name} não encontrado.")
        
        packets = rdpcap(file_name)
        ips = set()
        
        for packet in packets:
            ips.update(get_ips_from_packet(packet))
        
        results = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        for ip in ips:
            response = requests.get(f'https://ipapi.co/{ip}/json/', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                ip_addr = data.get('ip', 'N/A')
                city = data.get('city', 'N/A')
                region = data.get('region', 'N/A')
                country = data.get('country_name', 'N/A')
                latitude = data.get('latitude', 'N/A')
                longitude = data.get('longitude', 'N/A')
                
                result = (f"IP: {ip_addr}\n"
                          f"Location: {city}, {region}, {country}\n"
                          f"Latitude: {latitude}, Longitude: {longitude}\n")
                if latitude != 'N/A' and longitude != 'N/A':
                    google_maps_url = f"https://www.google.com/maps/place/{latitude},{longitude}"
                    result += f"Google Maps: {google_maps_url}\n"
                
                results.append(result)
            else:
                results.append(f"Erro ao obter dados para IP: {ip}")
        
        results_text = "\n".join(results)
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, results_text)
        
        save_option = messagebox.askyesno("Salvar Resultados", "Deseja salvar todas as informações em um arquivo?")
        if save_option:
            output_file = filedialog.asksaveasfilename(
                title="Salvar como",
                defaultextension=".txt",
                filetypes=[("Arquivos de texto", "*.txt")]
            )
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(results_text)
                messagebox.showinfo("Sucesso", f"Informações salvas em: {output_file}")
    
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

# Criar a janela principal
root = tk.Tk()
root.wm_state('zoomed')
root.title("PCAPNG Packet Analyzer")

# Botão para carregar o arquivo
load_button = tk.Button(root, text="Carregar Arquivo PCAPNG", command=load_file, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
load_button.pack(pady=10)

# Área de texto para mostrar os resultados
text_output = tk.Text(root, wrap=tk.WORD, height=45, width=100, font=("TkDefaultFont", 12, "bold"))
text_output.pack(padx=10, pady=10)

# Iniciar o loop da interface gráfica
root.mainloop()
