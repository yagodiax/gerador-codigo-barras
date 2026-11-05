import os, shutil, tkinter as tk
from tkinter import ttk,messagebox,filedialog
from database import templates,products,create_product,next_label,history
from label_pdf import create_label_pdf
class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title("Gerenciador de Etiquetas"); self.geometry("900x610"); self.minsize(780,500); self.current=None
  self.ts=templates(); self.tm={t["name"]:t for t in self.ts}; self.build(); self.refresh()
 def build(self):
  s=ttk.Style(self)
  try:s.theme_use("vista")
  except tk.TclError:pass
  head=ttk.Frame(self,padding=16); head.pack(fill="x")
  ttk.Label(head,text="GERENCIADOR DE ETIQUETAS",font=("Segoe UI",17,"bold")).pack(anchor="w")
  ttk.Label(head,text="Identificação e impressão de produtos").pack(anchor="w")
  f=ttk.LabelFrame(self,text="Geração",padding=12); f.pack(fill="x",padx=16,pady=6)
  ttk.Label(f,text="Produto").grid(row=0,column=0,sticky="w"); self.pv=tk.StringVar()
  self.pc=ttk.Combobox(f,textvariable=self.pv,width=32); self.pc.grid(row=1,column=0,padx=(0,10),sticky="ew"); self.pc.bind("<<ComboboxSelected>>",self.select_product)
  ttk.Label(f,text="Dimensão da etiqueta").grid(row=0,column=1,sticky="w"); self.tv=tk.StringVar(value=self.ts[0]["name"])
  ttk.Combobox(f,textvariable=self.tv,values=list(self.tm),state="readonly",width=18).grid(row=1,column=1,padx=(0,10))
  ttk.Label(f,text="Impressão").grid(row=0,column=2,sticky="w"); self.mv=tk.StringVar(value="Térmica")
  ttk.Combobox(f,textvariable=self.mv,values=["Térmica","A4"],state="readonly",width=12).grid(row=1,column=2,padx=(0,10))
  ttk.Button(f,text="Gerar próximo código",command=self.generate).grid(row=1,column=3); f.columnconfigure(0,weight=1)
  r=ttk.LabelFrame(self,text="Código gerado",padding=12); r.pack(fill="x",padx=16,pady=6)
  self.cv=tk.StringVar(value="Nenhum código gerado."); ttk.Label(r,textvariable=self.cv,font=("Segoe UI",15,"bold")).pack(anchor="w")
  a=ttk.Frame(r); a.pack(fill="x",pady=(8,0)); ttk.Button(a,text="Imprimir",command=self.print_current).pack(side="left"); ttk.Button(a,text="Salvar PDF",command=self.save_pdf).pack(side="left",padx=8)
  h=ttk.LabelFrame(self,text="Histórico recente",padding=8); h.pack(fill="both",expand=True,padx=16,pady=(6,16))
  self.table=ttk.Treeview(h,columns=("p","c","t","d"),show="headings")
  for col,title,width in [("p","Produto",180),("c","Código",230),("t","Etiqueta",120),("d","Data",170)]:self.table.heading(col,text=title); self.table.column(col,width=width,anchor="w")
  self.table.pack(fill="both",expand=True); self.table.bind("<<TreeviewSelect>>",self.select_history)
 def refresh(self):
  self.pc["values"]=[p["name"] for p in products()]
  for i in self.table.get_children():self.table.delete(i)
  for row in history():self.table.insert("","end",values=(row["product"],row["barcode"],row["template_name"],row["created_at"]))
 def select_product(self,event=None):
  name=self.pv.get().casefold()
  for p in products():
   if p["name"].casefold()==name and p["template_id"]:
    for t in self.ts:
     if t["id"]==p["template_id"]:self.tv.set(t["name"])
 def generate(self):
  name=self.pv.get().strip(); t=self.tm.get(self.tv.get())
  if not name or not t:messagebox.showwarning("Dados obrigatórios","Informe produto e dimensão."); return
  try:
   pid=create_product(name,t["id"]); self.current=next_label(pid,t["id"]); self.cv.set(self.current["barcode"]); self.refresh(); self.print_current()
  except Exception as e:messagebox.showerror("Erro",str(e))
 def select_history(self,event=None):
  sel=self.table.selection()
  if not sel:return
  vals=self.table.item(sel[0],"values"); code=vals[1]
  # Histórico selecionado: permite localizar e reimprimir sem gerar outro número.
  for row in history(1000):
   if row["barcode"]==code:
    prod=next((p for p in products() if p["name"]==row["product"]),None)
    if prod:
     t=next((x for x in self.ts if x["name"]==row["template_name"]),None)
     if t:self.current={"barcode":row["barcode"],"product":row["product"],"template":t}; self.cv.set(row["barcode"])
    break
 def print_current(self):
  if not self.current:messagebox.showinfo("Impressão","Gere ou selecione um código no histórico."); return
  try:os.startfile(create_label_pdf(self.current,"a4" if self.mv.get()=="A4" else "termica"))
  except Exception as e:messagebox.showerror("Impressão",str(e))
 def save_pdf(self):
  if not self.current:messagebox.showinfo("PDF","Gere ou selecione um código primeiro."); return
  dest=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")],initialfile=self.current["barcode"]+".pdf")
  if not dest:return
  try:
   shutil.copyfile(create_label_pdf(self.current,"a4" if self.mv.get()=="A4" else "termica"),dest); messagebox.showinfo("PDF","Arquivo salvo.")
  except Exception as e:messagebox.showerror("PDF",str(e))
if __name__=="__main__":App().mainloop()
