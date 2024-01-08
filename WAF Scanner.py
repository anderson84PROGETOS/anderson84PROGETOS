import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import itertools
from ttkthemes import ThemedStyle
from PIL import Image, ImageTk
from io import BytesIO

# Lista de WAFs conhecidos (em minúsculas)
known_wafs = [
    "cloudflare",
    "amazon",
    "akamai",
    "cisco",
    "imperva",
    "f5 networks",
    "fortinet",
    "sucuri",
    "radware",
    "incapsula",
    "barracuda networks",
    "azure (microsoft)",
    "netscaler (citrix)",
    "modsecurity",
    "wordfence",
    "sitelock",
    "akamai kona site defender",
    "cloudfront (amazon)",
    "stackpath",
    "sucuri cloudproxy",
    "distil networks",
    "arbor networks",
    "qualys",
    "zscaler",
    "symantec",
    "kaspersky",
    "mcafee",
    "trend micro",
    "check point",
    "palo alto networks",
    "sophos",
    "eset",
    "webroot",
    "bitdefender",
    "kaspersky",
    "tenable",
    "qualys",
    "rapid7",
    "darktrace",
    "carbon black",
    "crowdstrike",
    "fireeye",
    "splunk",
    "varonis",
    "ibm qradar",
    "alienvault",
    "solarwinds",
    "logrhythm",
    "nortonlifelock",
    "comodo",
    "mcafee secure",
    "securi",
    "esentire",
    "defendify",
    "armor",
    "akismet",
]

# Lista de User-Agents
user_agents = [  
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59', 
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z Safari/537.36',
    'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; AdsBot-Google-Mobile; +http://www.google.com/mobile/adsbot.html)', 
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) coc_coc_browser/50.0.125 Chrome/44.0.2403.125 Safari/537.36',
    

]

def download_icon(url):
    response = requests.get(url)
    icon_data = BytesIO(response.content)
    return Image.open(icon_data)

def scan_website():
    url = url_entry.get()

    if url:
        try:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)

            user_agent = next(user_agents_cycle)
            headers = {'User-Agent': user_agent}
            response = requests.get(url, headers=headers)
            headers = response.headers

            result_text.insert(tk.END, f"Cabeçalhos recebidos com User-Agent {user_agent}:\n\n")
            for header, value in headers.items():
                result_text.insert(tk.END, f"\n{header}: {value}\n")

            detected_wafs = [waf for waf in known_wafs if ('server' in headers and waf in headers['server'].lower()) or ('x-powered-by' in headers and waf in headers['x-powered-by'].lower())]

            if detected_wafs:
                result_text.insert(tk.END, "\n\n\n\nWAFs detectados:  ")
                for detected_waf in detected_wafs:
                    result_text.insert(tk.END, f"{detected_waf}")
            else:
                result_text.insert(tk.END, "\nNenhum WAF conhecido detectado para este User-Agent.")

            result_text.config(state=tk.DISABLED)

        except Exception as e:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"Erro ao analisar o site: {str(e)}")
            result_text.config(state=tk.DISABLED)
    else:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Por favor, insira a URL do site.")
        result_text.config(state=tk.DISABLED)

# Configuração da interface gráfica
window = tk.Tk()
window.wm_state('zoomed')
window.title("WAF Scanner")

# Configurando o estilo temático
style = ThemedStyle(window)
style.set_theme("itft1")

# URL do ícone
icon_url = "https://www.akontech.ru/wp-content/uploads/2020/07/solution_waf.png"

# Baixar o ícone da web
icon_image = download_icon(icon_url)

# Converter a imagem para o formato TKinter
tk_icon = ImageTk.PhotoImage(icon_image)

# Definir o ícone da janela
window.iconphoto(True, tk_icon)

# Entrada para a URL
url_label = ttk.Label(window, text="Digite a URL do WebSite")
url_label.pack(pady=10)
url_entry = ttk.Entry(window, width=40, font=("Arial", 12))
url_entry.pack(pady=10)

# Botão para iniciar a varredura
scan_button = ttk.Button(window, text="WAF Scanner", command=scan_website)
scan_button.pack(pady=10)

# Área de exibição dos resultados
result_text = scrolledtext.ScrolledText(window, width=130, height=40, font=("Arial", 12))
result_text.pack(pady=10)
result_text.config(state=tk.DISABLED)

# Initialize the cycle of user agents
user_agents_cycle = itertools.cycle(user_agents)

# Iniciar o loop da interface gráfica
window.mainloop()
