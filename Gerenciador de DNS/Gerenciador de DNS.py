import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess


def display_dns():
    try:
        result = subprocess.check_output(['ipconfig', '/displaydns'], shell=True)
        output.delete(1.0, tk.END)
        output.insert(tk.END, result.decode('latin-1', errors='ignore'))
    except subprocess.CalledProcessError:
        messagebox.showerror("Erro", "Erro ao exibir DNS")


def flush_dns():
    try:
        result = subprocess.check_output(['ipconfig', '/flushdns'], shell=True)
        clear_screen()  # limpa a tela também
        output.insert(tk.END, result.decode('latin-1', errors='ignore'))
        messagebox.showinfo("Sucesso", "DNS limpo com sucesso!")
    except subprocess.CalledProcessError:
        messagebox.showerror("Erro", "Erro ao limpar DNS")


def clear_screen():
    output.delete(1.0, tk.END)


# Janela
root = tk.Tk()
root.title("Gerenciador de DNS")
root.geometry("1000x800")
root.configure(bg="#1e1e1e")  # fundo escuro

# Título
title = tk.Label(root, text="Gerenciador de DNS", font=("Arial", 18, "bold"),bg="#1e1e1e", fg="white")
title.pack(pady=10)

# Frame dos botões
frame_buttons = tk.Frame(root, bg="#1e1e1e")
frame_buttons.pack(pady=10)

# Estilo padrão dos botões
btn_style = {"font": ("Arial", 10, "bold"),"width": 20,"bd": 0,"cursor": "hand2"}

# Botões
btn_show = tk.Button(frame_buttons, text="Mostrar DNS",bg="#0078D7", fg="white", activebackground="#005a9e",command=display_dns, **btn_style)
btn_show.grid(row=0, column=0, padx=10)

btn_flush = tk.Button(frame_buttons, text="Limpar DNS",bg="#28a745", fg="white", activebackground="#1e7e34",command=flush_dns, **btn_style)
btn_flush.grid(row=0, column=1, padx=10)

# Área de texto
output = scrolledtext.ScrolledText(root, wrap=tk.WORD,bg="#2b2b2b", fg="white",insertbackground="white",font=("Consolas", 12))
output.pack(padx=10, pady=10, fill="both", expand=True)

# Rodar
root.mainloop()
