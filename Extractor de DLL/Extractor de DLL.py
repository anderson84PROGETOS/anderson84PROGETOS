import pefile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
import json
import re
import io

exports_raw_names = []
exports_detalhados = []
exports_completos = []
pe = None

def selecionar_arquivo():
    global pe
    caminho = filedialog.askopenfilename(filetypes=[("DLL Files", "*.dll")])
    if caminho:
        entrada_arquivo.delete(0, tk.END)
        entrada_arquivo.insert(0, caminho)
        try:
            with open(caminho, 'rb') as f:
                dados = f.read()
                pe = pefile.PE(data=dados)
                pe.__data__ = io.BytesIO(dados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir DLL:\n{e}")
            return
        extrair_exports(pe)
        mostrar_normal()

def extrair_exports(pe_obj):
    global exports_raw_names, exports_detalhados, exports_completos
    exports_raw_names = []
    exports_detalhados = []
    exports_completos = []
    texto_saida.delete(1.0, tk.END)

    if not hasattr(pe_obj, 'DIRECTORY_ENTRY_EXPORT'):
        texto_saida.insert(tk.END, "Nenhuma função exportada encontrada.\n")
        return

    for exp in pe_obj.DIRECTORY_ENTRY_EXPORT.symbols:
        try:
            name = exp.name.decode('utf-8') if exp.name else "<sem nome>"
            ordinal = exp.ordinal
            rva = exp.address

            exports_completos.append({
                "name": name,
                "ordinal": ordinal,
                "rva": rva
            })

            if name != "<sem nome>":
                exports_raw_names.append(name)
                exports_detalhados.append({
                    "name": name,
                    "ordinal": ordinal,
                    "rva": hex(rva)
                })

        except:
            continue

    if not exports_completos:
        texto_saida.insert(tk.END, "Nenhuma função exportada encontrada.\n")

def salvar_txt():
    if not exports_raw_names:
        messagebox.showwarning("Aviso", "Nenhum dado para salvar.")
        return

    caminho_salvar = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar como TXT"
    )

    if caminho_salvar:
        try:
            with open(caminho_salvar, 'w', encoding='utf-8') as f:
                for item in exports_raw_names:
                    f.write(f"{item}\n")
            messagebox.showinfo("Sucesso", "Arquivo .txt salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro ao salvar .txt", str(e))

def salvar_json():
    if not exports_detalhados:
        messagebox.showwarning("Aviso", "Nenhum dado para salvar.")
        return

    caminho_salvar = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Arquivo JSON", "*.json")],
        title="Salvar como JSON"
    )

    if caminho_salvar:
        try:
            with open(caminho_salvar, 'w', encoding='utf-8') as f:
                json.dump(exports_detalhados, f, indent=4)
            messagebox.showinfo("Sucesso", "Arquivo .json salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro ao salvar .json", str(e))

def mostrar_normal():
    texto_saida.delete(1.0, tk.END)
    if not exports_raw_names:
        texto_saida.insert(tk.END, "Nenhuma função exportada encontrada.")
        return
    for nome in exports_raw_names:
        texto_saida.insert(tk.END, f"{nome}\n")

def mostrar_tudo():
    texto_saida.delete(1.0, tk.END)
    if not exports_completos:
        texto_saida.insert(tk.END, "Nenhuma função exportada encontrada.")
        return
    for exp in exports_completos:
        texto_saida.insert(tk.END, f"Nome: {exp['name']} | Ordinal: {exp['ordinal']} | RVA: {hex(exp['rva'])}\n")

def mostrar_strings():
    global pe
    if pe is None:
        messagebox.showwarning("Aviso", "Nenhuma DLL carregada.")
        return

    nome_func = simpledialog.askstring("Strings", "Digite o nome da função para ver as strings:")
    if not nome_func:
        return

    func = next((exp for exp in exports_completos if exp['name'] == nome_func), None)

    texto_saida.delete(1.0, tk.END)

    def string_valida(s_bytes):
        s_lower = s_bytes.lower()
        return not (s_lower.endswith(b'.dll') or s_lower.startswith(b'dll'))

    if func:
        rva_atual = func["rva"]
        try:
            offset_atual = pe.get_offset_from_rva(rva_atual)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao converter RVA:\n{e}")
            return

        for section in pe.sections:
            inicio = section.VirtualAddress
            fim = inicio + section.Misc_VirtualSize
            if inicio <= rva_atual < fim:
                rva_fim = fim
                break
        else:
            messagebox.showerror("Erro", "Não foi possível estimar o fim da função.")
            return

        tamanho = rva_fim - rva_atual
        try:
            pe.__data__.seek(offset_atual)
            dados = pe.__data__.read(tamanho)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler dados:\n{e}")
            return

        strings = re.findall(rb'[\x20-\x7E]{4,}', dados)
        texto_saida.insert(tk.END, f"Função selecionada: {nome_func}\n\n")
        strings_filtradas = [s for s in strings if string_valida(s)]

        if strings_filtradas:
            texto_saida.insert(tk.END, "Strings Encontradas\n\n")
            for s in strings_filtradas:
                texto_saida.insert(tk.END, s.decode('utf-8', errors='replace') + "\n")
        else:
            texto_saida.insert(tk.END, "Nenhuma string visível encontrada.")
    else:
        try:
            pe.__data__.seek(0)
            dados = pe.__data__.read()
            strings = re.findall(rb'[\x20-\x7E]{4,}', dados)
            strings_filtradas = [s for s in strings if string_valida(s)]

            if not strings_filtradas:
                texto_saida.insert(tk.END, "Nenhuma string visível encontrada na DLL.")
            else:
                texto_saida.insert(tk.END, "Strings encontradas na DLL (sem nomes de DLLs e strings iniciadas com 'Dll'):\n\n")
                for s in strings_filtradas:
                    texto_saida.insert(tk.END, s.decode('utf-8', errors='replace') + "\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao extrair strings:\n{e}")

def mostrar_hex_dump():
    global pe
    if pe is None:
        messagebox.showwarning("Aviso", "Nenhuma DLL carregada.")
        return

    nome_func = simpledialog.askstring("Hex Dump", "Digite o nome da função para ver o hex dump completo:")
    if not nome_func:
        return

    func = next((exp for exp in exports_completos if exp['name'] == nome_func), None)

    if not func:
        messagebox.showerror("Erro", f"Função '{nome_func}' não encontrada.")
        return

    rva_atual = func['rva']
    try:
        offset_atual = pe.get_offset_from_rva(rva_atual)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao converter RVA:\n{e}")
        return

    rvas_maiores = sorted([e['rva'] for e in exports_completos if e['rva'] > rva_atual])
    if rvas_maiores:
        rva_fim = rvas_maiores[0]
    else:
        for section in pe.sections:
            inicio = section.VirtualAddress
            fim = inicio + section.Misc_VirtualSize
            if inicio <= rva_atual < fim:
                rva_fim = fim
                break
        else:
            messagebox.showerror("Erro", "Não foi possível estimar o fim da função.")
            return

    tamanho = rva_fim - rva_atual
    try:
        pe.__data__.seek(offset_atual)
        dados = pe.__data__.read(tamanho)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler dados:\n{e}")
        return

    def byte_para_ascii(b):
        if 32 <= b < 127:
            return chr(b)
        else:
            return '.'

    texto_saida.delete(1.0, tk.END)
    texto_saida.insert(tk.END, f"Hex dump formatado da função: {nome_func}    ({tamanho} bytes)\n\n")
    texto_saida.insert(tk.END, f"{'Offset':<8} {'Bytes Hexadecimal':<39} ASCII\n\n")

    for i in range(0, len(dados), 8):
        bloco = dados[i:i+8]
        offset_str = f"{i:04X}"
        hex_str = ' '.join(f"{b:02X}" for b in bloco)
        ascii_str = ''.join(byte_para_ascii(b) for b in bloco)
        texto_saida.insert(tk.END, f"{offset_str:<8} {hex_str:<39} {ascii_str}\n")


# Interface Gráfica
janela = tk.Tk()
janela.title("Extractor de DLL")
janela.geometry("1200x600")
janela.wm_state('zoomed')

frame_topo = tk.Frame(janela)
frame_topo.pack(padx=10, pady=10)

btn_selecionar = tk.Button(frame_topo, text="Selecionar DLL", command=selecionar_arquivo,
                           font=("Arial", 12), fg="black", bg="#03fc7f")
btn_selecionar.pack(padx=10, pady=5)

entrada_arquivo = tk.Entry(frame_topo, width=120)
entrada_arquivo.pack(padx=10, pady=5)

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=5)

btn_salvar_txt = tk.Button(frame_botoes, text="Salvar como .TXT", command=salvar_txt,
                           font=("Arial", 12), fg="black", bg="#05ffff")
btn_salvar_txt.pack(side=tk.LEFT, padx=10)

btn_salvar_json = tk.Button(frame_botoes, text="Salvar como .JSON", command=salvar_json,
                            font=("Arial", 12), fg="black", bg="#ff8605")
btn_salvar_json.pack(side=tk.LEFT, padx=10)

btn_mostrar_normal = tk.Button(frame_botoes, text="Mostrar Normal", command=mostrar_normal,
                               font=("Arial", 12), fg="black", bg="#8c048c")
btn_mostrar_normal.pack(side=tk.LEFT, padx=10)

btn_mostrar_tudo = tk.Button(frame_botoes, text="Mostrar Tudo", command=mostrar_tudo,
                             font=("Arial", 12), fg="black", bg="#fcfc03")
btn_mostrar_tudo.pack(side=tk.LEFT, padx=10)

btn_hex_dump = tk.Button(frame_botoes, text="Mostrar Hex Dump", command=mostrar_hex_dump,
                         font=("Arial", 12), fg="black", bg="#f05454")
btn_hex_dump.pack(side=tk.LEFT, padx=10)

btn_strings = tk.Button(frame_botoes, text="Mostrar Strings", command=mostrar_strings,
                        font=("Arial", 12), fg="black", bg="#aaff00")
btn_strings.pack(side=tk.LEFT, padx=10)

texto_saida = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=108, height=45)
texto_saida.pack(padx=10, pady=10)

janela.mainloop()
