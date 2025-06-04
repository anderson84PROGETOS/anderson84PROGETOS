import tkinter as tk
from tkinter import messagebox
import urllib.request
import json
import webbrowser

class GeolocationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Geolocalização de Domínio ou IP")
        self.root.geometry("800x600")
        self.root.configure(bg="black")
        root.wm_state('zoomed')

        self.font_style = ("Courier New", 12)

        tk.Label(root, text="Digite o IP ou Domínio", fg="lime", bg="black", font=self.font_style).pack(pady=10)

        self.entry = tk.Entry(root, font=self.font_style, fg="lime", bg="#111", insertbackground="lime", width=50)
        self.entry.pack(pady=5, ipady=5)        

        self.search_btn = tk.Button(root, text="Buscar Localização", font=self.font_style, fg="black", bg="lime",
                                    activebackground="green", command=self.buscar_geo)
        self.search_btn.pack(pady=10)
        
        self.result_label = tk.Text(root, width=123, height=27, wrap=tk.WORD, bg="#111", fg="lime", font=self.font_style)
        self.result_label.pack(padx=10, pady=10)

        self.button_frame = tk.Frame(root, bg="black")
        self.button_frame.pack(pady=5)

        self.copy_btn = tk.Button(self.button_frame, text="Copiar Resultado", font=self.font_style, fg="black", bg="lime",
                                  command=self.copy_result)
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        self.bgp_btn = tk.Button(self.button_frame, text="Abrir BGP", font=self.font_style, fg="black", bg="lime",
                                 command=self.open_bgp)
        self.bgp_btn.pack(side=tk.LEFT, padx=5)
        self.bgp_btn.config(state=tk.DISABLED)

        self.maps_btn = tk.Button(self.button_frame, text="Google Maps", font=self.font_style, fg="black", bg="lime",
                                  command=self.open_google_maps_link)
        self.maps_btn.pack(side=tk.LEFT, padx=5)

        self.street_btn = tk.Button(self.button_frame, text="Street View", font=self.font_style, fg="black", bg="lime",
                                    command=self.open_street_view_link)
        self.street_btn.pack(side=tk.LEFT, padx=5)

        self.current_lat = None
        self.current_lon = None
        self.current_as_number = None

    def buscar_geo(self):
        dominio = self.entry.get().strip()
        self.result_label.delete(1.0, tk.END)
        self.current_lat = self.current_lon = self.current_as_number = None
        self.bgp_btn.config(state=tk.DISABLED)

        if not dominio or dominio == "exemplo.com":
            messagebox.showerror("Erro", "Por favor, insira um domínio ou IP válido.")
            return

        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{dominio}") as response:
                data = json.loads(response.read().decode())

            if data.get("status") != "success":
                raise Exception(data.get("message", "Erro desconhecido"))

            lat, lon = data["lat"], data["lon"]
            city, country = data["city"], data["country"]
            query = data["query"]
            as_info = data.get("as", "")

            as_number = org_name = bgp_link = ""
            if as_info and "AS" in as_info:
                parts = as_info.split(" ", 1)
                as_number = parts[0]
                org_name = parts[1] if len(parts) > 1 else "Não disponível"
                bgp_link = f"https://bgp.he.net/{as_number}"
                self.current_as_number = as_number
                self.bgp_btn.config(state=tk.NORMAL)

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

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar dados: {str(e)}")

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
