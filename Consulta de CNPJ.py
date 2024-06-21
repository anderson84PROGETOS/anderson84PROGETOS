import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import webbrowser
from datetime import datetime

def consultar_cnpj(cnpj):
    url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            messagebox.showerror("Erro ao consultar CNPJ", f"Erro ao consultar CNPJ: {response.status_code}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro na requisição", f"Erro na requisição: {e}")

def calcular_idade(data_abertura):
    hoje = datetime.now()
    data_abertura = datetime.strptime(data_abertura, '%d/%m/%Y')
    diferenca = hoje - data_abertura
    anos = diferenca.days // 365
    meses = (diferenca.days % 365) // 30
    dias = (diferenca.days % 365) % 30
    return f"{anos} anos, {meses} meses e {dias} dias"

def consultar_e_mostrar(cnpj_entry, info_text):
    cnpj = cnpj_entry.get()
    dados_cnpj = consultar_cnpj(cnpj)
    if dados_cnpj:
        # Limpa o ScrolledText e prepara para receber novos dados
        info_text.config(state=tk.NORMAL)
        info_text.delete(1.0, tk.END)

        # Monta a mensagem para exibir no ScrolledText
        message = f"Dados Encontrados para CNPJ:  {cnpj}\n\n"
        message += f"\nCNPJ: {dados_cnpj.get('cnpj', 'Não encontrado')}\n"
        message += f"\nNome: {dados_cnpj.get('nome', 'Não encontrado')}\n"
        message += f"\nTelefone: {dados_cnpj.get('telefone', 'Não encontrado')}\n"
        message += f"\nSituação: {dados_cnpj.get('situacao', 'Não encontrado')}\n"
        message += f"\nCNAE principal: {dados_cnpj['atividade_principal'][0]['text'] if 'atividade_principal' in dados_cnpj else 'Não encontrado'}\n"
        message += f"\nData da situação cadastral: {dados_cnpj.get('data_situacao', 'Não encontrado')}\n"        
        message += f"\nData de abertura: {dados_cnpj.get('abertura', 'Não encontrado')}\n"
        
        # Calcula e adiciona a idade da empresa (data de abertura)
        if 'abertura' in dados_cnpj:
            idade_empresa = calcular_idade(dados_cnpj['abertura'])
            message += f"\nIdade da Empresa: {idade_empresa}\n"
        else:
            message += "Data de abertura não encontrada\n"
        
        message += f"\nCapital social: R$ {dados_cnpj.get('capital_social', 'Não encontrado')}\n"

        # Adiciona Quadro de sócios e administradores, se existir
        if 'qsa' in dados_cnpj:
            message += "\n\n\n\n========== Quadro de Sócios e Administradores ==========\n\n"
            for socio in dados_cnpj['qsa']:
                message += f"\nNome: {socio['nome']} | Qualificação: {socio['qual']} | Entrada: {socio['qual']}\n"

        info_text.insert(tk.END, message)
        info_text.config(state=tk.DISABLED)

def abrir_site():
    webbrowser.open("https://www.informecadastral.com.br")

def criar_interface_grafica():
    root = tk.Tk()
    root.wm_state('zoomed')
    root.title("Consulta CNPJ")

    label = tk.Label(root, text="Digite o número do CNPJ  (ex: 18236120000158)", font=("Arial", 11))
    label.pack(pady=5)

    cnpj_entry = tk.Entry(root, width=40, font=("Arial", 11))
    cnpj_entry.pack()

    consultar_button = tk.Button(root, text="Consultar", command=lambda: consultar_e_mostrar(cnpj_entry, info_text), font=("Arial", 11), bg="#0bfc03")
    consultar_button.pack(pady=5)

    site_button = tk.Button(root, text="Mais informações no site: https://www.informecadastral.com.br", command=abrir_site, font=("Arial", 11))
    site_button.pack(pady=5)

    info_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=43, font=("Arial", 12))
    info_text.pack(pady=5)
    info_text.config(state=tk.DISABLED)

    root.mainloop()

# Chama a função para criar a interface gráfica
criar_interface_grafica()
