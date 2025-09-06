import subprocess
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox

# Função para buscar os erros do Windows
def buscar_erros():
    comando = 'wevtutil qe system /q:"*[System[(Level=2)]]" /f:text'
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    
    eventos = resultado.stdout.split("Event[")[1:]  # Ignora o primeiro que é vazio
    
    dicas = {
        "41": "Risco de reinício: verifique fonte, RAM, superaquecimento ou falha de energia.",
        "15": "Erro TPM: se não usa BitLocker, pode ignorar; se usa, atualizar driver TPM ou BIOS.",
        "7000": "Serviço não iniciou: verificar se o programa existe, reinstalar ou reparar o serviço.",
        "7009": "Timeout de serviço: aguarde o serviço ou reinstale o programa relacionado.",
        "7": "Erro de disco: rodar chkdsk ou CrystalDiskInfo para verificar saúde do HD/SSD.",
        "51": "Erro de disco: setor defeituoso, considerar backup e substituir disco se necessário."
    }
    
    # Limpa o ScrolledText
    txt_area.config(state='normal')
    txt_area.delete('1.0', tk.END)
    
    for evento in eventos:
        lines = evento.splitlines()
        event_id = ""
        source = ""
        description = ""
        for line in lines:
            if line.strip().startswith("Event ID:"):
                event_id = line.split(":", 1)[1].strip()
            elif line.strip().startswith("Source:"):
                source = line.split(":", 1)[1].strip()
            elif line.strip().startswith("Description:"):
                idx = lines.index(line)
                description = "\n".join(lines[idx+1:]).strip()
                break
        
        evento_texto = f"Event ID: {event_id}\nSource: {source}\nDescription: {description}\n"
        if event_id in dicas:
            evento_texto += f"Dica de correção: {dicas[event_id]}\n"
        evento_texto += "-"*100 + "\n\n"
        
        # Insere no ScrolledText com cores
        if event_id == "41" and source == "Kernel-Power":
            txt_area.insert(tk.END, evento_texto, 'vermelho')
        else:
            txt_area.insert(tk.END, evento_texto, 'amarelo')
    
    txt_area.config(state='disabled')

# Função para salvar o log
def salvar_log():
    log_text = txt_area.get('1.0', tk.END)
    if log_text.strip() == "":
        messagebox.showwarning("Aviso", "Não há log para salvar.")
        return
    with open("log_erros.txt", "w", encoding="utf-8") as f:
        f.write(log_text)
    messagebox.showinfo("Sucesso", "Log salvo em 'log_erros.txt'.")

# Criando a janela principal
root = tk.Tk()
root.title("Visualizador de Erros Críticos do Sistema")
root.geometry("1200x800")

# Botões
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

btn_buscar = tk.Button(btn_frame, text="Buscar Erros", command=buscar_erros, width=20, bg='lightblue')
btn_buscar.pack(side=tk.LEFT, padx=5)

btn_salvar = tk.Button(btn_frame, text="Salvar Log", command=salvar_log, width=20, bg='lightgreen')
btn_salvar.pack(side=tk.LEFT, padx=5)

btn_sair = tk.Button(btn_frame, text="Sair", command=root.destroy, width=20, bg='lightcoral')
btn_sair.pack(side=tk.LEFT, padx=5)

# ScrolledText
txt_area = scrolledtext.ScrolledText(root, width=150, height=52)
txt_area.pack(padx=10, pady=10)

# Configurando tags de cores
txt_area.tag_config('vermelho', foreground='darkred')  # vermelho escuro
txt_area.tag_config('amarelo', foreground='darkgreen') # verde escuro para não críticos

root.mainloop()
