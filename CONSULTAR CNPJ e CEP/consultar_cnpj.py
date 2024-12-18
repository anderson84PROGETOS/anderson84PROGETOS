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
        message = f"""
CNPJ: {dados_cnpj.get('cnpj', 'Não encontrado')}

RAZÃO SOCIAL: {dados_cnpj.get('nome', 'Não encontrado')}

MATRIZ OU FILIAL: {dados_cnpj.get('tipo', 'Não encontrado')}

NOME FANTASIA: {dados_cnpj.get('fantasia', 'Não encontrado')}

SITUAÇÃO CADASTRAL: {dados_cnpj.get('situacao', 'Não encontrado')}

DATA DA SITUAÇÃO CADASTRAL: {dados_cnpj.get('data_situacao', 'Não encontrado')}

MOTIVO DA SITUAÇÃO CADASTRAL: {dados_cnpj.get('motivo_situacao', 'Não encontrado')}

NATUREZA JURÍDICA: {dados_cnpj.get('natureza_juridica', 'Não encontrado')}

DATA DE ABERTURA: {dados_cnpj.get('abertura', 'Não encontrado')}

IDADE: {calcular_idade(dados_cnpj['abertura']) if 'abertura' in dados_cnpj else 'Não encontrado'}

PORTE (RFB): {dados_cnpj.get('porte', 'Não encontrado')}

CAPITAL SOCIAL: R$ {dados_cnpj.get('capital_social', 'Não encontrado')}

ATUALIZAÇÃO DESTA PÁGINA: {dados_cnpj.get('ultima_atualizacao', 'Não encontrado')}

\n\nLOCALIZAÇÃO\n=============
ENDEREÇO: {dados_cnpj.get('logradouro', 'Não encontrado')}    | Número: {dados_cnpj.get('numero', 'Não encontrado')}\n
COMPLEMENTO: {dados_cnpj.get('complemento', 'Não encontrado')}\n
BAIRRO: {dados_cnpj.get('bairro', 'Não encontrado')}\n
CIDADE | ESTADO: {dados_cnpj.get('municipio', 'Não encontrado')} | {dados_cnpj.get('uf', 'Não encontrado')}\n
CEP: {dados_cnpj.get('cep', 'Não encontrado')}\n
TELEFONES: {dados_cnpj.get('telefone', 'Não encontrado')}\n
E-MAILS: {dados_cnpj.get('email', 'Não encontrado')}\n

\n\nATIVIDADE ECONÔMICA PRINCIPAL\n==============================
CÓDIGO: {dados_cnpj['atividade_principal'][0]['code'] if 'atividade_principal' in dados_cnpj else 'Não encontrado'}
DESCRIÇÃO: {dados_cnpj['atividade_principal'][0]['text'] if 'atividade_principal' in dados_cnpj else 'Não encontrado'}

\n\nATIVIDADES ECONÔMICAS SECUNDÁRIAS\n====================================
"""
        # Adiciona atividades econômicas secundárias
        if 'atividades_secundarias' in dados_cnpj:
            for atividade in dados_cnpj['atividades_secundarias']:
                message += f"CÓDIGO: {atividade['code']} | DESCRIÇÃO: {atividade['text']}\n"

        # Adiciona informações do QSA
        message += "\n\n\nQUADRO DE SÓCIOS E ADMINISTRADORES (QSA)\n==========================================\n"
        
        if 'qsa' in dados_cnpj:
            for socio in dados_cnpj['qsa']:
                data_entrada = socio.get('data_entrada', None)
                if data_entrada:
                    # Converte para formato adequado, se necessário
                    data_entrada = datetime.strptime(data_entrada, '%d/%m/%Y').strftime('%d/%m/%Y')
                    message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
ENTRADA: {data_entrada}
"""
                else:
                    message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
"""
        else:
            message += "Não encontrado\n"

        # Exibe os dados no ScrolledText
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
