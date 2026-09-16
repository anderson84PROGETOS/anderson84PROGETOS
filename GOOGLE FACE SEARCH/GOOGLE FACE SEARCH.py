import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import urllib.parse
import os
import threading
import time
import base64
import platform

# =============================================================
# SELENIUM
# =============================================================

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    SELENIUM_AVAILABLE = True

except ImportError:
    webdriver = None
    SELENIUM_AVAILABLE = False


# =============================================================
# GOOGLE FACE SEARCH
# =============================================================

class GoogleFaceSearch:

    def __init__(self, root):

        self.root = root

        # =====================================================
        # CONFIGURAÇÃO
        # =====================================================

        self.root.title("🔍 GOOGLE FACE SEARCH")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        self.root.configure(bg="#0d1117")

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass

        self.current_url = ""
        self.selected_image = ""
        self.driver = None
        self.upload_running = False

        self.center_window()
        self.create_interface()

    # =========================================================
    # CENTRALIZAR
    # =========================================================

    def center_window(self):

        self.root.update_idletasks()

        width = 900
        height = 650

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # =========================================================
    # INTERFACE
    # =========================================================

    def create_interface(self):

        # =====================================================
        # CABEÇALHO
        # =====================================================

        title_frame = tk.Frame(
            self.root,
            bg="#0d1117"
        )

        title_frame.pack(
            pady=(25, 5)
        )

        title = tk.Label(
            title_frame,
            text="🔍 GOOGLE FACE SEARCH",
            font=("Segoe UI", 26, "bold"),
            fg="#e94560",
            bg="#0d1117"
        )

        title.pack()

        subtitle = tk.Label(
            title_frame,
            text="Pesquisa por nome ou por imagem do computador",
            font=("Segoe UI", 11),
            fg="#8b949e",
            bg="#0d1117"
        )

        subtitle.pack(
            pady=(5, 0)
        )

        # =====================================================
        # NOME
        # =====================================================

        name_frame = tk.Frame(
            self.root,
            bg="#161b22"
        )

        name_frame.pack(
            fill="x",
            padx=30,
            pady=(20, 10)
        )

        name_label = tk.Label(
            name_frame,
            text="👤 PESQUISAR PELO NOME",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#161b22"
        )

        name_label.pack(
            anchor="w",
            padx=20,
            pady=(15, 8)
        )

        self.name_entry = tk.Entry(
            name_frame,
            font=("Segoe UI", 15),
            bg="#0d1117",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0
        )

        self.name_entry.pack(
            fill="x",
            padx=20,
            pady=(0, 15),
            ipady=10
        )

        self.name_entry.bind(
            "<Return>",
            lambda event: self.search_name()
        )

        # =====================================================
        # BOTÕES
        # =====================================================

        button_frame = tk.Frame(
            self.root,
            bg="#0d1117"
        )

        button_frame.pack(
            pady=8
        )

        self.search_button = tk.Button(
            button_frame,
            text="🔎  BUSCAR NO GOOGLE",
            font=("Segoe UI", 10, "bold"),
            bg="#e94560",
            fg="#ffffff",
            activebackground="#c73650",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=11,
            command=self.search_name
        )

        self.search_button.pack(
            side="left",
            padx=5
        )

        self.open_button = tk.Button(
            button_frame,
            text="🌐  ABRIR PESQUISA",
            font=("Segoe UI", 10, "bold"),
            bg="#238636",
            fg="#ffffff",
            activebackground="#196c2e",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=11,
            command=self.open_search,
            state="disabled"
        )

        self.open_button.pack(
            side="left",
            padx=5
        )

        clear_button = tk.Button(
            button_frame,
            text="🗑️  LIMPAR",
            font=("Segoe UI", 10, "bold"),
            bg="#30363d",
            fg="#ffffff",
            activebackground="#21262d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=11,
            command=self.clear
        )

        clear_button.pack(
            side="left",
            padx=5
        )

        # =====================================================
        # IMAGEM
        # =====================================================

        image_frame = tk.Frame(
            self.root,
            bg="#161b22"
        )

        image_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        image_title = tk.Label(
            image_frame,
            text="🖼️ PESQUISAR UMA IMAGEM DO PC",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#161b22"
        )

        image_title.pack(
            anchor="w",
            padx=20,
            pady=(15, 5)
        )

        image_description = tk.Label(
            image_frame,
            text="Selecione uma imagem e ela será enviada automaticamente para o Google Lens.",
            font=("Segoe UI", 10),
            fg="#8b949e",
            bg="#161b22"
        )

        image_description.pack(
            anchor="w",
            padx=20,
            pady=(0, 12)
        )

        image_button_frame = tk.Frame(
            image_frame,
            bg="#161b22"
        )

        image_button_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        # =====================================================
        # SELECIONAR
        # =====================================================

        self.image_button = tk.Button(
            image_button_frame,
            text="🖼️  SELECIONAR IMAGEM",
            font=("Segoe UI", 11, "bold"),
            bg="#8957e5",
            fg="#ffffff",
            activebackground="#6e40c9",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=25,
            pady=12,
            command=self.select_image
        )

        self.image_button.pack(
            side="left",
            padx=(0, 10)
        )

        # =====================================================
        # ABRIR IMAGEM
        # =====================================================

        self.open_image_button = tk.Button(
            image_button_frame,
            text="📂  ABRIR IMAGEM",
            font=("Segoe UI", 10, "bold"),
            bg="#30363d",
            fg="#ffffff",
            activebackground="#21262d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=12,
            command=self.open_selected_image,
            state="disabled"
        )

        self.open_image_button.pack(
            side="left"
        )

        # =====================================================
        # LINK
        # =====================================================

        link_frame = tk.Frame(
            self.root,
            bg="#161b22"
        )

        link_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=10
        )

        link_title = tk.Label(
            link_frame,
            text="🔗 LINK DA PESQUISA",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#161b22"
        )

        link_title.pack(
            anchor="w",
            padx=20,
            pady=(12, 6)
        )

        self.url_text = tk.Text(
            link_frame,
            height=4,
            font=("Consolas", 10),
            bg="#0d1117",
            fg="#58a6ff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            wrap="word"
        )

        self.url_text.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15)
        )

        self.url_text.config(
            state="disabled"
        )

        # =====================================================
        # STATUS
        # =====================================================

        self.status_label = tk.Label(
            self.root,
            text="● Digite um nome ou selecione uma imagem",
            font=("Segoe UI", 10),
            fg="#8b949e",
            bg="#0d1117"
        )

        self.status_label.pack(
            pady=(0, 15)
        )

    # =========================================================
    # URL POR NOME
    # =========================================================

    def create_url(self, name):

        base_url = "https://www.google.com/search"

        params = {
            "q": name,
            "udm": "2",
            "source": "lnt",
            "tbs": "itp:face"
        }

        query = urllib.parse.urlencode(
            params,
            quote_via=urllib.parse.quote
        )

        return f"{base_url}?{query}"

    # =========================================================
    # PESQUISA POR NOME
    # =========================================================

    def search_name(self):

        name = self.name_entry.get().strip()

        if not name:

            messagebox.showwarning(
                "Campo vazio",
                "Digite o nome da pessoa."
            )

            self.name_entry.focus()

            return

        url = self.create_url(name)

        self.current_url = url

        self.show_url(url)

        self.status_label.config(
            text="● Pesquisa por nome aberta no Google",
            fg="#00d084"
        )

        self.open_button.config(
            state="normal"
        )

        webbrowser.open(url)

    # =========================================================
    # MOSTRAR URL
    # =========================================================

    def show_url(self, url):

        self.url_text.config(
            state="normal"
        )

        self.url_text.delete(
            "1.0",
            tk.END
        )

        self.url_text.insert(
            "1.0",
            url
        )

        self.url_text.config(
            state="disabled"
        )

    # =========================================================
    # ABRIR PESQUISA
    # =========================================================

    def open_search(self):

        if self.current_url:

            webbrowser.open(
                self.current_url
            )

    # =========================================================
    # SELECIONAR IMAGEM
    # =========================================================

    def select_image(self):

        if self.upload_running:
            return

        file_path = filedialog.askopenfilename(

            title="Selecione uma imagem",

            filetypes=[
                (
                    "Imagens",
                    "*.jpg *.jpeg *.png *.webp *.gif *.bmp"
                ),
                (
                    "JPG",
                    "*.jpg *.jpeg"
                ),
                (
                    "PNG",
                    "*.png"
                ),
                (
                    "WEBP",
                    "*.webp"
                ),
                (
                    "Todas as imagens",
                    "*.*"
                )
            ]
        )

        if not file_path:
            return

        self.selected_image = os.path.abspath(
            file_path
        )

        self.open_image_button.config(
            state="normal"
        )

        self.show_url(
            self.selected_image
        )

        self.status_label.config(
            text="● Preparando imagem para o Google Lens...",
            fg="#f2cc60"
        )

        self.image_button.config(
            state="disabled"
        )

        self.search_button.config(
            state="disabled"
        )

        self.upload_running = True

        thread = threading.Thread(
            target=self.upload_image_to_lens,
            args=(self.selected_image,),
            daemon=True
        )

        thread.start()

    # =========================================================
    # CRIAR CHROME
    # =========================================================

    def create_driver(self):

        options = Options()

        options.add_argument(
            "--start-maximized"
        )

        options.add_argument(
            "--disable-notifications"
        )

        options.add_argument(
            "--disable-popup-blocking"
        )

        options.add_argument(
            "--log-level=3"
        )

        options.add_argument(
            "--disable-logging"
        )

        options.add_argument(
            "--disable-background-networking"
        )

        options.add_argument(
            "--disable-component-update"
        )

        options.add_argument(
            "--disable-default-apps"
        )

        options.add_argument(
            "--disable-sync"
        )

        options.add_argument(
            "--disable-features=MediaRouter,OptimizationHints,AutofillServerCommunication"
        )

        # =====================================================
        # REMOVER LOG DO CHROMEDRIVER
        # =====================================================

        options.add_experimental_option(
            "excludeSwitches",
            [
                "enable-logging",
                "enable-automation"
            ]
        )

        options.add_experimental_option(
            "useAutomationExtension",
            False
        )

        # =====================================================
        # SERVIÇO SILENCIOSO
        # =====================================================

        service = Service(
            log_output=os.devnull
        )

        driver = webdriver.Chrome(
            service=service,
            options=options
        )

        return driver

    # =========================================================
    # ENVIAR IMAGEM PARA GOOGLE LENS
    # =========================================================

    def upload_image_to_lens(self, file_path):

        if not SELENIUM_AVAILABLE:

            self.root.after(
                0,
                self.selenium_error
            )

            return

        driver = None

        try:

            # =================================================
            # VERIFICAR ARQUIVO
            # =================================================

            if not os.path.isfile(file_path):

                raise Exception(
                    "Arquivo de imagem não encontrado."
                )

            # =================================================
            # ABRIR CHROME
            # =================================================

            self.root.after(
                0,
                lambda: self.status_label.config(
                    text="● Abrindo Google Lens...",
                    fg="#f2cc60"
                )
            )

            driver = self.create_driver()

            self.driver = driver

            # =================================================
            # ABRIR GOOGLE
            # =================================================

            driver.get(
                "https://www.google.com/"
            )

            time.sleep(2)

            # =================================================
            # LER IMAGEM
            # =================================================

            with open(
                file_path,
                "rb"
            ) as image_file:

                image_bytes = image_file.read()

            # =================================================
            # BASE64
            # =================================================

            encoded_image = base64.b64encode(
                image_bytes
            ).decode("ascii")

            # =================================================
            # ENDPOINT ATUAL DO GOOGLE LENS
            # =================================================

            lens_endpoint = (
                "https://lens.google.com/v3/upload"
            )

            # =================================================
            # JAVASCRIPT DE UPLOAD
            # =================================================

            javascript = r"""
const b64 = arguments[0];
const endpoint = arguments[1];

const bytes = Uint8Array.from(
    atob(b64),
    c => c.charCodeAt(0)
);

const form = document.createElement("form");

form.method = "POST";
form.action = endpoint;
form.enctype = "multipart/form-data";

const file = document.createElement("input");

file.type = "file";
file.name = "encoded_image";

const dataTransfer = new DataTransfer();

dataTransfer.items.add(
    new File(
        [bytes],
        "imagem.jpg",
        {
            type: "image/jpeg"
        }
    )
);

file.files = dataTransfer.files;

form.appendChild(file);

const source = document.createElement("input");

source.type = "hidden";
source.name = "sbisrc";
source.value = "Google Chrome";

form.appendChild(source);

document.body.appendChild(form);

form.submit();
"""

            # =================================================
            # STATUS
            # =================================================

            self.root.after(
                0,
                lambda: self.status_label.config(
                    text="● Enviando imagem para o Google Lens...",
                    fg="#f2cc60"
                )
            )

            # =================================================
            # EXECUTAR UPLOAD
            # =================================================

            before_url = driver.current_url

            driver.execute_script(
                javascript,
                encoded_image,
                lens_endpoint
            )

            # =================================================
            # ESPERAR REDIRECIONAMENTO
            # =================================================

            result_url = ""

            deadline = time.time() + 40

            while time.time() < deadline:

                try:

                    current_url = driver.current_url

                except Exception:

                    current_url = ""

                if current_url:

                    if (
                        current_url != before_url
                        and
                        not current_url.startswith(
                            lens_endpoint
                        )
                    ):

                        result_url = current_url

                        # =====================================
                        # RESULTADO DO LENS
                        # =====================================

                        if (
                            "udm=26" in current_url
                            or
                            "lens.google.com" in current_url
                        ):

                            break

                time.sleep(0.5)

            # =================================================
            # VERIFICAR RESULTADO
            # =================================================

            if not result_url:

                raise Exception(
                    "O Google Lens não retornou a página de resultados."
                )

            # =================================================
            # RESULTADO
            # =================================================

            self.root.after(
                0,
                lambda url=result_url:
                    self.upload_success(url)
            )

        except Exception as error:

            error_text = str(error)

            if not error_text:

                error_text = (
                    "Não foi possível concluir o upload."
                )

            self.root.after(
                0,
                lambda err=error_text:
                    self.upload_error(err)
            )

    # =========================================================
    # SUCESSO
    # =========================================================

    def upload_success(self, url):

        self.upload_running = False

        self.image_button.config(
            state="normal"
        )

        self.search_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● Imagem enviada para o Google Lens com sucesso",
            fg="#00d084"
        )

        self.current_url = url

        self.show_url(
            url
        )

        self.open_button.config(
            state="normal"
        )

    # =========================================================
    # ERRO
    # =========================================================

    def upload_error(self, error_text):

        self.upload_running = False

        self.image_button.config(
            state="normal"
        )

        self.search_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● Erro ao enviar a imagem para o Google Lens",
            fg="#f85149"
        )

        # =====================================================
        # NÃO MOSTRAR ERRO NO CMD
        # =====================================================

        messagebox.showerror(
            "Erro no Google Lens",
            "Não foi possível enviar a imagem.\n\n"
            "Detalhes:\n"
            + error_text
        )

    # =========================================================
    # SELENIUM NÃO INSTALADO
    # =========================================================

    def selenium_error(self):

        self.upload_running = False

        self.image_button.config(
            state="normal"
        )

        self.search_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● Selenium não está instalado",
            fg="#f85149"
        )

        messagebox.showerror(
            "Selenium",
            "O Selenium não está instalado.\n\n"
            "Execute no CMD:\n\n"
            "pip install selenium"
        )

    # =========================================================
    # ABRIR IMAGEM
    # =========================================================

    def open_selected_image(self):

        if not self.selected_image:
            return

        try:

            os.startfile(
                self.selected_image
            )

        except Exception:

            webbrowser.open(
                self.selected_image
            )

    # =========================================================
    # LIMPAR
    # =========================================================

    def clear(self):

        self.name_entry.delete(
            0,
            tk.END
        )

        self.name_entry.focus()

        self.current_url = ""
        self.selected_image = ""

        self.url_text.config(
            state="normal"
        )

        self.url_text.delete(
            "1.0",
            tk.END
        )

        self.url_text.config(
            state="disabled"
        )

        self.open_button.config(
            state="disabled"
        )

        self.open_image_button.config(
            state="disabled"
        )

        self.image_button.config(
            state="normal"
        )

        self.search_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● Digite um nome ou selecione uma imagem",
            fg="#8b949e"
        )


# =============================================================
# INICIAR
# =============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = GoogleFaceSearch(root)

    root.mainloop()
