from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether

def customer_pdf(p):
    """Only accepts an allowlisted customer package; never a quote/context object."""
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=(612,792),rightMargin=44,leftMargin=44,topMargin=40,bottomMargin=44)
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='ArcTitle',fontName='Times-Bold',fontSize=26,leading=30,textColor=colors.HexColor('#002139'),spaceAfter=18))
    styles['Normal'].textColor=colors.HexColor('#495050');styles['Normal'].leading=15
    def para(text,style='Normal'):return Paragraph(escape(str(text)),styles[style])
    story=[];logo=Path(__file__).resolve().parent/'assets'/'logo-dark.png'
    if logo.exists():
        from PIL import Image as PILImage
        w,h=PILImage.open(logo).size
        styles.add(ParagraphStyle(name='ProductWordmark',fontName='Helvetica-Bold',fontSize=19,leading=23,textColor=colors.HexColor('#002139'),alignment=1))
        styles.add(ParagraphStyle(name='ProductEndorsement',fontName='Helvetica',fontSize=8,leading=10,textColor=colors.HexColor('#002139'),alignment=1))
        endorsement=Table([[para('An','ProductEndorsement'),Image(str(logo),width=75,height=75*h/w),para('Product','ProductEndorsement')]],colWidths=[18,80,36],hAlign='CENTER')
        endorsement.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        lockup=Table([[para('FIELD & FORGE','ProductWordmark')],[endorsement]],colWidths=[180],hAlign='LEFT')
        lockup.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
        story += [KeepTogether([lockup,Spacer(1,18)])]
    story += [para('Manufacturing quotation','ArcTitle'),para('FICTIONAL DEMONSTRATION • NOT A REAL COMMERCIAL OFFER'),Spacer(1,14),para(p['seller'],'Heading2'),para('Fictional demo company'),para('Prepared for '+p['customer']),para('Recipient: '+p['recipient']),para('Quote '+p['quote_id'][:8].upper()+' · Revision '+str(p['revision'])),Spacer(1,16),para(p['description']),Spacer(1,14)]
    rows=[[para('Configuration'),para('Selected scope')]]+[[para(k.title()),para(v)] for k,v in p['configuration'].items()]
    rows += [[para('Order quantity'),para(p['quantity']+' assemblies')],[para('Total selling price'),para('USD '+p['selling_price'])]]
    t=Table(rows,colWidths=[145,379],hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6F6FC')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.5,colors.HexColor('#DDDDDD'))]));story.append(t)
    story += [Spacer(1,16),para('Commercial terms','Heading2')]
    for key in ['payment','freight','tax','delivery','exclusions']:story += [para(key.title()+': '+p['terms'][key]),Spacer(1,5)]
    story += [para('Valid through '+p['expires_at'][:10]+'. Conditional ready-to-ship forecast: '+p['ready_to_ship']+'.'),Spacer(1,8),para(p['drawing']),Spacer(1,12),para('Acceptance: record an explicit customer response against this quote and revision. A download is not proof of sending or acceptance.'),Spacer(1,14),para(p['branding'])]
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#495050'));canvas.drawString(44,24,'Fictional demonstration • Agentic Arc');canvas.drawRightString(568,24,f'Page {doc.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer);return buf.getvalue()
