import requests
import re
import socket
import tkinter as tk
from tkinter import font

def search_subdomains():
    url = url_entry.get()
    response = requests.get(f'http://{url}')
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    subdomains_listbox.delete(0, tk.END)
    for subdomain in subdomains:
        try:
            ip_address = socket.gethostbyname(subdomain.split('//')[1])
        except socket.gaierror:
            ip_address = 'Unknown'
        subdomains_listbox.insert(tk.END, f'{subdomain}  ➡️ {ip_address}')
        subdomains_listbox.itemconfig(tk.END, {'fg': 'black'})
        subdomains_listbox.config(font=('TkDefaultFont', 11, 'bold'))       
        

def copy_all():
    subdomains_list = subdomains_listbox.get(0, tk.END)
    subdomains_str = '\n'.join(subdomains_list)
    window.clipboard_clear()
    window.clipboard_append(subdomains_str)

def clear_listbox():
    subdomains_listbox.delete(0, tk.END)

window = tk.Tk()
window.wm_state('zoomed')
window.title('Subdomain Search')

clear_button = tk.Button(window, text='Clear All', command=clear_listbox, padx=5, pady=5, bg='#FF1493', fg='black', font=('TkDefaultFont', 11, 'bold'))
clear_button.pack(side=tk.RIGHT, padx=50, pady=(0, 850))


copy_button = tk.Button(window, text='Copy All', command=copy_all, padx=5, pady=5, bg='#00FFFF', fg='black', font=('TkDefaultFont', 11, 'bold'))
copy_button.pack(side=tk.RIGHT, padx=50, pady=(0, 850))

bold_font = font.Font(weight='bold')

url_label = tk.Label(window, text='Digite nome website (ex: google.com):', padx=10, font=bold_font)
url_label.pack(side=tk.TOP)

url_entry = tk.Entry(window, font=bold_font)
url_entry.pack(side=tk.TOP, padx=5, pady=5, ipadx=95, ipady=5)

search_button = tk.Button(window, text='Search', command=search_subdomains, padx=5, pady=5, bg='#00FF00', fg='black', font=('TkDefaultFont', 11, 'bold'))
search_button.pack(side=tk.TOP)

subdomains_frame = tk.Frame(window, pady=10)
subdomains_frame.pack()

subdomains_listbox = tk.Listbox(subdomains_frame, width=110, height=50)
subdomains_listbox.pack(side=tk.LEFT, padx=5, pady=5)

scrollbar = tk.Scrollbar(subdomains_frame, orient=tk.VERTICAL, width=20)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

subdomains_listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=subdomains_listbox.yview)


window.mainloop()
