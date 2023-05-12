import tkinter as tk
import subprocess
import re
from tkinter import ttk

def execute_cmd():
    url = url_entry.get()
    cmd = "curl -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36' -L -s {0}".format(url)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, bufsize=1, universal_newlines=True)
    output = []
    progress = 0
    for line in process.stdout:
        output.append(line)
        links = set(re.findall(r'http[s]?:\/\/[\w\.\-\/\?\&\=]+', line))
        for link in links:
            output_text.insert("end", link + "\n")
          
        progress = min(progress + 1, 100)        
        progress_var.set(progress)
        window.update_idletasks()
    process.stdout.close()
    process.wait()

# limpar
def clear_output():
    # Limpa a caixa de texto output_text
    output_text.delete("1.0", "end")

    # Reseta a barra de progresso
    progress_var.set(0)

# sair
def quit_app():
    window.destroy()

# GUI
window = tk.Tk()
window.title("Agente Deepweb")
window.geometry("800x600")
window.wm_state('zoomed')

url_label = tk.Label(text="Digite a URL ou nome do site para consultar", font=("Arial", 13, "bold"))
url_label.pack(pady=(20, 0))

url_entry = tk.Entry(window, width=40, font=("Arial", 15))
url_entry.pack(pady=(0, 20))

run_button = tk.Button(text="Consultar", command=execute_cmd, bg="blue", fg="white", font=("Arial Bold", 14))
run_button.pack()

output_label = tk.Label(text="Links encontrados", font=("Arial", 13, "bold"))
output_label.pack(pady=(20, 0))

output_text = tk.Text(height=35, width=100)
output_text.pack()

# botão de limpar
clear_button = tk.Button(text="Limpar", command=clear_output, bg="blue", fg="white", font=("bold"))
clear_button.pack(pady=(20, 0))

# botão de sair
quit_button = tk.Button(text="Sair", command=quit_app, bg="red", fg="white", font=("bold"))
quit_button.pack(pady=(20, 0))

# barra de progresso
progress_var = tk.DoubleVar()

style = ttk.Style()
style.theme_use('default')
style.configure('green.Horizontal.TProgressbar', background='#00FF00')

progress_bar = ttk.Progressbar(window, orient=tk.HORIZONTAL, mode='determinate', variable=progress_var, style='green.Horizontal.TProgressbar', length=500)
progress_bar.pack(pady=(20, 0))

window.mainloop()
