import tkinter as tk
import subprocess
import re

def execute_cmd():
    url = url_entry.get()
    cmd = "curl -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36' -L -s {0}".format(url)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    # Extrai os links da saída usando expressões regulares
    links = set(re.findall(r'http[s]?:\/\/[\w\.\-\/\?\&\=]+', output.decode()))

    # Exibe os links na caixa de texto
    output_text.delete("1.0", "end")
    for link in links:
        output_text.insert("end", link + "\n")

# limpar
def clear_output():
    # Clear the output_text widget
    output_text.delete("1.0", "end")

# sair
def quit_app():
    window.destroy()

# GUI
window = tk.Tk()
window.title("Agente Deepweb")
window.geometry("600x400")
window.wm_state('zoomed')

url_label = tk.Label(text="Digite A URL ou Nome do site Para Consultar", font=("Arial", 13, "bold"))

url_label.pack()


url_entry = tk.Entry(window, width=120, font=("Arial", 15))
url_entry.place(x=50, y=25, width=480, height=40)

run_button = tk.Button(text="Click Para Consultar", command=execute_cmd, bg="blue", fg="white", font=("Arial Bold", 14))
run_button.pack()

# botao de sair
quit_button = tk.Button(text="SAIR", command=quit_app, bg="red", fg="white", font=("bold"))
quit_button.pack(side="right", anchor="n")

output_label = tk.Label(text="")
output_label.pack()

output_text = tk.Text(height=50, width=150)
output_text.pack()

# botao de limpar
clear_button = tk.Button(text="LIMPAR", command=clear_output, bg="blue", fg="white", font=("bold"))
clear_button.pack()

window.mainloop()

