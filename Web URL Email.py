from bs4 import BeautifulSoup
import requests
import requests.exceptions
import urllib.parse
from collections import deque
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter.ttk import Progressbar, Style as TkStyle
import colorama
from colorama import Fore, Back, Style as AnsiStyle

colorama.init(autoreset=True)

def process_url():
    user_url = url_entry.get()
    if not user_url.startswith('http'):
        user_url = 'http://' + user_url
    urls = deque([user_url])
    scrapped_urls = set()
    emails = set()
    count = 0
    total_urls = len(urls)
    progress_bar['maximum'] = 100  # Define o valor máximo da barra de progresso como 100
    try:
        while len(urls):
            count += 1
            if count == 100:
                break
            url = urls.popleft()
            scrapped_urls.add(url)
            parts = urllib.parse.urlsplit(url)
            base_url = '{0.scheme}://{0.netloc}'.format(parts)
            path = url[:url.rfind('/') + 1] if '/' in parts.path else url
            log_text.insert(tk.END, '%s\n' % url)
            log_text.see(tk.END)
            try:
                response = requests.get(url)
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                continue
            new_emails = set(re.findall(r'[a-z0-9\. \-+_]+@[a-z0-9\. \-+_]+\.[a-z]+', response.text, re.I))
            emails.update(new_emails)
            soup = BeautifulSoup(response.text, features="html.parser")
            for anchor in soup.find_all("a"):
                link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
                if link.startswith('/'):
                    link = base_url + link
                elif not link.startswith('http'):
                    link = path + link
                if not link in urls and not link in scrapped_urls:
                    urls.append(link)

            progress_value = min(count, 100)  # Limita o valor máximo do progresso a 100
            progress_bar['value'] = progress_value
            root.update_idletasks()  # Atualiza a interface gráfica

    except KeyboardInterrupt:
        log_text.insert(tk.END, '[-] Closing!\n')
        log_text.see(tk.END)
    log_text.insert(tk.END, '\n################## E-mails : ######################\n\n')
    log_text.insert(tk.END, '\n'.join(emails))
    log_text.see(tk.END)

root = tk.Tk()
root.wm_state('zoomed')
root.title("Web URL Email")
root.geometry("500x450")

url_label = tk.Label(root, text="Insira Nome URL WebSite A Ser Verificado")
url_label.pack()
url_label.config(font=("Arial", 12, "bold"))  # Configura a fonte negrito para o rótulo

url_entry = tk.Entry(root, width=50)
url_entry.pack()
url_entry.config(font=("Arial", 12, "bold"))  # Configura a fonte negrito para a entrada de URL

start_button = tk.Button(root, text="Iniciar", command=process_url)
start_button.pack(pady=10)
start_button.config(font=("Arial", 12, "bold"), background="#00FFFF")  # Configura a fonte negrito e a cor de fundo do botão

style = TkStyle()
style.theme_use('default')
style.configure('green.Horizontal.TProgressbar', background='#00FF00')
progress_bar = Progressbar(root, orient=tk.HORIZONTAL, mode='determinate', style='green.Horizontal.TProgressbar', length=400)  # Ajusta o tamanho da barra de progresso para 400
progress_bar.pack(pady=5)

log_text = scrolledtext.ScrolledText(root, width=155, height=50)
log_text.pack()

root.mainloop()
