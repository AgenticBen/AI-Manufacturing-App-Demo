from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderSVG
from pathlib import Path
url='https://agentic-arc-manufacturing.vercel.app'
widget=qr.QrCodeWidget(url);x0,y0,x1,y1=widget.getBounds();size=320
d=Drawing(size,size,transform=[size/(x1-x0),0,0,size/(y1-y0),0,0]);d.add(widget)
Path('public/assets/demo-qr.svg').write_text(renderSVG.drawToString(d))
Path('artifacts/demo-qr.svg').write_text(renderSVG.drawToString(d))
print('QR generated from verified public Vercel URL.')
