import tkinter as tk
from tkinter import font
import requests
from datetime import datetime
from geopy.geocoders import Nominatim

# Função para buscar o tempo via scraping
def obter_tempo():
    cidade = entrada_cidade.get().replace(" ", "+")  # Corrige espaços no nome da cidade para URL
    url = f"https://wttr.in/{cidade}?format=%t+%C+%h+%w+%P"
    
    resposta = requests.get(url)
    if resposta.status_code == 200:
        dados = resposta.text.split()

        # Verifica se há dados de tempo válidos
        if len(dados) >= 5:
            temp = dados[0]  # Temperatura
            descricao = traduzir_descricao(dados[1])  # Descrição do clima traduzida            
            vento = dados[3]  # Velocidade do vento
            chuva = dados[4]  # Precipitação/Chuva
            
            # Atualiza a interface gráfica com os dados
            label_temp['text'] = f"{temp}"
            label_descricao['text'] = descricao            
            label_vento['text'] = f"Vento: {vento}"
            label_chuva['text'] = f"Chuva: {chuva}"

            # Atualiza a origem da cidade
            obter_origem_cidade(cidade)

            # Atualiza a data e a hora atuais
            atualizar_data_hora()
        else:
            label_temp['text'] = "Dados não encontrados"
    else:
        label_temp['text'] = "Erro na conexão"

# Função para traduzir a descrição do clima
def traduzir_descricao(descricao):
    traducoes = {
        "partly": "Parcialmente nublado",
        "cloudy": "Nublado",
        "clear": "Limpo",
        "sunny": "Ensolarado",
        "rain": "Chuva",
        "snow": "Neve",
        "fog": "Nevoeiro",
        "thunder": "Trovoada",
        "overcast": "Céu nublado",
        "drizzle": "Chuva leve",
    }
    return traducoes.get(descricao.lower(), "Descrição não disponível")

# Função para obter a origem da cidade
def obter_origem_cidade(cidade):
    geolocator = Nominatim(user_agent="weather_app")
    localizacao = geolocator.geocode(cidade)
    
    if localizacao:
        origem = f"{localizacao.address.split(',')[0]}, {localizacao.address.split(',')[-1]}"
        label_origem['text'] = f"Origem: {origem}"
    else:
        label_origem['text'] = "Origem não encontrada"

# Função para atualizar a data e hora
def atualizar_data_hora():
    agora = datetime.now()
    dias_da_semana = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }
    
    dia_semana = dias_da_semana[agora.weekday()]  # Obtém o dia da semana
    data_hora_formatada = f"{dia_semana}, {agora.strftime('%H:%M')}"
    label_data_hora['text'] = data_hora_formatada

# Criação da janela principal
janela = tk.Tk()
janela.geometry("500x500")  # Ajuste de tamanho da janela
janela.title("Previsão do Tempo")

# Fonte personalizada para o número da temperatura
minha_fonte = font.Font(family='Helvetica', size=48, weight='bold')

# Entrada para o nome da cidade
label_cidade = tk.Label(janela, text="Digite o Nome da Cidade", font=("TkDefaultFont", 11, "bold"))
label_cidade.pack(pady=10)

entrada_cidade = tk.Entry(janela, width=30, font=("TkDefaultFont", 11, "bold"))
entrada_cidade.pack(pady=10)

# Botão para buscar o tempo
botao = tk.Button(janela, text="Obter Clima", command=obter_tempo, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
botao.pack(pady=10)

# Exibir a temperatura
label_temp = tk.Label(janela, text="0°C", font=minha_fonte)
label_temp.pack(pady=10)

# Exibir a descrição do clima
label_descricao = tk.Label(janela, text="Descrição do clima", font=("TkDefaultFont", 11, "bold"))
label_descricao.pack(pady=10)

label_vento = tk.Label(janela, text="Vento: -- km/h", font=("TkDefaultFont", 11, "bold"))
label_vento.pack(pady=5)

label_chuva = tk.Label(janela, text="Chuva: --%", font=("TkDefaultFont", 11, "bold"))
label_chuva.pack(pady=5)

# Exibir a origem da cidade
label_origem = tk.Label(janela, text="Origem: ", font=("TkDefaultFont", 11, "bold"))
label_origem.pack(pady=5)

# Exibir a data e hora
label_data_hora = tk.Label(janela, text="", font=("TkDefaultFont", 11, "bold"))
label_data_hora.pack(pady=10)

# Inicia o loop da interface gráfica
janela.mainloop()
