import tkinter as tk
from datetime import datetime
import locale

# Definindo o locale para Português Brasileiro
locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

class Clock(tk.Canvas):
    def __init__(self, master=None, **kw):
        super().__init__(master=master, **kw)
        self.width = self.winfo_reqwidth()
        self.height = self.winfo_reqheight()
        self.configure(width=self.width, height=self.height)
        self.radius = min(self.width, self.height) / 2 * 0.9

    def draw_clock_face(self):
        self.delete("all")
        self.create_oval(
            self.width / 2 - self.radius,
            self.height / 2 - self.radius,
            self.width / 2 + self.radius,
            self.height / 2 + self.radius,
            fill="white", width=2
        )

    def draw_clock_text(self):
        current_time = datetime.now()
        date_str = current_time.strftime("%A, %d de %B de %Y").encode('iso-8859-1').decode('utf-8')
        time_str = current_time.strftime("%H:%M:%S")
        date_time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
        
        self.create_oval(
            self.width / 2 - self.radius,
            self.height / 2 - self.radius,
            self.width / 2 + self.radius,
            self.height / 2 + self.radius,
            fill="#4B0082", width=2
        )

        self.create_text(
            self.width / 2,
            self.height * 0.4,
            text=time_str,
            font=("Fake Hope", 35, "bold"),
            fill="white"
        )

        self.create_text(
            self.width / 2,
            self.height * 0.6,
            text=date_str,
            font=("Arial", 11, "bold"),
            fill="white"
        )

        self.date_time_text.delete("1.0", "end")
        self.date_time_text.insert("end", date_time_str)

    def update(self):
        self.draw_clock_face()
        self.draw_clock_text()
        self.after(1000, self.update)
        
root = tk.Tk()
root.title("Relógio Data")
root.resizable(False, False)

# Criando o canvas para o relógio
clock = Clock(root, width=280, height=280)
clock.pack()

# Obtendo a largura da tela
screen_width = root.winfo_screenwidth()

# Criando o widget Text para exibir a data e hora
date_time_frame = tk.Frame(root, bg="#4B0082", bd=20)
date_time_frame.pack(fill="both", expand=True)

date_time_label = tk.Label(date_time_frame, text="Data e Hora Atuais", font=("Arial", 12), fg="white", bg="#4B0082", anchor='center')
date_time_label.pack(pady=(5, 0))

clock_width = int(0.5 * screen_width)  # Define a largura do widget como 50% da largura da tela
clock.date_time_text = tk.Text(date_time_frame, height=1, width=20, font=("Arial", 13), fg="white", bg="#4B0082", state='disabled')
clock.date_time_text.pack(padx=20, pady=10)
clock.date_time_text.configure(state='normal')

# Obtém a data e hora atuais e converte em uma string format
from datetime import datetime

current_time = datetime.now()
date_time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
from datetime import datetime

current_time = datetime.now()
date_time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
clock.date_time_text.delete("1.0", "end")
clock.date_time_text.insert("end", date_time_str)

clock.update()
root.mainloop()
