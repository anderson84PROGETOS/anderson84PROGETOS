import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

def texto_para_binario(s: str) -> str:
    return ' '.join(f'{ord(c):08b}' for c in s)

def binario_para_texto(bstr: str) -> str:
    bits = ''.join(ch for ch in bstr if ch in '01')
    if len(bits) % 8 != 0:
        raise ValueError(f'Quantidade de bits ({len(bits)}) não é múltipla de 8.')
    chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
    return ''.join(chars)

def detalhar_binario(bstr: str) -> str:
    bits = ''.join(ch for ch in bstr if ch in '01')
    if len(bits) % 8 != 0:
        return "Bits não múltiplos de 8."
    pares = [bits[i:i+8] for i in range(0, len(bits), 8)]
    linhas = [f"{b} = {chr(int(b,2))}" for b in pares]
    return "\n".join(linhas)

def acao_criptografar():
    try:
        saida.delete('1.0', tk.END)
        detalhe.delete('1.0', tk.END)
        texto = entrada.get('1.0', tk.END).rstrip('\n')
        binario = texto_para_binario(texto)
        saida.insert(tk.END, binario)
        detalhe.insert(tk.END, detalhar_binario(binario))
        status.set('Texto convertido para binário.')
    except Exception as e:
        messagebox.showerror('Erro', str(e))

def acao_descriptografar():
    try:
        saida.delete('1.0', tk.END)
        detalhe.delete('1.0', tk.END)
        binario = entrada.get('1.0', tk.END)
        texto = binario_para_texto(binario)
        saida.insert(tk.END, texto)
        detalhe.insert(tk.END, detalhar_binario(binario))
        status.set('Binário convertido para texto.')
    except Exception as e:
        messagebox.showerror('Erro ao descriptografar', str(e))

def acao_abrir_txt():
    caminho = filedialog.askopenfilename(
        title='Abrir arquivo .txt com binário',
        filetypes=[('Arquivos de texto', '*.txt'), ('Todos os arquivos', '*.*')]
    )
    if not caminho:
        return
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        entrada.delete('1.0', tk.END)
        entrada.insert(tk.END, conteudo)
        acao_descriptografar()
        status.set(f'Arquivo carregado: {caminho}')
    except Exception as e:
        messagebox.showerror('Erro ao abrir arquivo', str(e))

def acao_salvar_saida():
    caminho = filedialog.asksaveasfilename(
        defaultextension='.txt',
        filetypes=[('Arquivos de texto', '*.txt')],
        title='Salvar tudo como'
    )
    if not caminho:
        return
    try:
        conteudo = []
        conteudo.append("=== Entrada ===\n")
        conteudo.append(entrada.get('1.0', tk.END).strip() + "\n\n")
        conteudo.append("\n\n=== Saída ===\n")
        conteudo.append(saida.get('1.0', tk.END).strip() + "\n\n")
        conteudo.append("\n\n=== Detalhe (binário = caractere) ===\n")
        conteudo.append(detalhe.get('1.0', tk.END).strip() + "\n")

        with open(caminho, 'w', encoding='utf-8') as f:
            f.write("".join(conteudo))

        status.set(f'Salvo em: {caminho}')
        messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n\nLocal: {caminho}")
    except Exception as e:
        messagebox.showerror('Erro ao salvar', str(e))

# --- GUI ---
root = tk.Tk()
root.title('Criptografar Descriptografar Binário')
root.geometry("1000x850")

# Criando um label com fonte personalizada
label = tk.Label(root, text="Criptografar Descriptografar Binário", font=("Arial", 12, "bold"))
label.pack(pady=1)

lbl_in = tk.Label(root, text='Entrada (texto OU binário)')
lbl_in.pack(anchor='w', padx=10, pady=(10, 0))

entrada = ScrolledText(root, height=6, wrap='word')
entrada.pack(fill='both', expand=True, padx=10, pady=(0, 10))

frm_btns = tk.Frame(root)
frm_btns.pack(fill='x', padx=10, pady=(0, 10))

btn_enc = tk.Button(frm_btns, text='Criptografar → Binário', bg="#d16b04", fg="black", command=acao_criptografar)
btn_enc.pack(side='left')

btn_dec = tk.Button(frm_btns, text='Descriptografar → Texto', bg="#03e8fc", fg="black", command=acao_descriptografar)
btn_dec.pack(side='left', padx=10)

btn_open = tk.Button(frm_btns, text='Abrir .txt', bg="#03fc24", fg="black", command=acao_abrir_txt)
btn_open.pack(side='left', padx=10)

btn_save = tk.Button(frm_btns, text='Salvar Resultado', bg="#fc9d03", fg="black", command=acao_salvar_saida)
btn_save.pack(side='right')

lbl_out = tk.Label(root, text='Saída')
lbl_out.pack(anchor='w', padx=10, pady=(0, 0))

saida = ScrolledText(root, height=4, wrap='word')
saida.pack(fill='both', expand=True, padx=10, pady=(0, 10))

lbl_det = tk.Label(root, text='Detalhe (binário = caractere)')
lbl_det.pack(anchor='w', padx=10, pady=(0, 0))

detalhe = ScrolledText(root, height=8, wrap='word')
detalhe.pack(fill='both', expand=True, padx=10, pady=(0, 10))

status = tk.StringVar(value='Pronto.')
lbl_status = tk.Label(root, textvariable=status, anchor='w')
lbl_status.pack(fill='x', padx=10, pady=(0, 10))

root.minsize(700, 600)
root.mainloop()
