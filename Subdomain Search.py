import requests
import re
import socket
import tkinter as tk

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
        subdomains_listbox.config(font=('TkDefaultFont', 9, 'bold'))       
        

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

url_label = tk.Label(window, text='Digite nome website (ex: google.com):', padx=10)
url_label.pack(side=tk.LEFT)

url_entry = tk.Entry(window)
url_entry.pack(side=tk.LEFT, padx=5, pady=5, ipadx=95, ipady=5)

search_button = tk.Button(window, text='Search', command=search_subdomains, padx=5, pady=5)
search_button.pack(side=tk.LEFT)

subdomains_frame = tk.Frame(window, pady=10)
subdomains_frame.pack()

subdomains_listbox = tk.Listbox(subdomains_frame, width=100, height=50)
subdomains_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(subdomains_frame, orient=tk.VERTICAL, width=20)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

subdomains_listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=subdomains_listbox.yview)

copy_button = tk.Button(window, text='Copy All', command=copy_all, padx=5, pady=5)
copy_button.pack(side=tk.BOTTOM, padx=5, pady=10)

clear_button = tk.Button(window, text='Clear All', command=clear_listbox, padx=5, pady=5)
clear_button.pack(side=tk.BOTTOM, padx=5, pady=10)

window.mainloop()
