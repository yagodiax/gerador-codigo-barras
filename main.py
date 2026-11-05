"""Interface inicial do Gerador de Código de Barras."""
import tkinter as tk
from tkinter import ttk, messagebox
import database

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Código de Barras")
        self.geometry("850x570")
        self.minsize(700, 450)
        database.init_db()
        self.build()
        self.refresh()

    def build(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Gerador de Código de Barras",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 14))
        form = ttk.LabelFrame(root, text="Cadastro de produto", padding=12)
        form.pack(fill="x")
        ttk.Label(form, text="Nome do produto").grid(row=0, column=0, sticky="w")
        self.name = tk.StringVar()
        ttk.Entry(form, textvariable=self.name, width=35).grid(row=1, column=0, padx=(0,12), sticky="ew")
        ttk.Label(form, text="Modelo de etiqueta").grid(row=0, column=1, sticky="w")
        self.template = ttk.Combobox(form, state="readonly", width=30)
        self.template.grid(row=1, column=1, padx=(0,12), sticky="ew")
        ttk.Button(form, text="Salvar produto", command=self.save).grid(row=1, column=2)
        form.columnconfigure(0, weight=1)
        self.template_rows = []
        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=12)
        ttk.Label(actions, text="Produtos cadastrados").pack(side="left")
        ttk.Button(actions, text="Gerar próximo código", command=self.generate).pack(side="right")
        self.product = ttk.Combobox(root, state="readonly")
        self.product.pack(fill="x")
        self.product_rows = []
        ttk.Label(root, text="Histórico recente", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(18,6))
        columns = ("product", "code", "template", "date")
        self.table = ttk.Treeview(root, columns=columns, show="headings", height=12)
        for col, title, width in [("product","Produto",190),("code","Código",190),("template","Etiqueta",190),("date","Data",150)]:
            self.table.heading(col, text=title)
            self.table.column(col, width=width)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.template_rows = database.templates()
        self.template["values"] = [f"{t['name']} ({t['width_mm']:g} x {t['height_mm']:g} mm)" for t in self.template_rows]
        if self.template_rows and not self.template.get():
            self.template.current(0)
        self.product_rows = database.products()
        self.product["values"] = [p["name"] for p in self.product_rows]
        if self.product_rows and self.product.current() < 0:
            self.product.current(0)
        for item in self.table.get_children():
            self.table.delete(item)
        for label in database.recent_labels():
            self.table.insert("", "end", values=(label["product_name"], label["barcode_value"], label["template_name"], label["created_at"]))

    def save(self):
        try:
            if not self.template_rows:
                raise ValueError("Nenhum modelo de etiqueta disponível.")
            database.save_product(self.name.get(), self.template_rows[self.template.current()]["id"])
            self.name.set("")
            self.refresh()
            messagebox.showinfo("Sucesso", "Produto salvo.")
        except Exception as exc:
            messagebox.showerror("Não foi possível salvar", str(exc))

    def generate(self):
        try:
            index = self.product.current()
            if index < 0:
                raise ValueError("Cadastre ou selecione um produto.")
            code = database.generate_label(self.product_rows[index]["id"])
            self.refresh()
            messagebox.showinfo("Código gerado", code)
        except Exception as exc:
            messagebox.showerror("Não foi possível gerar", str(exc))

if __name__ == "__main__":
    App().mainloop()
