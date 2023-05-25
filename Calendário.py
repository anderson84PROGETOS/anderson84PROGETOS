import calendar
import tkinter as tk
from tkinter import ttk
from datetime import datetime

def criar_calendario():
    ano_atual = datetime.now().year
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

    root = tk.Tk()    
    root.title("Calendário " + str(ano_atual))
    root.geometry("1100x710")

    title_label = ttk.Label(root, text='Calendário ' + str(ano_atual), font=('TkDefaultFont', 14, 'bold'), foreground='red', anchor='center')
    title_label.pack(side=tk.TOP, anchor='center', padx=10, pady=10)

    scroll_frame = ttk.Frame(root)
    scroll_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(scroll_frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

    inner_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor='nw')

    num_colunas = 4  # Número de colunas para exibir os meses

    for i, mes in enumerate(meses):
        coluna = i % num_colunas
        linha = i // num_colunas

        frame_mes = tk.Frame(inner_frame)
        frame_mes.grid(row=linha, column=coluna, padx=10, pady=10)

        label_mes = tk.Label(frame_mes, text=mes, font=("Arial", 15, "bold"))
        label_mes.pack()

        frame_dias_semana = tk.Frame(frame_mes)
        frame_dias_semana.pack()

        for dia_semana in dias_semana:
            label_dia_semana = tk.Label(frame_dias_semana, text=dia_semana, width=4, font=("Arial", 9, "bold"))
            label_dia_semana.pack(side=tk.LEFT)

        calendario_mes = calendar.monthcalendar(ano_atual, i+1)
        for semana in calendario_mes:
            frame_semana = tk.Frame(frame_mes)
            frame_semana.pack()

            for dia in semana:
                label_dia = tk.Label(frame_semana, text=str(dia) if dia != 0 else "", width=4)
                label_dia.pack(side=tk.LEFT)

    root.mainloop()

criar_calendario()
