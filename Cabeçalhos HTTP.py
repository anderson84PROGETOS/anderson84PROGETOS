import tkinter as tk
import subprocess

def get_headers():
    url = url_entry.get()
    headers = subprocess.check_output(['curl', '-s', '--head', '-A', 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666', url])
    headers_text.delete('1.0', tk.END)
    headers_text.insert(tk.END, headers.decode())

def clear_fields():
    url_entry.delete(0, tk.END)
    headers_text.delete('1.0', tk.END)

root = tk.Tk()
root.wm_state('zoomed')
root.title('Exibir cabeçalhos HTTP')

url_label = tk.Label(root, text='Digite a URL Do website', font=('TkDefaultFont', 12, 'bold'))
url_label.grid(row=0, column=0, padx=10)

url_entry = tk.Entry(root, width=40, font=('TkDefaultFont', 12, 'bold'))
url_entry.grid(row=0, column=1, sticky='W')

get_headers_button = tk.Button(root, text='Exibir cabeçalhos', command=get_headers, font=('TkDefaultFont', 12, 'bold'), bg='#00FF00')
get_headers_button.grid(row=1, column=0, columnspan=2, pady=10)

headers_label = tk.Label(root, text='Cabeçalhos', font=('TkDefaultFont', 12, 'bold'))
headers_label.grid(row=2, column=0, padx=20)

headers_text = tk.Text(root, width=157, height=45, padx=5, pady=0)
headers_text.configure(font=('TkDefaultFont', 11, 'bold'))
headers_text.grid(row=3, column=0, columnspan=2)

clear_button = tk.Button(root, text='Limpar tudo', command=clear_fields, font=('TkDefaultFont', 12, 'bold'), bg='firebrick1')
clear_button.grid(row=2, column=1, columnspan=2, pady=5)

root.mainloop()
