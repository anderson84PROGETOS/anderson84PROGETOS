import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import numpy as np
import os
import copy

class Layer:
    def __init__(self, image, name, width, height):
        self.original_image = image
        self.image = image
        self.name = name
        self.original_width = width  # Store original dimensions
        self.original_height = height
        self.width = width  # Current dimensions (may change with rotation)
        self.height = height
        self.rotation = 0
        self.watermark = None
        self.watermark_x = 0
        self.watermark_y = 0
        self.watermark_scale = 0.2
        self.adjustments = {
            'brightness': 0,
            'contrast': 0,
            'levels': 1,
            'exposure': 0,
            'curves': 1,
            'sharpen': 0
        }
        self.history = []  # List to store state history
        self.save_state()  # Save initial state

    def save_state(self):
        """Save the current state to history."""
        state = {
            'image': self.image.copy(),
            'rotation': self.rotation,
            'watermark': self.watermark.copy() if self.watermark else None,
            'watermark_x': self.watermark_x,
            'watermark_y': self.watermark_y,
            'watermark_scale': self.watermark_scale,
            'adjustments': copy.deepcopy(self.adjustments),
            'width': self.width,
            'height': self.height
        }
        self.history.append(state)

    def undo(self):
        """Revert to the previous state in history."""
        if len(self.history) > 1:  # Ensure there's at least one state to revert to
            self.history.pop()  # Remove current state
            prev_state = self.history[-1]  # Get previous state
            self.image = prev_state['image'].copy()
            self.rotation = prev_state['rotation']
            self.watermark = prev_state['watermark'].copy() if prev_state['watermark'] else None
            self.watermark_x = prev_state['watermark_x']
            self.watermark_y = prev_state['watermark_y']
            self.watermark_scale = prev_state['watermark_scale']
            self.adjustments = copy.deepcopy(prev_state['adjustments'])
            self.width = prev_state['width']
            self.height = prev_state['height']
            return True
        return False

class PhotoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Fotos Múltiplas")
        self.layers = []
        self.current_layer_index = -1
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        root.wm_state('zoomed')
        root.geometry("1280x1000")

        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.toolbar = tk.Frame(self.container, bg="#333")
        self.toolbar.pack(fill="x")

        tk.Button(self.toolbar, text="Carregar Imagem", command=self.load_image, bg="#02f523", fg="black").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Salvar como PNG", command=self.show_size_menu, bg="#05e3eb", fg="black").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Marca d'água", command=self.load_watermark, bg="#05f7b7", fg="black").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Remover Marca d'água", command=self.remove_watermark, bg="#eb8f05", fg="black").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Girar 90° ↻", command=lambda: self.rotate_layer(90), bg="#555", fg="white").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Girar 90° ↺", command=lambda: self.rotate_layer(-90), bg="#555", fg="white").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Girar 180°", command=lambda: self.rotate_layer(180), bg="#555", fg="white").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Redefinir Tudo", command=self.reset_all_adjustments, bg="#f257a7", fg="white").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Redefinir um para trás", command=self.undo_last_action, bg="#f5389a", fg="black").pack(side="left", padx=5, pady=5)
        tk.Button(self.toolbar, text="Excluir Camada", command=self.delete_layer, bg="#06cf06", fg="black").pack(side="left", padx=5, pady=5)

        self.main_frame = tk.Frame(self.container)
        self.main_frame.pack(fill="both", expand=True)

        self.layers_frame = tk.Frame(self.main_frame, bg="#f0f0f0", width=200)
        self.layers_frame.pack(side="right", fill="y", padx=(5, 0))

        tk.Label(self.layers_frame, text="Camadas", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=5)

        self.layers_list_frame = tk.Frame(self.layers_frame, bg="#f0f0f0")
        self.layers_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.layers_scrollbar = ttk.Scrollbar(self.layers_list_frame, orient="vertical")
        self.layers_scrollbar.pack(side="right", fill="y")

        self.layers_listbox = tk.Listbox(self.layers_list_frame, width=30, height=30, yscrollcommand=self.layers_scrollbar.set)
        self.layers_listbox.pack(side="left", fill="both", expand=True)
        self.layers_scrollbar.config(command=self.layers_listbox.yview)
        self.layers_listbox.bind('<<ListboxSelect>>', self.select_layer)

        self.adjustments_frame = tk.Frame(self.main_frame, bg="#444")
        self.adjustments_frame.pack(fill="x")

        tk.Label(self.adjustments_frame, text="Ajustes", bg="#444", fg="white", font=("Arial", 12, "bold")).pack(pady=5)

        self.sliders = {}
        adjustments = [
            ("Brilho", "brightness", -100, 100, 0),
            ("Contraste", "contrast", -100, 100, 0),
            ("Gama", "levels", 0.1, 2, 1, 0.1),
            ("Exposição", "exposure", -2, 2, 0, 0.1),
            ("Curvas", "curves", 0.1, 2, 1, 0.1),
            ("Nitidez", "sharpen", 0, 2, 0, 0.1),
            ("Tamanho da Marca d'água", "watermark_scale", 0.1, 0.5, 0.2, 0.01)
        ]

        for label, key, min_val, max_val, default, *step in adjustments:
            frame = tk.Frame(self.adjustments_frame, bg="#444")
            frame.pack(fill="x", padx=5, pady=2)
            tk.Label(frame, text=label, bg="#444", fg="white").pack(side="left")
            slider = tk.Scale(frame, from_=min_val, to=max_val, orient="horizontal", resolution=step[0] if step else 1,
                             command=lambda value, k=key: self.apply_adjustments(k, float(value)), bg="#444", fg="white")
            slider.set(default)
            slider.pack(side="left", fill="x", expand=True)
            self.sliders[key] = slider

        self.canvas_frame = tk.Frame(self.main_frame, bg="#eee")
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#eee")
        self.canvas.pack(expand=True, fill="both")

        # Add label for original image size below canvas
        self.size_label = tk.Label(self.canvas_frame, text="", bg="#eee", font=("Arial", 10))
        self.size_label.pack(side="bottom", pady=5)

        self.size_options = [
            ("Original", None, None),
            ("1280x900 (Custom)", 1280, 900),
            ("2048x1365 (Normal)", 2048, 1365),
            ("160x120", 160, 120),
            ("320x240", 320, 240),
            ("640x480", 640, 480),
            ("800x600", 800, 600),
            ("1024x768", 1024, 768),
            ("1280x720 (HD)", 1280, 720),
            ("1366x768", 1366, 768),
            ("1600x900", 1600, 900),
            ("1920x1080 (Full HD)", 1920, 1080),
            ("2560x1440 (QHD)", 2560, 1440),
            ("3840x2160 (4K UHD)", 3840, 2160),
            ("5472x3648 (4K Grande)", 5472, 3648),
            ("960x640", 960, 640),
            ("1440x960", 1440, 960),
            ("100x100", 100, 100),
            ("500x500", 500, 500),
            ("1080x1080 (Instagram)", 1080, 1080),
            ("1200x628 (Facebook Link)", 1200, 628),
            ("1080x1920 (Stories/Vertical)", 1080, 1920),
        ]

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Leave>", self.on_mouse_leave)
        self.root.bind("<Delete>", lambda event: self.delete_layer())
        self.root.bind("<Up>", lambda event: self.move_watermark_with_keys("up"))
        self.root.bind("<Down>", lambda event: self.move_watermark_with_keys("down"))
        self.root.bind("<Left>", lambda event: self.move_watermark_with_keys("left"))
        self.root.bind("<Right>", lambda event: self.move_watermark_with_keys("right"))

        self.update_layers_list()

    def load_image(self):
        files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if not files:
            return

        for file in files:
            try:
                img = Image.open(file)
                original_width, original_height = img.size  # Get original size before thumbnail
                max_width = int(self.root.winfo_screenwidth() * 0.8)
                max_height = int(self.root.winfo_screenheight() * 0.6)
                img.thumbnail((max_width, max_height), Image.LANCZOS)
                layer = Layer(img, os.path.basename(file), original_width, original_height)
                self.layers.append(layer)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar {os.path.basename(file)}: {str(e)}")

        self.current_layer_index = len(self.layers) - 1
        self.update_layers_list()
        self.update_adjustments_ui()
        self.render_current_layer()

    def load_watermark(self):
        if self.current_layer_index == -1:
            messagebox.showwarning("Aviso", "Selecione uma camada primeiro.")
            return
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file:
            try:
                layer = self.layers[self.current_layer_index]
                layer.save_state()
                watermark = Image.open(file)
                layer.watermark = watermark
                layer.watermark_scale = 0.2
                layer.watermark_x = 0
                layer.watermark_y = 0
                self.update_adjustments_ui()
                self.render_current_layer()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar marca d'água: {str(e)}")

    def remove_watermark(self):
        if self.current_layer_index == -1:
            messagebox.showwarning("Aviso", "Selecione uma camada primeiro.")
            return
        layer = self.layers[self.current_layer_index]
        layer.save_state()
        layer.watermark = None
        layer.watermark_x = 0
        layer.watermark_y = 0
        layer.watermark_scale = 0.2
        self.update_adjustments_ui()
        self.render_current_layer()

    def rotate_layer(self, angle):
        if self.current_layer_index == -1:
            messagebox.showwarning("Aviso", "Selecione uma camada primeiro.")
            return
        layer = self.layers[self.current_layer_index]
        layer.save_state()
        layer.rotation = (layer.rotation + angle) % 360
        layer.width = layer.original_image.width
        layer.height = layer.original_image.height
        if abs(layer.rotation % 180) == 90:
            layer.width, layer.height = layer.height, layer.width
        layer.image = layer.original_image.copy().rotate(layer.rotation, expand=True)
        self.render_current_layer()

    def move_watermark_with_keys(self, direction):
        if self.current_layer_index == -1 or not self.layers[self.current_layer_index].watermark:
            return
        layer = self.layers[self.current_layer_index]
        layer.save_state()
        step = 5
        img_width = layer.width
        img_height = layer.height
        watermark_width = img_width * layer.watermark_scale
        watermark_height = (layer.watermark.height / layer.watermark.width) * watermark_width

        if direction == "up":
            layer.watermark_y -= step
        elif direction == "down":
            layer.watermark_y += step
        elif direction == "left":
            layer.watermark_x -= step
        elif direction == "right":
            layer.watermark_x += step

        layer.watermark_x = max(-img_width / 2, min(layer.watermark_x, img_width / 2 - watermark_width))
        layer.watermark_y = max(-img_height / 2, min(layer.watermark_y, img_height / 2 - watermark_height))

        self.render_current_layer()

    def undo_last_action(self):
        if self.current_layer_index == -1:
            messagebox.showwarning("Aviso", "Selecione uma camada primeiro.")
            return
        layer = self.layers[self.current_layer_index]
        if layer.undo():
            self.update_adjustments_ui()
            self.render_current_layer()
        else:
            messagebox.showinfo("Info", "Não há ações para desfazer.")

    def update_layers_list(self):
        self.layers_listbox.delete(0, tk.END)
        for i, layer in enumerate(self.layers):
            self.layers_listbox.insert(tk.END, f"{layer.name} (Camada {i + 1})")
            if i == self.current_layer_index:
                self.layers_listbox.selection_set(i)

    def select_layer(self, event):
        selection = self.layers_listbox.curselection()
        if selection:
            self.current_layer_index = selection[0]
            self.update_adjustments_ui()
            self.render_current_layer()
            # Update size label with original dimensions
            layer = self.layers[self.current_layer_index]
            self.size_label.config(text=f"Tamanho Original: {layer.original_width} x {layer.original_height} pixels")
        else:
            self.size_label.config(text="")

    def delete_layer(self):
        if self.current_layer_index == -1 or not self.layers:
            return
        self.layers.pop(self.current_layer_index)
        if self.layers:
            self.current_layer_index = min(self.current_layer_index, len(self.layers) - 1)
        else:
            self.current_layer_index = -1
            self.canvas.delete("all")
            self.size_label.config(text="")
        self.update_layers_list()
        self.update_adjustments_ui()
        if self.current_layer_index != -1:
            self.render_current_layer()

    def reset_all_adjustments(self):
        if self.current_layer_index == -1:
            return
        layer = self.layers[self.current_layer_index]
        layer.save_state()
        layer.adjustments = {
            'brightness': 0,
            'contrast': 0,
            'levels': 1,
            'exposure': 0,
            'curves': 1,
            'sharpen': 0
        }
        layer.watermark = None
        layer.watermark_x = 0
        layer.watermark_y = 0
        layer.watermark_scale = 0.2
        layer.rotation = 0
        layer.image = layer.original_image.copy()
        layer.width = layer.original_image.width
        layer.height = layer.original_image.height
        self.update_adjustments_ui()
        self.render_current_layer()

    def update_adjustments_ui(self):
        if self.current_layer_index == -1:
            for key, slider in self.sliders.items():
                slider.set({'brightness': 0, 'contrast': 0, 'levels': 1, 'exposure': 0, 'curves': 1, 'sharpen': 0, 'watermark_scale': 0.2}[key])
            self.size_label.config(text="")
            return
        layer = self.layers[self.current_layer_index]
        for key, slider in self.sliders.items():
            slider.set(layer.adjustments.get(key, layer.watermark_scale if key == 'watermark_scale' else 0))
        self.size_label.config(text=f"Tamanho Original: {layer.original_width} x {layer.original_height} pixels")

    def apply_adjustments(self, adjustment_type, value):
        if self.current_layer_index == -1:
            return
        layer = self.layers[self.current_layer_index]
        layer.save_state()
        if adjustment_type == 'watermark_scale':
            layer.watermark_scale = value
        else:
            layer.adjustments[adjustment_type] = value
        self.render_current_layer()

    def show_size_menu(self):
        if self.current_layer_index == -1:
            messagebox.showwarning("Aviso", "Selecione uma camada para salvar.")
            return
        size_menu = tk.Toplevel(self.root)
        size_menu.title("Escolha o tamanho para salvar")
        size_menu.geometry("350x750")
        for label, width, height in self.size_options:
            tk.Button(size_menu, text=label, command=lambda w=width, h=height: self.save_canvas_with_size(w, h)).pack(fill="x", padx=5, pady=2)
        tk.Button(size_menu, text="Cancelar", command=size_menu.destroy).pack(fill="x", padx=5, pady=10)

    def apply_sharpen(self, image, sharpen_amount):
        if sharpen_amount <= 0:
            return image
        return image.filter(ImageFilter.UnsharpMask(radius=2, percent=int(sharpen_amount * 100), threshold=3))

    def render_current_layer(self):
        if self.current_layer_index == -1:
            self.canvas.delete("all")
            self.size_label.config(text="")
            return
        layer = self.layers[self.current_layer_index]
        img = layer.image.copy()

        img = ImageEnhance.Brightness(img).enhance(1 + layer.adjustments['brightness'] / 100)
        img = ImageEnhance.Contrast(img).enhance(1 + layer.adjustments['contrast'] / 100)
        img = ImageEnhance.Brightness(img).enhance(layer.adjustments['levels'])
        img = ImageEnhance.Brightness(img).enhance(2 ** layer.adjustments['exposure'])
        img = ImageEnhance.Contrast(img).enhance(layer.adjustments['curves'])
        img = self.apply_sharpen(img, layer.adjustments['sharpen'])

        max_width = int(self.canvas_frame.winfo_width() * 0.9)
        max_height = int(self.canvas_frame.winfo_height() * 0.9)
        img.thumbnail((max_width, max_height), Image.LANCZOS)
        layer.scale_factor = min(max_width / img.width, max_height / img.height)

        self.canvas.config(width=img.width, height=img.height)
        self.canvas.delete("all")
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(img.width / 2, img.height / 2, image=self.photo)

        if layer.watermark:
            watermark = layer.watermark.copy()
            watermark_width = int(img.width * layer.watermark_scale)
            watermark_height = int((layer.watermark.height / layer.watermark.width) * watermark_width)
            watermark = watermark.resize((watermark_width, watermark_height), Image.LANCZOS)
            watermark = watermark.convert("RGBA")
            img = img.convert("RGBA")
            layer.watermark_x = max(-img.width / 2, min(layer.watermark_x, img.width / 2 - watermark_width))
            layer.watermark_y = max(-img.height / 2, min(layer.watermark_y, img.height / 2 - watermark_height))
            x = int(layer.watermark_x + img.width / 2)
            y = int(layer.watermark_y + img.height / 2)
            img.paste(watermark, (x, y), watermark)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(img.width / 2, img.height / 2, image=self.photo)

        # Update size label with original dimensions
        self.size_label.config(text=f"Tamanho Original: {layer.original_width} x {layer.original_height} pixels")

    def save_canvas_with_size(self, target_width, target_height):
        if self.current_layer_index == -1:
            return
        layer = self.layers[self.current_layer_index]
        img = layer.image.copy()

        img = ImageEnhance.Brightness(img).enhance(1 + layer.adjustments['brightness'] / 100)
        img = ImageEnhance.Contrast(img).enhance(1 + layer.adjustments['contrast'] / 100)
        img = ImageEnhance.Brightness(img).enhance(layer.adjustments['levels'])
        img = ImageEnhance.Brightness(img).enhance(2 ** layer.adjustments['exposure'])
        img = ImageEnhance.Contrast(img).enhance(layer.adjustments['curves'])
        img = self.apply_sharpen(img, layer.adjustments['sharpen'])

        if target_width and target_height:
            img = img.resize((target_width, target_height), Image.LANCZOS)
        else:
            target_width, target_height = img.size

        if layer.watermark:
            watermark = layer.watermark.copy()
            watermark_width = int(target_width * layer.watermark_scale)
            watermark_height = int((layer.watermark.height / layer.watermark.width) * watermark_width)
            watermark = watermark.resize((watermark_width, watermark_height), Image.LANCZOS)
            watermark = watermark.convert("RGBA")
            img = img.convert("RGBA")
            x = int(layer.watermark_x * (target_width / layer.width) + target_width / 2)
            y = int(layer.watermark_y * (target_height / layer.height) + target_height / 2)
            img.paste(watermark, (x, y), watermark)

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            img.save(file_path)

    def is_mouse_over_watermark(self, x, y):
        if self.current_layer_index == -1 or not self.layers[self.current_layer_index].watermark:
            return False
        layer = self.layers[self.current_layer_index]
        img_width = layer.width
        img_height = layer.height
        watermark_width = img_width * layer.watermark_scale
        watermark_height = (layer.watermark.height / layer.watermark.width) * watermark_width
        canvas_x = (x - img_width / 2) / layer.scale_factor
        canvas_y = (y - img_height / 2) / layer.scale_factor
        angle = layer.rotation * np.pi / 180
        rotated_x = canvas_x * np.cos(angle) + canvas_y * np.sin(angle)
        rotated_y = -canvas_x * np.sin(angle) + canvas_y * np.cos(angle)
        return (rotated_x >= layer.watermark_x and
                rotated_x <= layer.watermark_x + watermark_width and
                rotated_y >= layer.watermark_y and
                rotated_y <= layer.watermark_y + watermark_height)

    def on_mouse_move(self, event):
        if self.current_layer_index == -1 or not self.layers[self.current_layer_index].watermark:
            self.canvas.config(cursor="arrow")
            return
        if self.is_mouse_over_watermark(event.x, event.y):
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="arrow")
        if self.is_dragging:
            layer = self.layers[self.current_layer_index]
            layer.save_state()
            img_width = layer.width
            img_height = layer.height
            canvas_x = (event.x - img_width / 2) / layer.scale_factor
            canvas_y = (event.y - img_height / 2) / layer.scale_factor
            angle = layer.rotation * np.pi / 180
            rotated_x = canvas_x * np.cos(angle) + canvas_y * np.sin(angle)
            rotated_y = -canvas_x * np.sin(angle) + canvas_y * np.cos(angle)
            watermark_width = img_width * layer.watermark_scale
            watermark_height = (layer.watermark.height / layer.watermark.width) * watermark_width
            layer.watermark_x = rotated_x - (self.drag_start_x - layer.watermark_x)
            layer.watermark_y = rotated_y - (self.drag_start_y - layer.watermark_y)
            layer.watermark_x = max(-img_width / 2, min(layer.watermark_x, img_width / 2 - watermark_width))
            layer.watermark_y = max(-img_height / 2, min(layer.watermark_y, img_height / 2 - watermark_height))
            self.render_current_layer()

    def on_mouse_down(self, event):
        if self.current_layer_index == -1 or not self.layers[self.current_layer_index].watermark:
            return
        if self.is_mouse_over_watermark(event.x, event.y):
            self.is_dragging = True
            layer = self.layers[self.current_layer_index]
            img_width = layer.width
            img_height = layer.height
            canvas_x = (event.x - img_width / 2) / layer.scale_factor
            canvas_y = (event.y - img_height / 2) / layer.scale_factor
            angle = layer.rotation * np.pi / 180
            self.drag_start_x = canvas_x * np.cos(angle) + canvas_y * np.sin(angle)
            self.drag_start_y = -canvas_x * np.sin(angle) + canvas_y * np.cos(angle)

    def on_mouse_up(self, event):
        self.is_dragging = False

    def on_mouse_leave(self, event):
        self.is_dragging = False
        self.canvas.config(cursor="arrow")

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditorApp(root)
    root.mainloop()
