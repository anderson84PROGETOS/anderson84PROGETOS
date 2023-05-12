import requests
import re
import socket
import tkinter as tk
from tkinter import font
from tkinter import ttk

def search_subdomains():
    url = url_entry.get()
    if not url.startswith('http'):
        url = f'http://{url}'
    response = requests.get(url)
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    subdomains_listbox.delete(0, tk.END)
    num_subdomains = len(subdomains)
    progress_var.set(0)
    window.update_idletasks()
    for i, subdomain in enumerate(subdomains):
        try:
            ip_address = socket.gethostbyname(subdomain.split('//')[1])
        except socket.gaierror:
            ip_address = 'Unknown'
        subdomains_listbox.insert(tk.END, f'{subdomain}  ➡️ {ip_address}')
        subdomains_listbox.itemconfig(tk.END, {'fg': 'black'})
        subdomains_listbox.config(font=('TkDefaultFont', 11, 'bold'))
        progress_percent = min(100, int((i + 1) / num_subdomains * 100))
        progress_var.set(progress_percent)
        window.update_idletasks()

def copy_all():
    subdomains_list = subdomains_listbox.get(0, tk.END)
    subdomains_str = '\n'.join(subdomains_list)
    window.clipboard_clear()
    window.clipboard_append(subdomains_str)

def clear_listbox():
    subdomains_listbox.delete(0, tk.END)
    progress_var.set(0)

def clear_progress():
    progress_var.set(0)

window = tk.Tk()
title_label = ttk.Label(window, text='Agente Web', font=('TkDefaultFont', 14, 'bold'))
title_label.pack(side=tk.TOP, anchor='w', padx=10, pady=10)

window.attributes('-fullscreen', True)
window.attributes('-toolwindow', False)
window.attributes('-topmost', True)

exit_button = tk.Button(window, text='Exit', command=window.quit, padx=5, pady=5, bg='red', fg='white', font=('TkDefaultFont', 11, 'bold'))
exit_button.pack(side=tk.RIGHT, padx=5, pady=(0, 850))

minimize_button = tk.Button(window, text='Minimizar', command=window.iconify, padx=5, pady=5, font=('TkDefaultFont', 11))
minimize_button.pack(side=tk.RIGHT, padx=5, pady=(0, 960))


clear_all_button = tk.Button(window, text='Clean All', command=clear_listbox, padx=5, pady=5, bg='#FF1493', fg='black', font=('TkDefaultFont', 11, 'bold'))
clear_all_button.pack(side=tk.RIGHT, padx=5, pady=(0, 850))

copy_button = tk.Button(window, text='Copy All', command=copy_all, padx=5, pady=5, bg='#00FFFF', fg='black', font=('TkDefaultFont', 11, 'bold'))
copy_button.pack(side=tk.RIGHT, padx=50, pady=(0, 850))

bold_font = font.Font(weight='bold')

url_label = tk.Label(window, text='Digite o Nome do site ou a url do website (ex:google.com  ou  https://google.com)', padx=10, font=bold_font)
url_label.pack(side=tk.TOP)

url_entry = tk.Entry(window, font=bold_font)
url_entry.pack(side=tk.TOP, padx=5, pady=5, ipadx=95, ipady=5)

search_button = tk.Button(window, text='Search', command=search_subdomains, padx=15, pady=1, bg='#FFA500', fg='black', font=('TkDefaultFont', 11, 'bold'))
search_button.pack(side=tk.TOP)

subdomains_frame = tk.Frame(window, pady=10)
subdomains_frame.pack()

subdomains_listbox = tk.Listbox(subdomains_frame, width=110, height=50)
subdomains_listbox.pack(side=tk.LEFT, padx=5, pady=(30, 5))

scrollbar = tk.Scrollbar(subdomains_frame, orient=tk.VERTICAL, width=20)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

subdomains_listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=subdomains_listbox.yview)

progress_var = tk.DoubleVar()

style = ttk.Style()
style.theme_use('default')
style.configure('green.Horizontal.TProgressbar', background='#00FF00')
progress_bar = ttk.Progressbar(window, orient=tk.HORIZONTAL, mode='determinate', variable=progress_var, style='green.Horizontal.TProgressbar', length=670)
progress_bar.place(x=85, y=160) 

window.mainloop()
