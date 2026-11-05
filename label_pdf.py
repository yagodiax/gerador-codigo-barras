import os,tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
def create_label_pdf(label,mode="termica"):
 t=label["template"]; w=float(t["width_mm"])*mm; h=float(t["height_mm"])*mm
 fd,path=tempfile.mkstemp(prefix="etiqueta_",suffix=".pdf"); os.close(fd)
 if mode=="a4":
  pw,ph=A4; c=canvas.Canvas(path,pagesize=A4); margin=10*mm; gap=3*mm
  cols=max(1,int((pw-2*margin+gap)//(w+gap))); rows=max(1,int((ph-2*margin+gap)//(h+gap)))
  x=margin; y=ph-margin-h
 else:
  c=canvas.Canvas(path,pagesize=(w,h)); x=0; y=0; cols=rows=1
 draw_label(c,x,y,w,h,label)
 c.save(); return path
def draw_label(c,x,y,w,h,label):
 pad=2*mm
 c.setFont("Helvetica-Bold",max(7,min(12,h/mm*.25)))
 c.drawCentredString(x+w/2,y+h-pad-4*mm,label["product"][:35])
 bc=code128.Code128(label["barcode"],barHeight=max(8*mm,h*.42),barWidth=.25*mm,humanReadable=False)
 scale=min(1,(w-2*pad)/bc.width)
 c.saveState(); c.translate(x+(w-bc.width*scale)/2,y+h*.22); c.scale(scale,1); bc.drawOn(c,0,0); c.restoreState()
 c.setFont("Helvetica",7); c.drawCentredString(x+w/2,y+pad,label["barcode"])
