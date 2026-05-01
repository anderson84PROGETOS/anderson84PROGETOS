import xml.etree.ElementTree as ET
from tkinter import *
from tkinter import ttk, filedialog, messagebox

# 🏗 STORAGE / BASE BUILDING (MMG)
MMG_CATEGORIAS = {
    "tent": "⛺ Tenda",
    "crate": "📦 Caixa",
    "supplycrate": "📦 Caixa Supply",
    "army_box": "📦 Caixa Militar",
    "case": "🧰 Case",
    "palette": "📦 Storage Pallet",

    "locker": "🔒 Armário",
    "safe": "🔒 Cofre",
    "cabinet": "🗄 Armário Blindado",

    "gear_stand": "🧍 Suporte Equipamento",
    "gun_rack": "🔫 Suporte de Armas",
    "gun_wall": "🔫 Parede de Armas",

    "fridge": "🧊 Geladeira",
    "toolwagon": "🧰 Carrinho de Ferramentas",

    "trash": "🗑 Lixeira",
    "grenade_case": "💣 Caixa de Granada",

    "planter": "🌱 Plantação",
    "greenhouse": "🌱 Estufa",

    "table": "🪑 Mesa",
    "shelf": "📚 Prateleira",

    "solo_locker": "🔐 Locker Solo"
}

# 🏍 QUADRICICLOS (POLARIS / ATV)
POLARIS = [
    "mbm_polaris500xc",
    "mbm_polaris500"
]


# 🚤 BARCOS
BARCOS = [
    "boat_01_black",
    "boat_01_blue",
    "boat_01_camo",
    "boat_01_orange"
]

# 🚗 VEÍCULOS DAYZ
VEICULOS = [
    "civilian_sedan",
    "offroadhatchback",
    "offroad_02",
    "sedan_02",
    "hatchback_02"
]

# 🔧 PEÇAS DE VEÍCULOS
PECAS_VEICULO = {
    "door": "🚪 Porta",
    "hood": "🛠 Capô",
    "trunk": "📦 Porta-malas",
    "wheel": "🎡 Roda",
    "radiator": "🌡 Radiador",
    "sparkplug": "⚡ Vela",
    "battery": "🔋 Bateria",
    "headlight": "💡 Farol",
    "panel": "📟 Painel",
    "engine": "⚙ Motor"
}

# 📦 categorias com ícones
CATEGORIAS = {
    "weapons": "🔫 Armas",
    "ammo": "💥 Munição",
    "magazines": "📦 Carregadores",
    "food": "🍖 Comida",
    "drinks": "🥤 Bebidas",
    "clothes": "👕 Roupas",
    "medical": "💊 Remédios",
    "tools": "🛠 Ferramentas",
    "vehicles": "🚗 Veículos",
    "explosives": "💣 Explosivos"
}

# 🐾 animais
ANIMAIS = {
    "bear": "🐻 Urso",
    "boar": "🐗 Javali",
    "deer": "🦌 Veado",
    "cow": "🐄 Vaca",
    "goat": "🐐 Cabra",
    "sheep": "🐑 Ovelha",
    "pig": "🐖 Porco",
    "chicken": "🐔 Galinha",
    "wolf": "🐺 Lobo",
    "fox": "🦊 Raposa",
    "rabbit": "🐰 Coelho",

    "animal_bostaurus": "🐄 Vaca",
    "animal_canislupus": "🐺 Lobo",
    "animal_caprahircus": "🐐 Cabra",
    "animal_capreolus": "🦌 Veado",
    "animal_cervuselaphus": "🦌 Cervo",
    "animal_gallus": "🐔 Galinha",
    "animal_lepus": "🐰 Coelho",
    "animal_ovisaries": "🐑 Ovelha",
    "animal_rangifer": "🦌 Rena",
    "animal_sus": "🐖 Porco",
    "animal_ursus": "🐻 Urso",
    "animal_vulpes": "🦊 Raposa"
}

# 🔥 categorização
def format_cat(cat, name):
    name = name.lower()

    # 🔑 chaves (colocar acima)
    if any(x in name for x in ["key", "dimplekey"]):
        return "🔑 Chaves"

    # 🎒 mochilas (corrigido)
    if any(x in name for x in [
        "backpack", "rucksack", "drybag", "huntingbag", "fieldpack", "tortillabag"
    ]):
        return "🎒 Mochilas"

    # 👝 bolsas
    if any(x in name for x in [
        "bag", "pouch", "case"
    ]):
        return "👝 Bolsas"
       

    # 💥 munição
    if any(x in name for x in [
        "ammo", "bullet", "round", "762", "556", "545", "9x19", "9mm", "380", "12ga"
    ]):
        return "💥 Munição"


    # 🔫 armas
    if any(x in name for x in [
        "ak", "m4", "rifle", "pistol", "shotgun", "smg", "svd", "mosin"
    ]):
        return "🔫 Armas"


    # 🛡 coletes
    if any(x in name for x in [
        "vest", "carrier", "platecarrier", "pressvest"
    ]):
        return "🛡 Colete"


    # 👕 roupas (geral)
    if any(x in name for x in [
        "jacket", "shirt", "hoodie", "coat", "tshirt"
    ]):
        return "👕 Roupas"


    # 🧤 luvas
    if any(x in name for x in [
        "gloves"
    ]):
        return "🧤 Luvas"


    # 👖 calças
    if any(x in name for x in [
        "pants", "trousers"
    ]):
        return "👖 Calças"


    # 👢 sapatos / botas
    if any(x in name for x in [
        "boots", "shoes", "sneakers"
    ]):
        return "👢 Calçados"

    # 🏗 MMG STORAGE / BASE BUILDING
    if "mmg_" in name:
        for key, val in MMG_CATEGORIAS.items():
            if key in name:
                return val

    # 🍖 comidas (completo)
    if any(x in name for x in [
        # carnes
        "steak", "meat", "chicken", "beef", "pork", "mutton",

        # enlatados
        "bakedbeans", "sardines", "tuna", "peaches", "spaghetti",

        # frutas
        "apple", "pear", "plum",

        # vegetais
        "zucchini", "pumpkin", "potato", "pepper",

        # comida geral
        "rice", "cereal", "powderedmilk",

        # snacks
        "chips", "crackers", "candy", "chocolate",

        # outros
        "honey", "jam"
    ]):
        return "🍖 Comida"

    # 🥤 bebidas (completo)
    if any(x in name for x in [
        "waterbottle",
        "canteen",
        "soda",
        "cola",
        "spite",
        "kvass",
        "energy"
    ]):
        return "🥤 Bebidas"

    # 💊 sistema médico inteligente
    if any(x in name for x in ["vitamin", "bandage", "saline", "morphine", "tetracycline", "charcoal"]):
        return "💊 Remédios"

    # 🏍 QUADRICICLO (ATV)
    for p in POLARIS:
        if p in name:
            if "wheel" in name:
                return "🎡 Roda ATV"
            return "🏍 Quadriciclo"

    # 🚤 BARCOS (antes de veículos!)
    for b in BARCOS:
        if b in name:
            return "🚤 Barcos"

    for key, val in ANIMAIS.items():
        if key in name:
            return val

    if "heli" in name:
        return "🚁 Helicóptero"

    # 🔧 peças primeiro
    for key, val in PECAS_VEICULO.items():
        if key in name:
            return val

    # 🚗 veículos
    for v in VEICULOS:
        if v in name:
            return "🚗 Veículos"

    if any(x in name for x in ["sedan", "hatchback", "offroad", "truck", "bus"]):
        return "🚗 Veículos"

    if any(x in name for x in ["ak", "m4", "rifle", "pistol"]):
        return "🔫 Armas"

    if "grenade" in name:
        return "💣 Explosivos"

    return CATEGORIAS.get(cat, cat)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("DayZ Editor PRO")
        self.root.geometry("1200x650")
        self.root.state("zoomed")
        self.root.configure(bg="#000")

        style = ttk.Style()
        style.theme_use("default")

        style.configure("Treeview",
                        background="#111",
                        foreground="white",
                        fieldbackground="#111")

        style.configure("Treeview.Heading",
                        background="#222",
                        foreground="white")

        # 🔝 TOPO
        top = Frame(root, bg="#000")
        top.pack(fill=X)

        Button(top, text="Abrir XML",
               bg="#00aa66", fg="black",
               command=self.load_xml).pack(side=LEFT, padx=5, pady=5)

        Button(top, text="Salvar XML",
               bg="#444", fg="white",
               command=self.save_xml).pack(side=LEFT, padx=5)

        # ✅ BOTÃO COPIAR (AGORA NO LUGAR CERTO)
        Button(top, text="📋 Copiar Item",
               bg="#0088ff", fg="white",
               command=self.copy_selected).pack(side=LEFT, padx=5)

        self.search_var = StringVar()

        Entry(top,
              textvariable=self.search_var,
              bg="#111",
              fg="white",
              insertbackground="white").pack(side=LEFT, fill=X, expand=True, padx=10)

        self.search_var.trace_add("write", self.filter_items)

        self.count_label = Label(top, text="0 itens", bg="#000", fg="white")
        self.count_label.pack(side=RIGHT, padx=10)

        # 📋 TABELA
        frame = Frame(root, bg="#000")
        frame.pack(fill=BOTH, expand=True)

        scroll = Scrollbar(frame)
        scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(frame,
                                columns=("name", "cat", "nominal", "min", "lifetime", "edit"),
                                show="headings",
                                yscrollcommand=scroll.set)

        scroll.config(command=self.tree.yview)

        self.tree.heading("name", text="Item")
        self.tree.heading("cat", text="Categoria")
        self.tree.heading("nominal", text="Nominal")
        self.tree.heading("min", text="Min")
        self.tree.heading("lifetime", text="Lifetime")
        self.tree.heading("edit", text="Ação")

        self.tree.column("name", width=300)
        self.tree.column("cat", width=220)
        self.tree.column("nominal", width=100, anchor="center")
        self.tree.column("min", width=100, anchor="center")
        self.tree.column("lifetime", width=120, anchor="center")
        self.tree.column("edit", width=100, anchor="center")

        self.tree.pack(fill=BOTH, expand=True)

        self.tree.bind("<Button-1>", self.on_click)

        self.data = []
        self.filtered = []
        self.tree_xml = None

    # 📋 copiar nome
    def copy_selected(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Aviso", "Selecione um item primeiro!")
            return

        item = self.tree.item(selected[0])
        nome = item["values"][0]

        self.root.clipboard_clear()
        self.root.clipboard_append(nome)
        self.root.update()

        messagebox.showinfo("Copiado", f"Nome copiado:\n{nome}")

    def load_xml(self):
        path = filedialog.askopenfilename(filetypes=[("XML", "*.xml")])
        if not path:
            return

        self.tree_xml = ET.parse(path)
        root = self.tree_xml.getroot()

        self.data.clear()

        for t in root.findall("type"):
            cat = t.find("category")
            cat = cat.get("name") if cat is not None else "outros"

            self.data.append({
                "node": t,
                "name": t.get("name"),
                "cat": cat,
                "nominal": t.findtext("nominal", "0"),
                "min": t.findtext("min", "0"),
                "max": t.findtext("max", "0"),
                "lifetime": t.findtext("lifetime", "0"),
                "restock": t.findtext("restock", "0"),
            })

        self.filtered = self.data.copy()
        self.update_table()

    def update_table(self):
        self.tree.delete(*self.tree.get_children())

        for i, item in enumerate(self.filtered):
            tag = "even" if i % 2 == 0 else "odd"

            self.tree.insert("", "end",
                values=(item["name"],
                        format_cat(item["cat"], item["name"]),
                        item["nominal"],
                        item["min"],
                        item["lifetime"],
                        "🟩 Editar 🟩"),
                tags=(tag, "edit_btn"))

        self.tree.tag_configure("even", background="#111")
        self.tree.tag_configure("odd", background="#1a1a1a")
        self.tree.tag_configure("edit_btn", foreground="#00ff99")

        self.count_label.config(text=f"{len(self.filtered)} itens")

    def filter_items(self, *args):
        termo = self.search_var.get().lower()

        self.filtered = [
            i for i in self.data
            if termo in i["name"].lower() or termo in i["cat"].lower()
        ]

        self.update_table()

    def on_click(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not row:
            return

        if col == "#6":
            name = self.tree.item(row)["values"][0]
            item = next(i for i in self.data if i["name"] == name)
            self.open_editor(item)

    def open_editor(self, item):
        win = Toplevel(self.root)
        win.title(item["name"])
        win.geometry("400x420")
        win.configure(bg="#111")

        def field(label, value):
            Label(win, text=label, bg="#111", fg="white").pack()
            e = Entry(win, bg="#222", fg="white")
            e.insert(0, value)
            e.pack(fill=X, padx=20, pady=3)
            return e

        nominal = field("Nominal", item["nominal"])
        min_v = field("Min", item["min"])
        max_v = field("Max", item["max"])
        lifetime = field("Lifetime", item["lifetime"])
        restock = field("Restock", item["restock"])

        def salvar():
            if item["node"].find("nominal") is not None:
                item["node"].find("nominal").text = nominal.get()

            if item["node"].find("min") is not None:
                item["node"].find("min").text = min_v.get()

            if item["node"].find("max") is not None:
                item["node"].find("max").text = max_v.get()

            if item["node"].find("lifetime") is not None:
                item["node"].find("lifetime").text = lifetime.get()

            if item["node"].find("restock") is not None:
                item["node"].find("restock").text = restock.get()

            self.update_table()
            messagebox.showinfo("Sucesso", "Item atualizado com sucesso!")
            win.destroy()

        Button(win, text="Salvar", bg="#00aa66", fg="black", command=salvar).pack(pady=10)
        Button(win, text="Cancelar", bg="#444", fg="white", command=win.destroy).pack()

    def save_xml(self):
        if not self.tree_xml:
            return

        path = filedialog.asksaveasfilename(defaultextension=".xml")
        if not path:
            return

        self.tree_xml.write(path, encoding="utf-8", xml_declaration=True)
        messagebox.showinfo("Sucesso", "XML salvo com sucesso!")


root = Tk()
app = App(root)
root.mainloop()
