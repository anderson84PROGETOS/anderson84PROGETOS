import tkinter as tk
from datetime import datetime

dias_da_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
nomes_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

janela = tk.Tk()
janela.title('Relógio')
janela.geometry('600x380')
janela.configure(bg='#4B0082')

label_hora = tk.Label(janela, font=('Fake Hope', 65), bg='#008000', fg='white', borderwidth=0, highlightthickness=0)
label_hora.config(highlightbackground='#008000', padx=20, pady=20, relief='ridge', bd=10, width=12, height=2, anchor='center')

label_data = tk.Label(janela, font=('Arial', 26), bg='#008000', fg='white', borderwidth=0, highlightthickness=0)
label_data.config(highlightbackground='#008000', padx=20, pady=20, relief='ridge', bd=10, width=25, height=2, anchor='center')

label_hora.pack(pady=20)
label_ano = tk.Label(janela, font=('Arial', 15), bg='#4B0082', fg='white')
label_ano.pack(pady=5)
label_data.pack(pady=10)

def update_clock():
    agora = datetime.now()
    dia_da_semana = agora.weekday()
    dia = agora.day
    mes = agora.month
    ano = agora.year
    hora = agora.hour
    minuto = agora.minute
    segundo = agora.second    
    label_hora.config(text=f'{hora:02d}:{minuto:02d}:{segundo:02d}')
    label_data.config(text=f'{dias_da_semana[dia_da_semana]}, {dia:02d} de {nomes_meses[mes-1]} de {ano}')
    label_ano.config(text=datetime.now().strftime('%d/%m/%Y'))

    janela.after(1000, update_clock)  # call this function again in 1000ms (1s)

update_clock()
janela.mainloop()
