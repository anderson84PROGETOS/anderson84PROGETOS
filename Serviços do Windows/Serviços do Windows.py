import subprocess
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import json

ultima_saida = ""
servicos_data = []

def listar_servicos():
    """Executa o comando sc query e mostra a saída colorida"""
    global ultima_saida, servicos_data
    try:
        resultado = subprocess.run(
            "sc query type= service state= all",
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        saida = resultado.stdout.strip()
        ultima_saida = saida
        servicos_data = []

        txt_output.delete(1.0, tk.END)
        txt_output.insert(tk.END, "LISTA DE SERVIÇOS DO WINDOWS             sc query type= service state= all \n\n", "titulo")

        if not saida:
            txt_output.insert(tk.END, "⚠️ Nenhuma informação retornada. Execute como administrador.\n", "erro")
            return

        blocos = saida.split("\n\n")
        for bloco in blocos:
            servico = {}
            linhas = bloco.strip().split("\n")
            for linha in linhas:
                linha_limpa = linha.strip()

                # Processar NOME_DO_SERVICO
                if "NOME_DO_SERVIO:" in linha_limpa:
                    parts = linha_limpa.split("NOME_DO_SERVIO:", 1)
                    if len(parts) > 1:
                        txt_output.insert(tk.END, "NOME_DO_SERVIO: ", "servico_label")
                        txt_output.insert(tk.END, parts[1].strip() + "\n", "amarelo")
                        servico["NOME_DO_SERVICO"] = parts[1].strip()
                    else:
                        txt_output.insert(tk.END, linha_limpa + "\n", "servico_label")

                # Processar NOME_PARA_EXIBIO
                elif "NOME_PARA_EXIBIO:" in linha_limpa:
                    parts = linha_limpa.split("NOME_PARA_EXIBIO:", 1)
                    if len(parts) > 1:
                        txt_output.insert(tk.END, "NOME_PARA_EXIBIO: ", "NOME_PARA_EXIBIO")
                        txt_output.insert(tk.END, parts[1].strip() + "\n", "azul")
                        servico["NOME_PARA_EXIBIO"] = parts[1].strip()
                    else:
                        txt_output.insert(tk.END, linha_limpa + "\n", "NOME_PARA_EXIBIO")        

                # Processar DISPLAY_NAME
                elif "DISPLAY_NAME:" in linha_limpa:
                    parts = linha_limpa.split("DISPLAY_NAME:", 1)
                    if len(parts) > 1:
                        txt_output.insert(tk.END, "DISPLAY_NAME: ", "exibicao_label")
                        txt_output.insert(tk.END, parts[1].strip() + "\n", "verde")
                        servico["DISPLAY_NAME"] = parts[1].strip()
                    else:
                        txt_output.insert(tk.END, linha_limpa + "\n", "exibicao_label")

                # ESTADO / STATE
                elif "STATE" in linha_limpa or "ESTADO" in linha_limpa:
                    if "RUNNING" in linha_limpa or "EM_EXECUÇÃO" in linha_limpa:
                        txt_output.insert(tk.END, linha_limpa + "\n", "verde_claro")
                        servico["state"] = "RUNNING"
                    elif "STOPPED" in linha_limpa or "PARADO" in linha_limpa:
                        txt_output.insert(tk.END, linha_limpa + "\n", "vermelho")
                        servico["state"] = "STOPPED"
                    else:
                        txt_output.insert(tk.END, linha_limpa + "\n", "cinza")
                        servico["state"] = linha_limpa.split()[-1] if linha_limpa.split() else "UNKNOWN"

                # Outros campos (ex.: TYPE, WIN32_EXIT_CODE, etc.)
                else:
                    parts = linha_limpa.split(":", 1)
                    if len(parts) > 1:
                        key = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip()
                        servico[key] = value
                        txt_output.insert(tk.END, linha_limpa + "\n", "cinza")

            if servico:
                servicos_data.append(servico)

            # Adiciona uma quebra extra entre blocos de serviços
            txt_output.insert(tk.END, "\n\n", "cinza")

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao executar o comando:\n{e}")


def salvar_resultado():
    """Salva a saída em .txt ou .json com base na escolha do usuário"""
    if not ultima_saida:
        messagebox.showwarning("Aviso", "Nenhum resultado para salvar!")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[
            ("Arquivo de texto", "*.txt"),
            ("Arquivo JSON", "*.json")
        ],
        title="Salvar como (TXT ou JSON)..."
    )

    if not caminho:
        return

    try:
        if caminho.endswith(".txt"):
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(ultima_saida)
            messagebox.showinfo("Sucesso", f"Arquivo TXT salvo em:\n{caminho}")
        elif caminho.endswith(".json"):
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(servicos_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Sucesso", f"Arquivo JSON salvo em: {caminho}")
        else:
            messagebox.showwarning("Aviso", "Formato de arquivo não suportado. Use .txt ou .json.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao salvar arquivo:\n{e}")


# ==== INTERFACE ====  
root = tk.Tk()
root.title("Serviços do Windows  -  sc query type= service state= all")
root.geometry("1280x800")
root.state("zoomed")  # Abrir maximizado
root.config(bg="#1E1E1E")

lbl_titulo = tk.Label(root, text="Monitor de Serviços do Windows   sc query type= service state= all",
                      fg="white", bg="#1E1E1E", font=("Segoe UI", 16, "bold"))
lbl_titulo.pack(pady=10)

frame_botoes = tk.Frame(root, bg="#1E1E1E")
frame_botoes.pack(pady=5)

btn_executar = tk.Button(frame_botoes, text="🔄 Executar sc query", command=listar_servicos,
                         bg="#007ACC", fg="white", font=("Segoe UI", 11, "bold"), width=20)
btn_executar.grid(row=0, column=0, padx=10)

btn_salvar = tk.Button(frame_botoes, text="💾 Salvar Saída", command=salvar_resultado,
                       bg="#28A745", fg="white", font=("Segoe UI", 11, "bold"), width=20)
btn_salvar.grid(row=0, column=1, padx=10)

txt_output = scrolledtext.ScrolledText(root, width=120, height=43, bg="#252526",
                                       fg="#ffffff", insertbackground="white", font=("Consolas", 12))
txt_output.pack(pady=10)

# === Definição das cores ===
txt_output.tag_config("titulo", foreground="#00BFFF", font=("Segoe UI", 12, "bold"))
txt_output.tag_config("servico_label", foreground="#f3ff05", font=("Consolas", 12, "bold"))  # Label NOME_DO_SERVICO:
txt_output.tag_config("exibicao_label", foreground="#32CD32", font=("Consolas", 12, "bold"))  # Label DISPLAY_NAME:
txt_output.tag_config("amarelo", foreground="#FFD700", font=("Consolas", 12))  # Valor de NOME_DO_SERVICO
txt_output.tag_config("verde", foreground="#32CD32", font=("Consolas", 12))  # Valor de DISPLAY_NAME
txt_output.tag_config("verde_claro", foreground="#98FB98", font=("Consolas", 12))
txt_output.tag_config("vermelho", foreground="#FF4500", font=("Consolas", 12, "bold"))
txt_output.tag_config("erro", foreground="#FF5555", font=("Segoe UI", 12, "bold"))
txt_output.tag_config("NOME_PARA_EXIBIO", foreground="#05eeff", font=("Segoe UI", 11, "bold"))
txt_output.tag_config("azul", foreground="#1E90FF", font=("Consolas", 12))

root.mainloop()
