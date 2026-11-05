import os
import tempfile

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128


def draw_label(pdf, x, y, width, height, label):
    padding = 2 * mm
    title_size = max(7, min(12, height / mm * 0.25))
    pdf.setFont("Helvetica-Bold", title_size)
    pdf.drawCentredString(x + width / 2, y + height - padding - 4 * mm, label["product"][:35])

    barcode = code128.Code128(
        label["barcode"],
        barHeight=max(8 * mm, height * 0.42),
        barWidth=0.25 * mm,
        humanReadable=False,
    )
    scale = min(1, (width - 2 * padding) / barcode.width)
    pdf.saveState()
    pdf.translate(x + (width - barcode.width * scale) / 2, y + height * 0.22)
    pdf.scale(scale, 1)
    barcode.drawOn(pdf, 0, 0)
    pdf.restoreState()

    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(x + width / 2, y + padding, label["barcode"])


def create_label_pdf(label, mode="termica"):
    template = label["template"]
    width = float(template["width_mm"]) * mm
    height = float(template["height_mm"]) * mm
    fd, path = tempfile.mkstemp(prefix="etiqueta_", suffix=".pdf")
    os.close(fd)

    if mode == "a4":
        page_width, page_height = A4
        margin = 10 * mm
        gap = 3 * mm
        columns = max(1, int((page_width - 2 * margin + gap) // (width + gap)))
        rows = max(1, int((page_height - 2 * margin + gap) // (height + gap)))
        used_width = columns * width + (columns - 1) * gap
        used_height = rows * height + (rows - 1) * gap
        start_x = (page_width - used_width) / 2
        start_y = (page_height + used_height) / 2 - height
        pdf = canvas.Canvas(path, pagesize=A4)
        for row in range(rows):
            for column in range(columns):
                x = start_x + column * (width + gap)
                y = start_y - row * (height + gap)
                draw_label(pdf, x, y, width, height, label)
    else:
        pdf = canvas.Canvas(path, pagesize=(width, height))
        draw_label(pdf, 0, 0, width, height, label)

    pdf.save()
    return path
