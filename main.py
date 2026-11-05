import os
import shutil
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pymupdf as fitz
from PIL import Image, ImageTk

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
        ttk.Button(actions, text="Visualizar / Imprimir", command=self.print_current).pack(side="left")
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
            if messagebox.askyesno(
                "Código gerado",
                f"Código: {self.current['barcode']}\n\nDeseja visualizar e imprimir a etiqueta agora?",
                icon="question",
            ):
                self.open_print_window()
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

    def open_print_window(self):
        if not self.current:
            messagebox.showinfo("Impressão", "Gere ou selecione um código no histórico.")
            return

        mode = "a4" if self.mode_var.get() == "A4" else "termica"
        pdf_path = None
        try:
            pdf_path = create_label_pdf(self.current, mode)
            with fitz.open(pdf_path) as document:
                page = document[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
                preview = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            window = tk.Toplevel(self)
            window.title("Pré-visualização e impressão")
            window.geometry("920x760")
            window.minsize(700, 560)
            window.transient(self)

            top = ttk.Frame(window, padding=12)
            top.pack(fill="x")
            ttk.Label(top, text=f"Produto: {self.current['product']}   |   Código: {self.current['barcode']}",
                      font=("Segoe UI", 10, "bold")).pack(anchor="w")
            ttk.Label(top, text="Confira a etiqueta e selecione a impressora.").pack(anchor="w", pady=(3, 8))

            printer_row = ttk.Frame(top)
            printer_row.pack(fill="x")
            ttk.Label(printer_row, text="Impressora:").pack(side="left")
            printer_var = tk.StringVar()
            printer_combo = ttk.Combobox(printer_row, textvariable=printer_var, state="readonly", width=55)
            printer_combo.pack(side="left", padx=8, fill="x", expand=True)

            try:
                import win32print
                flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                printer_names = sorted({item[2] for item in win32print.EnumPrinters(flags)})
                default_printer = win32print.GetDefaultPrinter()
            except Exception as error:
                printer_names = []
                default_printer = ""
                messagebox.showerror("Impressoras", f"Não foi possível listar as impressoras do Windows.\n{error}", parent=window)

            printer_combo["values"] = printer_names
            if default_printer in printer_names:
                printer_var.set(default_printer)
            elif printer_names:
                printer_var.set(printer_names[0])

            preview_area = ttk.Frame(window, padding=(12, 0, 12, 8))
            preview_area.pack(fill="both", expand=True)
            preview.thumbnail((820, 570), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
            preview_label = ttk.Label(preview_area, image=photo, anchor="center")
            preview_label.image = photo
            preview_label.pack(expand=True)

            if mode == "termica":
                note = "Na impressora térmica, deixe configurado no driver o mesmo tamanho da etiqueta selecionada."
            else:
                note = "A folha A4 será enviada como uma página, com várias cópias da etiqueta."
            ttk.Label(window, text=note, wraplength=850).pack(padx=12, pady=(0, 8))

            buttons = ttk.Frame(window, padding=12)
            buttons.pack(fill="x")

            def do_print():
                selected = printer_var.get().strip()
                if not selected:
                    messagebox.showwarning("Impressora", "Selecione uma impressora instalada.", parent=window)
                    return
                try:
                    self.send_pdf_to_printer(pdf_path, selected)
                    messagebox.showinfo("Impressão", f"Trabalho enviado para:\n{selected}", parent=window)
                    window.destroy()
                except Exception as error:
                    messagebox.showerror("Erro de impressão", str(error), parent=window)

            ttk.Button(buttons, text="Cancelar", command=window.destroy).pack(side="right")
            ttk.Button(buttons, text="Imprimir", command=do_print).pack(side="right", padx=8)
            if not printer_names:
                ttk.Label(buttons, text="Nenhuma impressora encontrada.").pack(side="left")
        except Exception as error:
            messagebox.showerror("Pré-visualização", str(error), parent=self)
        finally:
            if pdf_path and os.path.exists(pdf_path):
                # O arquivo fica disponível enquanto a janela estiver aberta.
                pass

    @staticmethod
    def send_pdf_to_printer(pdf_path, printer_name):
        import win32con
        import win32ui
        from PIL import ImageWin

        with fitz.open(pdf_path) as document:
            page = document[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        dc = win32ui.CreateDC()
        dc.CreatePrinterDC(printer_name)
        try:
            printable_width = dc.GetDeviceCaps(win32con.HORZRES)
            printable_height = dc.GetDeviceCaps(win32con.VERTRES)
            fit_scale = min(printable_width / image.width, printable_height / image.height)
            target_size = (
                max(1, int(image.width * fit_scale)),
                max(1, int(image.height * fit_scale)),
            )
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            x = max(0, (printable_width - image.width) // 2)
            y = max(0, (printable_height - image.height) // 2)
            dib = ImageWin.Dib(image)
            dc.StartDoc("Gerenciador de Etiquetas")
            dc.StartPage()
            dib.draw(dc.GetHandleOutput(), (x, y, x + image.width, y + image.height))
            dc.EndPage()
            dc.EndDoc()
        except Exception:
            try:
                dc.AbortDoc()
            except Exception:
                pass
            raise
        finally:
            dc.DeleteDC()

    def print_current(self):
        self.open_print_window()

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
