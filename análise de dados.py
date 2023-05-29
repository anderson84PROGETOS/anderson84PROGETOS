import tkinter as tk
from tkinter import filedialog
from PIL import Image, ExifTags
from tkinter import Scrollbar
import PyPDF2
import docx2txt

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"),
                                                     ("Text Files", "*.txt"),
                                                     ("Word Documents", "*.doc"),
                                                     ("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.ico"),
                                                     ("PDF Files", "*.pdf"),
                                                     ("Executable Files", "*.exe")])
    if file_path:
        try:
            if file_path.lower().endswith((".csv", ".txt")):
                with open(file_path, 'r') as file:
                    content = file.read()
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, content)
            elif file_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".ico")):
                image = Image.open(file_path)
                exif_data = image._getexif()
                if exif_data is not None:
                    exif_info = ""
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_info += f"{tag_name}: {value}\n"
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, exif_info)
                else:
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, "Nenhuma informação EXIF encontrada.")
            elif file_path.lower().endswith((".pdf", ".exe")):
                if file_path.lower().endswith(".pdf"):
                    pdf_file = open(file_path, 'rb')
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
                    pdf_file.close()
                else:  # .exe file
                    with open(file_path, 'rb') as file:
                        content = file.read().hex()
                    text_content = "Hexadecimal representation of the executable file:\n" + content
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, text_content)
            elif file_path.lower().endswith(".doc"):
                text_content = docx2txt.process(file_path)
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, text_content)
        except:
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, f"Não foi possível abrir o arquivo {file_path}.")

def clear_results():
    text_box.delete(1.0, tk.END)

# Criar a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Análise Dados")
window.geometry("400x400")

# Set the window icon using ICO file
try:
    window.iconbitmap("icone.ico")  # Replace "icone.ico" with the filename of your icon file
except tk.TclError:
    print("Failed to load the icon file.")

# Create a scrollbar for the text box
scrollbar = Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Botão "Abrir arquivo"
btn_open_file = tk.Button(window, text="Abrir arquivo", command=open_file, bg="#00FFFF")
btn_open_file.pack(pady=20)

# Botão "Limpar resultados"
btn_clear_results = tk.Button(window, text="Limpar resultados", command=clear_results, bg="#D2691E")
btn_clear_results.pack(pady=10)

# Janela em branco para exibir os resultados
text_box = tk.Text(window, height=200, width=170, font=("TkDefaultFont", 10, "bold"))
text_box.pack(pady=10)

# Configure the scrollbar to work with the text box
text_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)

# Executar o loop principal da janela
window.mainloop()
