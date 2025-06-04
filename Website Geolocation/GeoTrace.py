import tkinter as tk
from tkinter import messagebox
import requests
import folium
import webbrowser
from datetime import datetime
import time
import random
import threading
import tempfile
import os

class GeolocationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Geolocalização de Domínio ou IP")
        self.root.configure(bg="#000000")
        self.root.geometry("1000x700")
        root.wm_state('zoomed')

        self.font_style = ("Courier New", 12)
        self.header_font = ("Courier New", 20, "bold")

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)
        self.chars = "01"
        self.font_size = 14
        self.columns = int(self.root.winfo_screenwidth() / self.font_size)
        self.drops = [1] * self.columns
        threading.Thread(target=self.draw_matrix, daemon=True).start()

        self.clock_label = tk.Label(self.root, font=("Courier New", 24, "bold"), fg="#00ff00", bg="#000000")
        self.clock_label.pack(pady=10)
        self.update_clock()

        self.title_label = tk.Label(self.root, text="Geolocalização de Domínio ou IP", font=self.header_font, fg="#00ff00", bg="#000000")
        self.title_label.pack(pady=10)

        self.input_frame = tk.Frame(self.root, bg="#000000")
        self.input_frame.pack(pady=10)
        self.domain_entry = tk.Entry(self.input_frame, font=self.font_style, bg="#111111", fg="#00ff00", insertbackground="#00ff00")
        self.domain_entry.pack(side=tk.LEFT, padx=5, ipady=5)
        self.domain_entry.insert(0, "Digite o domínio ou IP")
        self.domain_entry.bind("<FocusIn>", lambda e: self.domain_entry.delete(0, tk.END))

        self.search_button = tk.Button(self.input_frame, text="Buscar Localização", font=self.font_style,
                                       bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                       activeforeground="#000000", command=self.get_geo)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.bgp_button = tk.Button(self.input_frame, text="Abrir Detalhes AS", font=self.font_style,
                                    bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                    activeforeground="#000000", command=self.open_bgp)
        self.bgp_button.pack(side=tk.LEFT, padx=5)
        self.bgp_button.config(state=tk.DISABLED)

        self.result_frame = tk.Frame(self.root, bg="#111111", bd=2, relief="solid")
        self.result_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        self.result_label = tk.Text(self.result_frame, font=self.font_style, fg="#00ff00",
                                    bg="#111111", wrap=tk.WORD, height=15)
        self.result_label.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.map_button_frame = tk.Frame(self.root, bg="#000000")
        self.map_button_frame.pack(pady=10)

        self.map1_button = tk.Button(self.map_button_frame, text="Abrir OpenStreetMap", font=self.font_style,
                                     bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                     activeforeground="#000000", command=self.open_temp_map1)
        self.map1_button.pack(side=tk.LEFT, padx=10)

        self.map2_button = tk.Button(self.map_button_frame, text="Abrir Google Maps Style", font=self.font_style,
                                     bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                     activeforeground="#000000", command=self.open_temp_map2)
        self.map2_button.pack(side=tk.LEFT, padx=10)

        self.google_maps_button = tk.Button(self.map_button_frame, text="Abrir Google Maps (Link)", font=self.font_style,
                                            bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                            activeforeground="#000000", command=self.open_google_maps_link)
        self.google_maps_button.pack(side=tk.LEFT, padx=10)

        self.street_view_button = tk.Button(self.map_button_frame, text="Abrir Street View", font=self.font_style,
                                            bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                            activeforeground="#000000", command=self.open_street_view_link)
        self.street_view_button.pack(side=tk.LEFT, padx=10)

        self.copy_button = tk.Button(self.map_button_frame, text="Copiar Resultado", font=self.font_style,
                                     bg="#000000", fg="#00ff00", activebackground="#00ff00",
                                     activeforeground="#000000", command=self.copy_result)
        self.copy_button.pack(side=tk.LEFT, padx=10)

        self.footer_label = tk.Label(self.root, text="© Geolocalização de Domínio ou IP", font=self.font_style, fg="#00ff00", bg="#000000")
        self.footer_label.pack(pady=10)

        self.current_lat = None
        self.current_lon = None
        self.current_as_number = None
        self.temp_file_map1 = None
        self.temp_file_map2 = None

    def draw_matrix(self):
        while True:
            self.canvas.delete("char")
            for i in range(len(self.drops)):
                char = random.choice(self.chars)
                x = i * self.font_size
                y = self.drops[i] * self.font_size
                self.canvas.create_text(x, y, text=char, fill="#00ff00", font=("Courier New", self.font_size), tags="char")
                if y > self.root.winfo_screenheight() and random.random() > 0.975:
                    self.drops[i] = 0
                self.drops[i] += 1
            self.canvas.update()
            time.sleep(0.033)

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def get_geo(self):
        domain = self.domain_entry.get().strip()
        self.result_label.delete(1.0, tk.END)
        self.current_as_number = None
        self.bgp_button.config(state=tk.DISABLED)
        self.temp_file_map1 = None
        self.temp_file_map2 = None

        if not domain or domain == "Digite o domínio ou IP":
            messagebox.showerror("Erro", "Por favor, insira um domínio ou IP válido.")
            return

        try:
            response = requests.get(f"http://ip-api.com/json/{domain}", timeout=5)
            data = response.json()

            if data.get("status") != "success":
                messagebox.showerror("Erro", f"Erro: {data.get('message', 'Desconhecido')}")
                return

            lat, lon = data["lat"], data["lon"]
            city, country = data["city"], data["country"]
            isp, query = data["isp"], data["query"]
            as_info = data.get("as", "")

            as_number = org_name = bgp_link = ""
            if as_info and "AS" in as_info:
                parts = as_info.split(" ", 1)
                as_number = parts[0]
                org_name = parts[1] if len(parts) > 1 else "Não disponível"
                bgp_link = f"https://bgp.he.net/{as_number}"
                self.current_as_number = as_number
                self.bgp_button.config(state=tk.NORMAL)

            result_text = (
                f"Resultado da Geolocalização\n\n"
                f"\nIP: {query}\n"
                f"\nCidade: {city}\n"
                f"\nPaís: {country}\n"
            )
            if as_number:
                result_text += (
                    f"\nOrganização: {org_name}\n"
                    f"\nNúmero AS: {as_number}\n"
                    f"\nDetalhes AS: {bgp_link}\n"
                )
            result_text += (
                f"\n\nLatitude: {lat}\n"
                f"\nLongitude: {lon}\n"
                f"\nGeolocalização: {lat},{lon}\n\n"
                f"Google Maps: https://www.google.com/maps/place/{lat},{lon}\n\n"
                f"Street View: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=-45&pitch=38&fov=80"
            )

            self.result_label.insert(tk.END, result_text)

            self.current_lat = lat
            self.current_lon = lon

            map1 = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon], popup=f"{city}, {country} | {query}").add_to(map1)
            self.temp_file_map1 = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            map1.save(self.temp_file_map1.name)

            map2 = folium.Map(location=[lat, lon], zoom_start=10, tiles=None)
            folium.TileLayer(
                tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                attr="Google Maps",
                name="Google Maps",
                overlay=False,
                control=False
            ).add_to(map2)
            folium.Marker([lat, lon], popup=f"{city}, {country} | {query}").add_to(map2)
            self.temp_file_map2 = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            map2.save(self.temp_file_map2.name)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar dados: {str(e)}")

    def open_temp_map1(self):
        if self.temp_file_map1:
            webbrowser.open(f"file://{self.temp_file_map1.name}")
        else:
            messagebox.showwarning("Aviso", "O mapa ainda não foi gerado.")

    def open_temp_map2(self):
        if self.temp_file_map2:
            webbrowser.open(f"file://{self.temp_file_map2.name}")
        else:
            messagebox.showwarning("Aviso", "O mapa ainda não foi gerado.")

    def open_google_maps_link(self):
        if self.current_lat is not None and self.current_lon is not None:
            url = f"https://www.google.com/maps/place/{self.current_lat},{self.current_lon}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Aviso", "Nenhuma localização válida encontrada para abrir no Google Maps.")

    def open_street_view_link(self):
        if self.current_lat is not None and self.current_lon is not None:
            url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={self.current_lat},{self.current_lon}&heading=-45&pitch=38&fov=80"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Aviso", "Nenhuma localização válida encontrada para abrir no Street View.")

    def open_bgp(self):
        if self.current_as_number:
            url = f"https://bgp.he.net/{self.current_as_number}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Aviso", "Nenhum número AS disponível.")

    def copy_result(self):
        text = self.result_label.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            messagebox.showinfo("Copiado", "Resultado copiado para a área de transferência.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GeolocationApp(root)
    root.mainloop()
