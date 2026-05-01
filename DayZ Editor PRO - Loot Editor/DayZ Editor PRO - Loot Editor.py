import xml.etree.ElementTree as ET
from tkinter import *
from tkinter import ttk, filedialog, messagebox

# ====================== DICIONÁRIOS E LISTAS ======================

# 🏗 STORAGE / BASE BUILDING (MMG)
MMG_CATEGORIAS = {
    "tent": "⛺ Tenda", "crate": "📦 Caixa", "supplycrate": "📦 Caixa Supply",
    "army_box": "📦 Caixa Militar", "case": "🧰 Case", "palette": "📦 Storage Pallet",
    "locker": "🔒 Armário", "safe": "🔒 Cofre", "cabinet": "🗄 Armário Blindado",
    "gear_stand": "🧍 Suporte Equipamento", "gun_rack": "🔫 Suporte de Armas",
    "gun_wall": "🔫 Parede de Armas", "fridge": "🧊 Geladeira",
    "toolwagon": "🧰 Carrinho de Ferramentas", "trash": "🗑 Lixeira",
    "grenade_case": "💣 Caixa de Granada", "planter": "🌱 Plantação",
    "greenhouse": "🌱 Estufa", "table": "🪑 Mesa", "shelf": "📚 Prateleira",
    "solo_locker": "🔐 Locker Solo"
}

# 🏍 QUADRICICLOS
POLARIS = ["mbm_polaris500xc", "mbm_polaris500"]

# 🚤 BARCOS
BARCOS = ["boat_01_black", "boat_01_blue", "boat_01_camo", "boat_01_orange"]

# 🚗 VEÍCULOS
VEICULOS = ["civilian_sedan", "offroadhatchback", "offroad_02", "sedan_02", "hatchback_02"]

# 🔧 PEÇAS DE VEÍCULO
PECAS_VEICULO = {
    "door": "🚪 Porta", "hood": "🛠 Capô", "trunk": "📦 Porta-malas",
    "wheel": "🎡 Roda", "radiator": "🌡 Radiador", "sparkplug": "⚡ Vela",
    "battery": "🔋 Bateria", "headlight": "💡 Farol", "panel": "📟 Painel",
    "engine": "⚙ Motor"
}

# 🐾 ANIMAIS
ANIMAIS = {
    "bear": "🐻 Urso", "boar": "🐗 Javali", "deer": "🦌 Veado", "cow": "🐄 Vaca",
    "goat": "🐐 Cabra", "sheep": "🐑 Ovelha", "pig": "🐖 Porco", "chicken": "🐔 Galinha",
    "wolf": "🐺 Lobo", "fox": "🦊 Raposa", "rabbit": "🐰 Coelho",
    "animal_bostaurus": "🐄 Vaca", "animal_canislupus": "🐺 Lobo",
    "animal_caprahircus": "🐐 Cabra", "animal_capreolus": "🦌 Veado",
    "animal_cervuselaphus": "🦌 Cervo", "animal_gallus": "🐔 Galinha",
    "animal_lepus": "🐰 Coelho", "animal_ovisaries": "🐑 Ovelha",
    "animal_rangifer": "🦌 Rena", "animal_sus": "🐖 Porco",
    "animal_ursus": "🐻 Urso", "animal_vulpes": "🦊 Raposa"
}

CATEGORIAS = {
    "weapons": "🔫 Armas", "ammo": "💥 Munição", "magazines": "📦 Carregadores",
    "food": "🍖 Comida", "drinks": "🥤 Bebidas", "clothes": "👕 Roupas",
    "medical": "💊 Remédios", "tools": "🛠 Ferramentas", "vehicles": "🚗 Veículos",
    "explosives": "💣 Explosivos"
}


# ====================== FUNÇÃO DE CATEGORIA ======================
def format_cat(cat: str, name: str) -> str:
    name_lower = name.lower()

    # GHILLIE SYSTEM
    if "ghillieatt" in name_lower:
        if "mossy" in name_lower:    return "🟢 Anexo Ghillie - Floresta"
        if "tan" in name_lower:      return "🟤 Anexo Ghillie - Deserto"
        if "winter" in name_lower:   return "⚪ Anexo Ghillie - Neve"
        if "woodland" in name_lower: return "🌲 Anexo Ghillie - Mata Fechada"
        return "🧥 Anexo Ghillie"

    if "ghilliehood" in name_lower:
        if "mossy" in name_lower:    return "🟢 Capuz Ghillie - Floresta"
        if "tan" in name_lower:      return "🟤 Capuz Ghillie - Deserto"
        if "winter" in name_lower:   return "⚪ Capuz Ghillie - Neve"
        if "woodland" in name_lower: return "🌲 Capuz Ghillie - Mata Fechada"
        return "🧢 Capuz Ghillie"

    if "ghilliesuit" in name_lower:
        if "mossy" in name_lower:    return "🟢 Traje Ghillie - Floresta"
        if "tan" in name_lower:      return "🟤 Traje Ghillie - Deserto"
        if "winter" in name_lower:   return "⚪ Traje Ghillie - Neve"
        if "woodland" in name_lower: return "🌲 Traje Ghillie - Mata Fechada"
        return "🥋 Traje Ghillie"

    if "ghillietop" in name_lower:
        if "mossy" in name_lower:    return "🟢 Parte Superior Ghillie - Floresta"
        if "tan" in name_lower:      return "🟤 Parte Superior Ghillie - Deserto"
        if "winter" in name_lower:   return "⚪ Parte Superior Ghillie - Neve"
        if "woodland" in name_lower: return "🌲 Parte Superior Ghillie - Mata Fechada"
        return "👕 Parte Superior Ghillie"

    if "ghilliebushrag" in name_lower:
        if "mossy" in name_lower:    return "🟢 Bushrag Ghillie - Floresta"
        if "tan" in name_lower:      return "🟤 Bushrag Ghillie - Deserto"
        if "winter" in name_lower:   return "⚪ Bushrag Ghillie - Neve"
        if "woodland" in name_lower: return "🌲 Bushrag Ghillie - Mata Fechada"
        return "🥷 Bushrag Ghillie"

    # Categorias Gerais
    if any(x in name_lower for x in ["key", "dimplekey"]): return "🔑 Chaves"
    if any(x in name_lower for x in ["backpack", "rucksack", "drybag", "huntingbag", "fieldpack", "tortillabag"]): 
        return "🎒 Mochilas"
    if any(x in name_lower for x in ["bag", "pouch"]): return "👝 Bolsas"
    if any(x in name_lower for x in ["ammo", "bullet", "round", "762", "556", "545", "9x19", "9mm", "380", "12ga"]): 
        return "💥 Munição"
    if any(x in name_lower for x in ["ak", "m4", "rifle", "pistol", "shotgun", "smg", "svd", "mosin"]): 
        return "🔫 Armas"
    if any(x in name_lower for x in ["vest", "carrier", "platecarrier", "pressvest"]): 
        return "🛡 Colete"
    if any(x in name_lower for x in ["jacket", "shirt", "hoodie", "coat", "tshirt"]): 
        return "👕 Roupas"
    if "gloves" in name_lower: return "🧤 Luvas"
    if any(x in name_lower for x in ["pants", "trousers"]): return "👖 Calças"
    if any(x in name_lower for x in ["boots", "shoes", "sneakers"]): return "👢 Calçados"

    # MMG
    if "mmg_" in name_lower:
        for key, val in MMG_CATEGORIAS.items():
            if key in name_lower:
                return val

    # Comida, Bebidas, Remédios
    if any(x in name_lower for x in ["steak", "meat", "chicken", "beef", "pork", "mutton", "bakedbeans", "sardines", "tuna", "peaches", "spaghetti", "apple", "pear", "plum", "zucchini", "pumpkin", "potato", "pepper", "rice", "cereal", "chips", "crackers", "candy", "chocolate", "honey", "jam"]):
        return "🍖 Comida"

    if any(x in name_lower for x in ["waterbottle", "canteen", "soda", "cola", "sprite", "kvass", "energy"]):
        return "🥤 Bebidas"

    if any(x in name_lower for x in ["vitamin", "bandage", "saline", "morphine", "tetracycline", "charcoal"]):
        return "💊 Remédios"

    # Veículos e Barcos
    for p in POLARIS:
        if p in name_lower:
            return "🎡 Roda ATV" if "wheel" in name_lower else "🏍 Quadriciclo"

    for b in BARCOS:
        if b in name_lower:
            return "🚤 Barcos"

    for key, val in ANIMAIS.items():
        if key in name_lower:
            return val

    if "heli" in name_lower: return "🚁 Helicóptero"

    for key, val in PECAS_VEICULO.items():
        if key in name_lower:
            return val

    for v in VEICULOS:
        if v in name_lower: return "🚗 Veículos"

    if any(x in name_lower for x in ["sedan", "hatchback", "offroad", "truck", "bus"]):
        return "🚗 Veículos"

    if "grenade" in name_lower:
        return "💣 Explosivos"

    return CATEGORIAS.get(cat, cat.capitalize() if cat else "Outros")


# ====================== APLICAÇÃO ======================
class App:
    def __init__(self, root):
        self.file_path = None
        self.tree_xml = None
        self.data = []
        self.filtered = []

        self.root = root
        self.root.title("DayZ Editor PRO - Loot Editor")
        self.root.geometry("1250x720")
        self.root.state("zoomed")
        self.root.configure(bg="#000")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#111", foreground="white", fieldbackground="#111")
        style.configure("Treeview.Heading", background="#222", foreground="white")

        # Top Bar
        top = Frame(root, bg="#000")
        top.pack(fill=X, pady=8)

        Button(top, text="📂 Abrir XML", bg="#00aa66", fg="black", font=("Arial", 10, "bold"), command=self.load_xml).pack(side=LEFT, padx=5)
        Button(top, text="💾 Salvar XML", bg="#fc054f", fg="black", font=("Arial", 10, "bold"), command=self.save_all).pack(side=LEFT, padx=5)
        Button(top, text="📋 Copiar Nome", bg="#05fafa", fg="black", font=("Arial", 10, "bold"), command=self.copy_selected).pack(side=LEFT, padx=5)

        self.search_var = StringVar()
        Entry(top, textvariable=self.search_var, bg="#ffffff", fg="black", font=("Arial", 12, "bold"), width=50).pack(side=LEFT, padx=15, fill=X, expand=True)

        self.search_var.trace_add("write", self.filter_items)

        self.count_label = Label(top, text="0 itens", bg="#000", fg="#00ff99", font=("Arial", 12, "bold"))
        self.count_label.pack(side=RIGHT, padx=20)

        # Treeview
        frame = Frame(root, bg="#000")
        frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        scroll = Scrollbar(frame)
        scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(frame, columns=("name", "cat", "nominal", "min", "lifetime", "edit"),
                                 show="headings", yscrollcommand=scroll.set)
        scroll.config(command=self.tree.yview)

        self.tree.heading("name", text="Item")
        self.tree.heading("cat", text="Categoria")
        self.tree.heading("nominal", text="Nominal")
        self.tree.heading("min", text="Min")
        self.tree.heading("lifetime", text="Lifetime")
        self.tree.heading("edit", text="Editar")

        self.tree.column("name", width=340)
        self.tree.column("cat", width=240)
        self.tree.column("nominal", width=90, anchor="center")
        self.tree.column("min", width=90, anchor="center")
        self.tree.column("lifetime", width=110, anchor="center")
        self.tree.column("edit", width=100, anchor="center")

        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Button-1>", self.on_click)        

    def load_xml(self):
        path = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
        if not path:
            return

        self.file_path = path
        self.tree_xml = ET.parse(path)
        root = self.tree_xml.getroot()

        self.data.clear()

        for t in root.findall("type"):
            cat_node = t.find("category")
            cat = cat_node.get("name") if cat_node is not None else "outros"

            self.data.append({
                "node": t,
                "name": t.get("name"),
                "cat": cat,
                "nominal": t.findtext("nominal", "0"),
                "min": t.findtext("min", "0"),
                "lifetime": t.findtext("lifetime", "0"),
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
        termo = self.search_var.get().lower().strip()
        if not termo:
            self.filtered = self.data.copy()
        else:
            self.filtered = [i for i in self.data if termo in i["name"].lower() or termo in i["cat"].lower()]
        self.update_table()

    def on_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#6":
            return

        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        name = self.tree.item(row_id)["values"][0]
        item = next((i for i in self.data if i["name"] == name), None)
        if item:
            self.open_editor(item)

    def copy_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um item!")
            return
        nome = self.tree.item(selected[0])["values"][0]
        self.root.clipboard_clear()
        self.root.clipboard_append(nome)
        messagebox.showinfo("Copiado", f"Nome copiado:\n{nome}")

    # ==================== JANELA DE EDIÇÃO ====================
    def open_editor(self, item):
        win = Toplevel(self.root)
        win.title(f"Editando: {item['name']}")
        win.geometry("760x600")
        win.configure(bg="#111")
        win.resizable(True, True)

        node = item["node"]
        entries = {}

        def create_field(label_text, tag_name, default="0"):
            frame = Frame(win, bg="#111")
            frame.pack(fill=X, padx=25, pady=7)

            Label(frame, text=label_text, bg="#111", fg="#ffffff", width=20, anchor="w", font=("Arial", 10)).pack(side=LEFT)
            entry = Entry(frame, bg="#00ff88", fg="#000000", font=("Consolas", 11, "bold"))
            entry.insert(0, default)
            entry.pack(side=LEFT, padx=10, fill=X, expand=True)
            entries[tag_name] = entry
            return entry

        # Campos principais
        nominal   = create_field("Nominal",      "nominal",   node.findtext("nominal", "0"))
        lifetime  = create_field("Lifetime",     "lifetime",  node.findtext("lifetime", "0"))
        restock   = create_field("Restock",      "restock",   node.findtext("restock", "0"))
        min_v     = create_field("Min",          "min",       node.findtext("min", "0"))
        quantmin  = create_field("Quant Min",    "quantmin",  node.findtext("quantmin", "0"))
        quantmax  = create_field("Quant Max",    "quantmax",  node.findtext("quantmax", "0"))
        cost      = create_field("Cost",         "cost",      node.findtext("cost", "0"))

        # Flags
        flags = node.find("flags")
        create_field("Count in Cargo",   "count_in_cargo",   flags.get("count_in_cargo", "0") if flags else "0")
        create_field("Count in Hoarder", "count_in_hoarder", flags.get("count_in_hoarder", "0") if flags else "0")
        create_field("Count in Map",     "count_in_map",     flags.get("count_in_map", "0") if flags else "0")
        create_field("Count in Player",  "count_in_player",  flags.get("count_in_player", "0") if flags else "0")

        # Category e Usage
        cat_node = node.find("category")
        cat_val = cat_node.get("name") if cat_node is not None else ""
        cat_field = create_field("Category", "category", cat_val)

        usages = [u.get("name") for u in node.findall("usage")]
        usage_field = create_field("Usage (separado por vírgula)", "usage", ",".join(usages))

        # ==================== SALVAR ====================
        def save_changes():
            def set_or_create(tag, value):
                el = node.find(tag)
                if el is None:
                    el = ET.SubElement(node, tag)
                el.text = str(value).strip()

            set_or_create("nominal", nominal.get())
            set_or_create("lifetime", lifetime.get())
            set_or_create("restock", restock.get())
            set_or_create("min", min_v.get())
            set_or_create("quantmin", quantmin.get())
            set_or_create("quantmax", quantmax.get())
            set_or_create("cost", cost.get())

            # Flags
            flags_node = node.find("flags")
            if flags_node is None:
                flags_node = ET.SubElement(node, "flags")
            flags_node.set("count_in_cargo", entries["count_in_cargo"].get())
            flags_node.set("count_in_hoarder", entries["count_in_hoarder"].get())
            flags_node.set("count_in_map", entries["count_in_map"].get())
            flags_node.set("count_in_player", entries["count_in_player"].get())

            # Category
            cat_node = node.find("category")
            if cat_node is None:
                cat_node = ET.SubElement(node, "category")
            cat_node.set("name", cat_field.get().strip())

            # Usage
            for u in node.findall("usage"):
                node.remove(u)
            for u_name in [x.strip() for x in usage_field.get().split(",") if x.strip()]:
                ET.SubElement(node, "usage").set("name", u_name)

            # Atualiza dados na memória
            item["nominal"] = nominal.get().strip()
            item["min"] = min_v.get().strip()
            item["lifetime"] = lifetime.get().strip()

            # Salva arquivo
            if self.tree_xml and self.file_path:
                self.tree_xml.write(self.file_path, encoding="utf-8", xml_declaration=True)

            self.update_table()

            messagebox.showinfo("Sucesso", f"✅ {item['name']} salvo!\nLifetime atualizado para: {lifetime.get()}")
            win.destroy()

        # Botões
        btn_frame = Frame(win, bg="#111")
        btn_frame.pack(pady=25)

        Button(btn_frame, text="💾 Salvar Alterações", bg="#00aa66", fg="black",
               font=("Arial", 11, "bold"), width=22, command=save_changes).pack(side=LEFT, padx=12)
        Button(btn_frame, text="Cancelar", bg="#555", fg="white",
               font=("Arial", 11, "bold"), width=15, command=win.destroy).pack(side=LEFT, padx=12)

    def save_all(self):
        if not self.tree_xml or not self.file_path:
            messagebox.showwarning("Aviso", "Nenhum arquivo aberto!")
            return
        self.tree_xml.write(self.file_path, encoding="utf-8", xml_declaration=True)
        messagebox.showinfo("Salvo", "Arquivo XML salvo com sucesso!")


# ====================== EXECUÇÃO ======================
if __name__ == "__main__":
    root = Tk()
    app = App(root)
    root.mainloop()
