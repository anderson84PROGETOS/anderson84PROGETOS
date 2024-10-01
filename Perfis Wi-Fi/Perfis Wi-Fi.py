import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog

def get_wifi_profiles():
    try:
        # Executa o comando netsh para obter a lista de perfis WLAN
        command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True)
        lines = command_output.split('\n')

        # Variável para armazenar os resultados
        profiles = []

        # Itera pelas linhas, ignorando as primeiras 9
        for line in lines[9:]:
            tokens = line.split(':')
            if len(tokens) >= 2:
                profile_name = tokens[0].strip()
                ssid = tokens[1].strip()

                if ssid:
                    try:
                        # Obtém a chave para o perfil atual
                        key_output = subprocess.check_output(f'netsh wlan show profile "{ssid}" key=clear', shell=True, universal_newlines=True)
                        key_content_line = [line for line in key_output.split('\n') if "Key Content" in line]
                        if key_content_line:
                            key_content = key_content_line[0].split(":")[1].strip()
                            profiles.append(f"SSID: {ssid}, Senha: {key_content}")
                        else:
                            # Executa o comando para mostrar o perfil e armazena a saída
                            profile_output = subprocess.check_output(f'netsh wlan show profile name="{ssid}" key=clear', shell=True, universal_newlines=True)
                            profiles.append(f"SSID: {ssid}\n{profile_output}")

                    except subprocess.CalledProcessError as e:
                        profiles.append(f"SSID: {ssid}, Erro ao obter a senha (código: {e.returncode})")

        return profiles

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

def show_profiles():
    profiles = get_wifi_profiles()
    if profiles:
        output_text.delete(1.0, tk.END)  # Limpa o campo de texto
        output_text.insert(tk.END, "\n\n".join(profiles))  # Insere os perfis encontrados

def save_results():
    # Abre um diálogo para selecionar onde salvar o arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(output_text.get(1.0, tk.END))  # Grava o conteúdo do campo de texto
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo: {e}")

# Configuração da janela principal
root = tk.Tk()
root.title("Perfis Wi-Fi")
root.geometry("1200x1000")  # Aumentado para melhor visualização dos detalhes

# Botão para mostrar perfis
btn_show = tk.Button(root, text="Mostrar Perfis Wi-Fi", command=show_profiles, font=("TkDefaultFont", 10, "bold"), bg='#07f5c1')
btn_show.pack(pady=10)

# Botão para salvar resultados
btn_save = tk.Button(root, text="Salvar Resultados", command=save_results, font=("TkDefaultFont", 10, "bold"), bg='#fa9405')
btn_save.pack(pady=10)

# Campo de texto para exibir os resultados
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=42, font=("TkDefaultFont", 12, "bold"))
output_text.pack(pady=10)

# Executa a aplicação
root.mainloop()
