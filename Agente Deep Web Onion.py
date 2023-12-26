import requests
import re
import socket
import tkinter as tk
from tkinter import ttk, font, filedialog, scrolledtext
from urllib.parse import urlparse
from ttkthemes import ThemedStyle

def save_to_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        subdomains_text = result_text.get("1.0", tk.END)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(subdomains_text)

def get_main_site_ip(url):
    parsed_url = urlparse(url)
    main_site_domain = parsed_url.netloc
    try:
        ip_address = socket.gethostbyname(main_site_domain)
    except socket.gaierror:
        ip_address = 'Unknown'
    return ip_address

def search_subdomains():
    url = url_entry.get()
    if not url.startswith('http'):
        url = f'http://{url}'
    response = requests.get(url)
    subdomains = set(re.findall(
        r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    result_text.delete('1.0', tk.END)  # Clear previous content
    num_subdomains = len(subdomains)
    main_site_ip = get_main_site_ip(url)
    progress_var.set(0)
    window.update_idletasks()

    for i, subdomain in enumerate(subdomains):
        try:
            ip_address = socket.gethostbyname(subdomain.split('//')[1])
        except socket.gaierror:
            ip_address = main_site_ip

        tag = "red" if subdomain.endswith(".onion") else "left"
        result_text.insert(tk.END, f'{subdomain}  ➡️{ip_address}\n\n', (tag,))
        
        progress_percent = min(100, int((i + 1) / num_subdomains * 100))
        progress_var.set(progress_percent)
        window.update_idletasks()

    result_text.tag_configure("red", justify="left", font=('TkDefaultFont', 13, 'bold'), foreground='#18c4c9')
    result_text.tag_configure("left", justify="left", font=('TkDefaultFont', 12, 'bold'))  # Change "center" to "left"
    result_text.tag_add("left", "1.0", "end")  # Change "center" to "left"

    progress_percent = min(100, int((i + 1) / num_subdomains * 100))
    progress_var.set(progress_percent)
    window.update_idletasks()

def copy_all():
    subdomains_text = result_text.get("1.0", tk.END)
    window.clipboard_clear()
    window.clipboard_append(subdomains_text)

def clear_text():
    result_text.delete('1.0', tk.END)
    progress_var.set(0)

window = tk.Tk()
window.wm_state('zoomed')
window.title("Onion Agente Deep Web")

# Configurando o estilo temático
style = ThemedStyle(window)
style.set_theme("itft1")  # Escolha o tema desejado

title_label = ttk.Label(window, text='Onion Agente Deep Web', font=('TkDefaultFont', 15, 'bold'))
title_label.pack(side=tk.TOP, anchor=tk.W, padx=440, pady=20)
bold_font = font.Font(weight='bold')

url_label = tk.Label(window, text='Digite o Nome do site ou a URL do website (ex: google.com ou https://google.com', padx=12, font=bold_font, background='#03fcf8')
url_label.pack(side=tk.TOP, anchor=tk.W, padx=223, pady=5)

clear_all_button = ttk.Button(window, text='Clean All', command=clear_text, style='TButton')
clear_all_button.pack(side=tk.RIGHT, pady=(0, 800), padx=5)

save_button = ttk.Button(window, text='Save to File', command=save_to_file, style='TButton')
save_button.pack(side=tk.RIGHT, padx=5, pady=(0, 800))

url_entry = ttk.Entry(window, font=bold_font)
url_entry.pack(side=tk.TOP, padx=5, pady=5, ipadx=222, ipady=5)

search_button = ttk.Button(window, text='Search', command=search_subdomains, style='TButton')
search_button.pack(side=tk.TOP, pady=2)

result_frame = ttk.Frame(window, padding=10)
result_frame.pack(pady=10)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=100, height=40, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W, pady=15)

progress_var = tk.DoubleVar()
style.configure('green.Horizontal.TProgressbar', background='#05b5f5')
progress_bar = ttk.Progressbar(window, orient=tk.HORIZONTAL, mode='determinate', variable=progress_var, style='green.Horizontal.TProgressbar', length=905)
progress_bar.place(x=90, y=175 + 20)  # Adicionei 20 à posição y

window.mainloop()
