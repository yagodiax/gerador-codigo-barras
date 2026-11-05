import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from database import templates, products, create_product, next_label, history
from label_pdf import create_label_pdf


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Etiquetas")
        self.geometry("900x610")
        self.minsize(780, 500)
        self.current = None
        self.ts = templates()
        self.tm = {item["name"]: item for item in self.ts}
        self.build()
        self.refresh()

    def build(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        head = ttk.Frame(self, padding=16)
        head.pack(fill="x")
        ttk.Label(head, text="GERENCIADOR DE ETIQUETAS", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(head, text="Identificação e impressão de produtos").pack(anchor="w")

        frame = ttk.LabelFrame(self, text="Geração", padding=12)
        frame.pack(fill="x", padx=16, pady=6)
        ttk.Label(frame, text="Produto").grid(row=0, column=0, sticky="w")
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(frame, textvariable=self.product_var, width=32)
        self.product_combo.grid(row=1, column=0, padx=(0, 10), sticky="ew")
        self.product_combo.bind("<<ComboboxSelected>>", self.select_product)

        ttk.Label(frame, text="Dimensão da etiqueta").grid(row=0, column=1, sticky="w")
        self.template_var = tk.StringVar(value=self.ts[0]["name"])
        ttk.Combobox(frame, textvariable=self.template_var, values=list(self.tm), state="readonly", width=18).grid(
            row=1, column=1, padx=(0, 10)
        )

        ttk.Label(frame, text="Formato").grid(row=0, column=2, sticky="w")
        self.mode_var = tk.StringVar(value="Térmica")
        ttk.Combobox(frame, textvariable=self.mode_var, values=["Térmica", "A4"], state="readonly", width=12).grid(
            row=1, column=2, padx=(0, 10)
        )
        ttk.Button(frame, text="Gerar próximo código", command=self.generate).grid(row=1, column=3)
        frame.columnconfigure(0, weight=1)

        result = ttk.LabelFrame(self, text="Código gerado", padding=12)
        result.pack(fill="x", padx=16, pady=6)
        self.code_var = tk.StringVar(value="Nenhum código gerado.")
        ttk.Label(result, textvariable=self.code_var, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        actions = ttk.Frame(result)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Imprimir", command=self.print_current).pack(side="left")
        ttk.Button(actions, text="Salvar PDF", command=self.save_pdf).pack(side="left", padx=8)

        history_frame = ttk.LabelFrame(self, text="Histórico recente", padding=8)
        history_frame.pack(fill="both", expand=True, padx=16, pady=(6, 16))
        self.table = ttk.Treeview(history_frame, columns=("product", "code", "template", "date"), show="headings")
        for column, title, width in [
            ("product", "Produto", 180), ("code", "Código", 230),
            ("template", "Etiqueta", 120), ("date", "Data", 170)
        ]:
            self.table.heading(column, text=title)
            self.table.column(column, width=width, anchor="w")
        self.table.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", self.select_history)

    def refresh(self):
        self.product_combo["values"] = [item["name"] for item in products()]
        for item in self.table.get_children():
            self.table.delete(item)
        for row in history():
            self.table.insert("", "end", values=(row["product"], row["barcode"], row["template_name"], row["created_at"]))

    def select_product(self, event=None):
        selected = self.product_var.get().casefold()
        for product in products():
            if product["name"].casefold() == selected and product["template_id"]:
                for template in self.ts:
                    if template["id"] == product["template_id"]:
                        self.template_var.set(template["name"])
                        return

    def generate(self):
        name = self.product_var.get().strip()
        template = self.tm.get(self.template_var.get())
        if not name or not template:
            messagebox.showwarning("Dados obrigatórios", "Informe o produto e a dimensão.")
            return
        try:
            product_id = create_product(name, template["id"])
            self.current = next_label(product_id, template["id"])
            self.code_var.set(self.current["barcode"])
            self.refresh()
            answer = messagebox.askyesno(
                "Código gerado",
                f"Código: {self.current['barcode']}\n\nDeseja abrir a etiqueta para imprimir agora?",
                icon="question",
            )
            if answer:
                self.open_pdf_for_print()
        except Exception as error:
            messagebox.showerror("Erro", str(error))

    def select_history(self, event=None):
        selection = self.table.selection()
        if not selection:
            return
        values = self.table.item(selection[0], "values")
        code = values[1]
        for row in history(1000):
            if row["barcode"] == code:
                template = next((item for item in self.ts if item["name"] == row["template_name"]), None)
                if template:
                    self.current = {"barcode": row["barcode"], "product": row["product"], "template": template}
                    self.code_var.set(row["barcode"])
                return

    def open_pdf_for_print(self):
        if not self.current:
            messagebox.showinfo("Impressão", "Gere ou selecione um código no histórico.")
            return
        try:
            pdf_path = create_label_pdf(self.current, "a4" if self.mode_var.get() == "A4" else "termica")
            os.startfile(pdf_path)
        except Exception as error:
            messagebox.showerror("Impressão", str(error))

    def print_current(self):
        self.open_pdf_for_print()

    def save_pdf(self):
        if not self.current:
            messagebox.showinfo("PDF", "Gere ou selecione um código primeiro.")
            return
        destination = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=self.current["barcode"] + ".pdf",
        )
        if not destination:
            return
        try:
            shutil.copyfile(
                create_label_pdf(self.current, "a4" if self.mode_var.get() == "A4" else "termica"),
                destination,
            )
            messagebox.showinfo("PDF", "Arquivo salvo.")
        except Exception as error:
            messagebox.showerror("PDF", str(error))


if __name__ == "__main__":
    App().mainloop()
