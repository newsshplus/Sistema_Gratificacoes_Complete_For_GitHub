
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report(filename, report_title, rows, totals=None, footer_text=None):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20,leftMargin=20, topMargin=20,bottomMargin=20)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph(report_title, styles['Title']))
    elems.append(Spacer(1,6))
    # Table data
    data = [['Vendedor','Vendas','Meta 100%','% Atingido','Gratificação Base','Bônus','Total Pago']]
    for r in rows:
        data.append([r.get('vendedor'), f"R$ {r.get('vendas'):,}", f"R$ {r.get('meta_100'):,}", f"{r.get('atingimento')*100:.2f}%" if r.get('atingimento') is not None else '-', f"R$ {r.get('grat_base'):,}", f"R$ {r.get('bonus'):,}", f"R$ {r.get('total'):,}"])
    if totals:
        data.append(['TOTAL','','','','','', f"R$ {totals:,}"])
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2E86C1')),
                           ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                           ('GRID',(0,0),(-1,-1),0.5,colors.grey),
                           ('ALIGN',(1,1),(-1,-1),'RIGHT')]))
    elems.append(t)
    elems.append(Spacer(1,12))
    if footer_text:
        elems.append(Paragraph(footer_text, styles['Normal']))
    doc.build(elems)
    return filename
