import os
from tkinter import Tk, Button, filedialog, Label, OptionMenu, StringVar, Canvas, simpledialog, messagebox, Frame
from PIL import Image, ImageTk

class LogoOverlayApp:
    def __init__(self, master):
        self.master = master
        master.title("Aplicativo de Logo Fotografia")
        master.geometry("1400x1000")  # Window size

        # Initialize variables
        self.images = []
        self.logo_path = None
        self.current_image = None
        self.logo_position = StringVar(value="bottom-right")
        self.positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center", "custom"]
        self.custom_logo_pos = None  # Store custom logo position (x, y) in canvas coordinates
        self.logo_item = None  # Canvas item for the logo
        self.logo_bbox = None  # Canvas item for logo bounding box
        self.dragging = False  # Track dragging state
        self.logo_size = 150  # Default logo size (pixels)
        self.image_scale = 1.0  # Scaling factor for canvas image
        self.zoom_level = 1.0  # Zoom factor (0.5x, 1.0x, 1.5x)
        self.photo = None  # ImageTk.PhotoImage for base image
        self.logo_photo = None  # ImageTk.PhotoImage for logo

        # GUI Elements
        self.label = Label(master, text="Selecione suas fotos e o logo", font=("Arial", 12))
        self.label.pack(pady=5)

        self.dimension_label = Label(master, text="Dimensões da Foto: Nenhuma foto selecionada")
        self.dimension_label.pack(pady=5)

        self.status_label = Label(master, text="Pronto", fg="blue", font=("Arial", 10))
        self.status_label.pack(pady=5)

        self.select_images_button = Button(master, text="Selecionar Fotos", command=self.select_images, font=("Arial", 10), bg="#03fc1c")
        self.select_images_button.pack(pady=5)

        self.select_logo_button = Button(master, text="Selecionar Logo", command=self.select_logo, font=("Arial", 10), bg="#fcad03")
        self.select_logo_button.pack(pady=5)

        self.select_size_button = Button(master, text="Definir Tamanho do Logo", command=self.set_logo_size, font=("Arial", 10), bg="#03f4fc")
        self.select_size_button.pack(pady=5)

        self.position_label = Label(master, text="Posição do Logo", font=("Arial", 10))
        self.position_label.pack(pady=5)

        self.position_menu = OptionMenu(master, self.logo_position, *self.positions, command=self.update_preview)
        self.position_menu.pack(pady=5)

        # Frame to hold Zoom, Apply, and Save buttons side by side
        self.button_frame = Frame(master)
        self.button_frame.pack(pady=5)

        self.zoom_button = Button(self.button_frame, text="Zoom Imagem", command=self.toggle_zoom, font=("Arial", 10), bg="#55aaff")
        self.zoom_button.pack(side="left", padx=5)

        self.apply_button = Button(self.button_frame, text="Aplicar e Visualizar", command=self.preview_logo, font=("Arial", 10), bg="#fcad03")
        self.apply_button.pack(side="left", padx=5)

        self.save_button = Button(self.button_frame, text="Salvar Fotos", command=self.save_images, font=("Arial", 10), bg="#03fc6f")
        self.save_button.pack(side="left", padx=5)

        self.reset_position_button = Button(master, text="Redefinir Posição", command=self.reset_position, font=("Arial", 10), bg="#ff5555")
        self.reset_position_button.pack(pady=5)

        self.canvas = Canvas(master, width=1000, height=550, bg="white")
        self.canvas.pack(pady=10)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.set_logo_position)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

        # Bind arrow key events
        self.master.bind("<Up>", self.move_logo)
        self.master.bind("<Down>", self.move_logo)
        self.master.bind("<Left>", self.move_logo)
        self.master.bind("<Right>", self.move_logo)

    def select_images(self):
        self.images = filedialog.askopenfilenames(title="Selecionar Fotos", filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
        if self.images:
            self.current_image = self.images[0]
            self.display_image(self.current_image)
            self.status_label.config(text=f"{len(self.images)} foto(s) selecionada(s)", fg="green")
        else:
            self.status_label.config(text="Nenhuma foto selecionada", fg="red")

    def select_logo(self):
        self.logo_path = filedialog.askopenfilename(title="Selecionar Logo", filetypes=[("Imagens", "*.png *.jpg *.webp")])
        if self.logo_path:
            self.status_label.config(text="Logo selecionado com sucesso", fg="green")
            if self.current_image:
                self.preview_logo()
        else:
            self.status_label.config(text="Nenhum logo selecionado", fg="red")

    def set_logo_size(self):
        size = simpledialog.askinteger(
            "Tamanho do Logo",
            "Digite o tamanho do logo (50 a 900 pixels):",
            parent=self.master,
            minvalue=50,
            maxvalue=900,
            initialvalue=self.logo_size
        )
        if size is not None:
            self.logo_size = size
            self.status_label.config(text=f"Tamanho do logo definido: {self.logo_size}px", fg="green")
            if self.current_image and self.logo_path:
                self.preview_logo()
        else:
            self.status_label.config(text="Tamanho do logo não alterado", fg="orange")

    def reset_position(self):
        self.logo_position.set("bottom-right")
        self.custom_logo_pos = None
        self.status_label.config(text="Posição redefinida para canto inferior direito", fg="blue")
        if self.current_image and self.logo_path:
            self.preview_logo()

    def toggle_zoom(self):
        # Cycle through zoom levels: 0.5x, 1.0x, 1.5x
        zoom_levels = [0.5, 1.0, 1.5]
        current_index = zoom_levels.index(self.zoom_level) if self.zoom_level in zoom_levels else 1
        next_index = (current_index + 1) % len(zoom_levels)
        self.zoom_level = zoom_levels[next_index]
        self.status_label.config(text=f"Zoom ajustado para {self.zoom_level}x", fg="blue")
        if self.current_image:
            self.display_image(self.current_image)
            if self.logo_path:
                self.preview_logo()

    def display_image(self, img_path):
        img = Image.open(img_path).convert("RGBA")
        # Calculate scaling to fit within 1000x550, adjusted by zoom level
        img_width, img_height = img.size
        canvas_width, canvas_height = 1000, 550
        scale = min(canvas_width / img_width, canvas_height / img_height) * self.zoom_level
        self.image_scale = scale
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        # Center image in canvas
        self.canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.photo)
        # Update dimension label
        original_img = Image.open(img_path)
        self.dimension_label.config(text=f"Dimensões da Foto: {original_img.width} x {original_img.height} pixels")

    def get_logo_position(self, base, logo):
        if self.logo_position.get() == "custom" and self.custom_logo_pos:
            # Convert canvas coordinates to original image coordinates
            canvas_width, canvas_height = 1000, 550
            img_width, img_height = base.size
            display_width = int(img_width * self.image_scale)
            display_height = int(img_height * self.image_scale)
            img_left = (canvas_width - display_width) / 2
            img_top = (canvas_height - display_height) / 2
            scale_x = img_width / display_width
            scale_y = img_height / display_height
            canvas_x, canvas_y = self.custom_logo_pos
            # Adjust for image offset and scaling
            x = (canvas_x - img_left) * scale_x
            y = (canvas_y - img_top) * scale_y
            # Ensure logo stays within image bounds
            x = max(0, min(x, img_width - logo.width))
            y = max(0, min(y, img_height - logo.height))
            return (int(x), int(y))
        position = self.logo_position.get()
        margin = 10
        if position == "top-left":
            return (margin, margin)
        elif position == "top-right":
            return (base.width - logo.width - margin, margin)
        elif position == "bottom-left":
            return (margin, base.height - logo.height - margin)
        elif position == "center":
            return ((base.width - logo.width) // 2, (base.height - logo.height) // 2)
        else:  # bottom-right
            return (base.width - logo.width - margin, base.height - logo.height - margin)

    def set_logo_position(self, event):
        if not self.current_image or not self.logo_path:
            return
        # Set logo position to where the user clicked (top-left of logo)
        self.logo_position.set("custom")
        logo_canvas_size = self.logo_size * self.image_scale
        # Adjust to place logo's top-left at click point
        self.custom_logo_pos = (event.x, event.y)
        self.status_label.config(text=f"Logo posicionado em ({event.x}, {event.y})", fg="blue")
        self.preview_logo()

    def on_drag(self, event):
        if not self.current_image or not self.logo_path:
            return
        self.dragging = True
        self.logo_position.set("custom")
        logo_canvas_size = self.logo_size * self.image_scale
        # Update logo position to follow mouse (top-left of logo)
        self.custom_logo_pos = (event.x, event.y)
        self.status_label.config(text=f"Arrastando logo para ({event.x}, {event.y})", fg="blue")
        self.preview_logo()

    def stop_drag(self, event):
        if self.dragging:
            self.dragging = False
            self.status_label.config(text=f"Logo posicionado em ({self.custom_logo_pos[0]}, {self.custom_logo_pos[1]})", fg="blue")

    def move_logo(self, event):
        if not self.current_image or not self.logo_path:
            return
        if self.custom_logo_pos is None:
            self.custom_logo_pos = (0, 0)
        x, y = self.custom_logo_pos
        step = 5
        if event.keysym == "Up":
            y -= step
        elif event.keysym == "Down":
            y += step
        elif event.keysym == "Left":
            x -= step
        elif event.keysym == "Right":
            x += step
        # Keep logo within canvas image bounds
        canvas_width, canvas_height = 1000, 550
        logo_canvas_size = self.logo_size * self.image_scale
        img_width = int(Image.open(self.current_image).size[0] * self.image_scale)
        img_height = int(Image.open(self.current_image).size[1] * self.image_scale)
        img_left = (canvas_width - img_width) / 2
        img_top = (canvas_height - img_height) / 2
        x = max(img_left, min(x, img_left + img_width - logo_canvas_size))
        y = max(img_top, min(y, img_top + img_height - logo_canvas_size))
        self.custom_logo_pos = (x, y)
        self.logo_position.set("custom")
        self.status_label.config(text=f"Logo movido para ({x}, {y})", fg="blue")
        self.preview_logo()

    def update_preview(self, *args):
        if self.current_image and self.logo_path:
            self.preview_logo()

    def preview_logo(self):
        if not self.current_image or not self.logo_path:
            messagebox.showwarning("Aviso", "Selecione uma foto e um logo primeiro.")
            return

        base = Image.open(self.current_image).convert("RGBA")
        logo = Image.open(self.logo_path).convert("RGBA")
        logo = logo.resize((self.logo_size, self.logo_size), Image.Resampling.LANCZOS)

        # Prepare logo for canvas
        logo_canvas_size = int(self.logo_size * self.image_scale)
        preview_logo = logo.copy()
        preview_logo.thumbnail((logo_canvas_size, logo_canvas_size), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(preview_logo)

        # Display base image
        base_thumbnail = base.copy()
        canvas_width, canvas_height = 1000, 550
        base_thumbnail.thumbnail((int(canvas_width / self.image_scale), int(canvas_height / self.image_scale)), Image.Resampling.LANCZOS)
        base_thumbnail = base_thumbnail.resize((int(base_thumbnail.width * self.image_scale), int(base_thumbnail.height * self.image_scale)), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(base_thumbnail)

        self.canvas.delete("all")
        img_width, img_height = base_thumbnail.size
        self.canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.photo)

        # Place logo
        if self.logo_position.get() == "custom" and self.custom_logo_pos:
            logo_x, logo_y = self.custom_logo_pos
        else:
            pos = self.get_logo_position(base, logo)
            # Convert to canvas coordinates
            img_left = (canvas_width - img_width) / 2
            img_top = (canvas_height - img_height) / 2
            scale_x = img_width / base.width
            scale_y = img_height / base.height
            logo_x = img_left + pos[0] * scale_x
            logo_y = img_top + pos[1] * scale_y
            self.custom_logo_pos = (logo_x, logo_y)

        # Draw logo and bounding box
        self.logo_item = self.canvas.create_image(logo_x + logo_canvas_size / 2, logo_y + logo_canvas_size / 2, image=self.logo_photo)
        self.logo_bbox = self.canvas.create_rectangle(
            logo_x, logo_y, logo_x + logo_canvas_size, logo_y + logo_canvas_size,
            outline="white", width=2
        )

    def save_images(self):
        if not self.images or not self.logo_path:
            messagebox.showwarning("Aviso", "Selecione as fotos e o logo antes de salvar.")
            return

        logo = Image.open(self.logo_path).convert("RGBA")
        logo = logo.resize((self.logo_size, self.logo_size), Image.Resampling.LANCZOS)

        saved_count = 0
        for img_path in self.images:
            output_path = filedialog.asksaveasfilename(
                title="Salvar Imagem Como",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("All files", "*.*")],
                defaultextension=".png",
                initialfile=os.path.basename(img_path)
            )
            if not output_path:
                self.status_label.config(text=f"Salvamento cancelado para: {os.path.basename(img_path)}", fg="orange")
                continue

            base = Image.open(img_path).convert("RGBA")
            pos = self.get_logo_position(base, logo)
            base.paste(logo, pos, logo)

            ext = os.path.splitext(output_path)[1].lower()
            if ext in (".jpg", ".jpeg"):
                base = base.convert("RGB")
                base.save(output_path, format="JPEG", quality=95)
            else:
                base.save(output_path, format="PNG")

            saved_count += 1

        if saved_count > 0:
            messagebox.showinfo("Sucesso", f"{saved_count} foto(s) salva(s) com sucesso!")
            self.status_label.config(text=f"{saved_count} foto(s) salva(s)", fg="green")
        else:
            self.status_label.config(text="Nenhuma foto salva", fg="red")

if __name__ == "__main__":
    root = Tk()
    app = LogoOverlayApp(root)
    root.mainloop()
