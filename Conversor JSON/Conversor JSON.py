import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import json
import csv
import os

dados_convertidos = None  # variável global para guardar o último JSON convertido

def ler_arquivo_com_fallback(arquivo):
    """Tenta abrir o arquivo em UTF-8, se falhar tenta Latin-1."""
    try:
        with open(arquivo, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(arquivo, encoding="latin-1") as f:
            return f.read()

def converter_para_json(arquivo):
    extensao = os.path.splitext(arquivo)[1].lower()
    try:
        if extensao == ".csv":
            # Tenta abrir CSV com fallback de encoding
            try:
                with open(arquivo, encoding="utf-8") as f:
                    leitor = csv.DictReader(f)
                    dados = list(leitor)
            except UnicodeDecodeError:
                with open(arquivo, encoding="latin-1") as f:
                    leitor = csv.DictReader(f)
                    dados = list(leitor)

        elif extensao == ".json":
            try:
                with open(arquivo, encoding="utf-8") as f:
                    dados = json.load(f)
            except UnicodeDecodeError:
                with open(arquivo, encoding="latin-1") as f:
                    dados = json.load(f)

        else:  # TXT ou qualquer outro formato
            conteudo = ler_arquivo_com_fallback(arquivo)
            linhas = conteudo.splitlines()
            dados = {"linhas": linhas}

        return dados
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível converter: {e}")
        return None

def abrir_arquivo():
    global dados_convertidos
    arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo",
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if arquivo:
        dados = converter_para_json(arquivo)
        if dados is not None:
            dados_convertidos = dados
            txt_output.delete("1.0", tk.END)
            json_formatado = json.dumps(dados, indent=4, ensure_ascii=False)
            txt_output.insert(tk.END, json_formatado)            

def salvar_como_json():
    global dados_convertidos
    if dados_convertidos is None:
        messagebox.showwarning("Atenção", "Nenhum arquivo foi convertido ainda.")
        return
    
    arquivo = filedialog.asksaveasfilename(
        title="Salvar como",
        defaultextension=".json",
        filetypes=[("Arquivo JSON", "*.json")]
    )
    if arquivo:
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados_convertidos, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Sucesso", f"Arquivo salvo em\n\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

# === Interface gráfica ===
root = tk.Tk()
root.title("Conversor JSON")
root.geometry("1280x1024")

frame_botoes = tk.Frame(root)
frame_botoes.pack(pady=5)

btn_abrir = tk.Button(frame_botoes, text="Abrir arquivo e converter", bg="#03fc0b", fg="black", command=abrir_arquivo)
btn_abrir.grid(row=0, column=0, padx=5)

btn_salvar = tk.Button(frame_botoes, text="Salvar como JSON", bg="#fc9d03", fg="black", command=salvar_como_json)
btn_salvar.grid(row=0, column=1, padx=5)

txt_output = scrolledtext.ScrolledText(root, width=150, height=54)
txt_output.pack(pady=5)

root.mainloop()
