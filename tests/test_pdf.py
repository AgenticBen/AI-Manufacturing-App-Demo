from io import BytesIO
from pypdf import PdfReader
from backend.pdf_export import customer_pdf
from test_domain import walkthrough

def test_customer_pdf_allowlist_and_original_logo():
    for sid in ['seed','grain','feed']:
        q=walkthrough(sid);data=customer_pdf(q['package']);pdf=PdfReader(BytesIO(data));text='\n'.join(p.extract_text() for p in pdf.pages)
        assert 'Ivy Hopper Works' in text and 'Fictional demo company' in text
        assert q['package']['selling_price'] in text
        for internal in ['Projected gross','gross margin','base cost','loaded rate','Midwest Fasteners','Prairie Metals','Internal route']:
            assert internal.lower() not in text.lower()
        assert sum(len(p.images) for p in pdf.pages)>=1,'Original logo must be embedded'
        assert len(pdf.pages)<=3
