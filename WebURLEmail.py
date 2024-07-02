import requests
import urllib.parse
from collections import deque
import re
import tkinter as tk
from tkinter import scrolledtext
from tkinter.ttk import Progressbar, Style as TkStyle
from bs4 import BeautifulSoup

def process_url():
    user_url = url_entry.get()
    if not user_url.startswith(('http:', 'https:')):
        user_url = 'http://' + user_url
    urls = deque([user_url])
    scrapped_urls = set()
    emails = set()
    count = 0

    # Cabeçalhos HTTP para evitar erro 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    while urls and count < 100:
        url = urls.popleft()
        count += 1

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Check for HTTP request errors
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                continue
            else:
                continue
        except requests.exceptions.RequestException as e:
            continue
        except KeyboardInterrupt:
            log_text.insert(tk.END, '[-] Closing!\n')
            log_text.see(tk.END)
            break

        scrapped_urls.add(url)
        parts = urllib.parse.urlsplit(url)
        base_url = '{0.scheme}://{0.netloc}'.format(parts)
        path = url[:url.rfind('/') + 1] if '/' in parts.path else url
        log_text.insert(tk.END, f'{url}\n')
        log_text.see(tk.END)

        new_emails = set(re.findall(r'[a-z0-9\. \-+_]+@[a-z0-9\. \-+_]+\.[a-z]+', response.text, re.I))
        emails.update(new_emails)
        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.find_all("a"):
            link = anchor.get('href', '')
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith(('http:', 'https:')):
                link = urllib.parse.urljoin(url, link)
            if link not in urls and link not in scrapped_urls:
                urls.append(link)
        
        # Update progress bar gradually
        progress = count / 100
        progress_bar['value'] = progress * 100
        root.update()

    log_text.insert(tk.END, '\n\n################## Email ######################\n\n')
    log_text.insert(tk.END, '\n'.join(emails))
    log_text.insert(tk.END, f'\n\n\nForam Encontradas URL: {len(scrapped_urls)}\n')
    log_text.insert(tk.END, f'\nForam Encontrados Email: {len(emails)}\n')
    log_text.see(tk.END) 
    # Set progress bar to 100% when done
    progress_bar['value'] = 100

root = tk.Tk()
root.wm_state('zoomed')
root.title("Web URL Email")
root.geometry("500x450")

url_label = tk.Label(root, text="Insira o Nome ou a URL WebSite")
url_label.pack()
url_label.config(font=("Arial", 12, "bold"))

url_entry = tk.Entry(root, width=30)
url_entry.pack()
url_entry.config(font=("Arial", 12, "bold"))

start_button = tk.Button(root, text="Iniciar", command=process_url)
start_button.pack(pady=10)
start_button.config(font=("Arial", 12, "bold"), background="#00FFFF")

style = TkStyle()
style.theme_use('default')
style.configure('green.Horizontal.TProgressbar', background='#00FF00')
progress_bar = Progressbar(root, orient=tk.HORIZONTAL, mode='determinate', style='green.Horizontal.TProgressbar', length=275)
progress_bar.pack(pady=10)

log_text = scrolledtext.ScrolledText(root, width=130, height=41, font=("Arial", 12, "bold"))
log_text.pack()

root.mainloop()
