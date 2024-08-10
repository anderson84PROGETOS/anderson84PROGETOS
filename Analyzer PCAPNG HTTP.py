import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import subprocess
import threading

def analyze_pcap():
    # Função interna para análise do PCAPNG em um thread
    def run_analysis():
        # Selecionar o arquivo .pcapng
        file_path = filedialog.askopenfilename(filetypes=[("PCAPNG files", "*.pcapng")])
        if not file_path:
            return

        try:
            # Determinar o comando para o tshark
            cmd = ["tshark", "-r", file_path, "-Y", "http", "-V"]

            # Executar o comando e capturar a saída
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            
            # Dividir a saída em linhas
            output_lines = result.stdout.split('\n')
            
            # Atualizar a interface gráfica na thread principal
            def update_text_area():
                text_area.delete('1.0', tk.END)  # Limpar o conteúdo anterior
                
                for line in output_lines:
                    start = 0
                    while True:
                        # Procurar a palavra "Form item" para destacar
                        start = line.find('Form item', start)
                        if start == -1:
                            # Se não encontrar, insere o resto da linha e quebra o loop
                            text_area.insert(tk.END, line + '\n')
                            break
                        # Inserir o texto antes da palavra destacada
                        text_area.insert(tk.END, line[:start])
                        # Inserir a palavra destacada com a tag
                        end = start + len('Form item')
                        text_area.insert(tk.END, line[start:end], 'highlight')
                        # Atualizar a posição para a próxima ocorrência
                        start = end
                    text_area.insert(tk.END, '\n')  # Adicionar nova linha após cada linha de texto
                
                if not output_lines:
                    text_area.insert(tk.END, 'Nenhum resultado encontrado.')

                # Reabilitar o botão
                button.config(state=tk.NORMAL)

            # Atualizar a interface gráfica na thread principal
            root.after(0, update_text_area)

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Erro ao processar o arquivo: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
        finally:
            # Reabilitar o botão
            button.config(state=tk.NORMAL)

    # Desabilitar o botão durante a análise
    button.config(state=tk.DISABLED)
    
    # Iniciar o thread para a análise
    threading.Thread(target=run_analysis, daemon=True).start()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Analyzer PCAPNG HTTP")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Botão para carregar o arquivo .pcapng e analisar
button = tk.Button(frame, text="Selecionar Arquivo .pcapng", command=analyze_pcap, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
button.pack(pady=15)

# Área de texto para exibir os resultados
text_area = scrolledtext.ScrolledText(frame, width=130, height=43, font=("TkDefaultFont", 11, "bold"))
text_area.pack()

# Configurar a tag 'highlight' para aplicar a cor vermelha
text_area.tag_configure('highlight', foreground='red')

root.mainloop()
