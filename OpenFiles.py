import tkinter as tk
from tkinter import filedialog
from PIL import Image, ExifTags
from tkinter import Scrollbar
import PyPDF2
import docx2txt
from docx import Document
import pandas as pd
import openpyxl

def analyze_data(file_path):
    try:
        if file_path.lower().endswith((".csv", ".txt", ".py")):
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
                text_box.insert(tk.END, "No EXIF information found.")
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
        elif file_path.lower().endswith((".doc", ".docx")):
            if file_path.lower().endswith(".doc"):
                text_content = docx2txt.process(file_path)
            else:  # .docx file
                doc = Document(file_path)
                paragraphs = []
                for paragraph in doc.paragraphs:
                    paragraphs.append(paragraph.text)
                text_content = "\n".join(paragraphs)
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, text_content)
        elif file_path.lower().endswith(".html"):
            with open(file_path, 'r') as file:
                content = file.read()
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, content)
        elif file_path.lower().endswith(".xlsx"):
            df = pd.read_excel(file_path, engine='openpyxl')
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, df.to_string(index=False))
        else:
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, "Unsupported file format.")
    except:
        text_box.delete(1.0, tk.END)
        text_box.insert(tk.END, f"Failed to open the file {file_path}.")

def open_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        analyze_data(file_path)

def clear_results():
    text_box.delete(1.0, tk.END)

# Create the main window
window = tk.Tk()
window.wm_state('zoomed')
window.title("Open Files")
window.geometry("400x400")

# Set the window icon using ICO file
try:
    window.iconbitmap("icon.ico")  # Replace "icon.ico" with the filename of your icon file
except tk.TclError:
    print("Failed to load the icon file.")

# Create a scrollbar for the text box
scrollbar = Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# "Open File" button
btn_open_file = tk.Button(window, text="Open File", command=open_file, bg="#00FFFF")
btn_open_file.pack(pady=20)

# "Clear Results" button
btn_clear_results = tk.Button(window, text="Clear Results", command=clear_results, bg="#D2691E")
btn_clear_results.pack(pady=10)

# Blank text box to display results
text_box = tk.Text(window, height=200, width=170, font=("TkDefaultFont", 10, "bold"))
text_box.pack(pady=10)

# Configure the scrollbar to work with the text box
text_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)

# Run the main window loop
window.mainloop()
