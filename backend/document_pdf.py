from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from urllib.parse import quote

def artifact_pdf(doc,qid,origin):
    data=BytesIO();styles=getSampleStyleSheet();story=[]
    for text,style in [('IVY HOPPER WORKS · FICTIONAL DEMO','Normal'),(doc['title'],'Title'),(doc['classification']+' · '+doc['version'],'Normal'),('Created by '+doc['creator']+' · Reviewed by '+doc['reviewed_by'],'Normal'),('Used by '+doc['used_by'],'Normal')]:story.extend([Paragraph(escape(text),styles[style]),Spacer(1,10)])
    for section in doc['sections']:
        story.append(Paragraph(escape(section['text']),styles['BodyText']))
        for c in section['citations']:
            if 'database' in c:
                url=f"{origin}/?database={c['database']}&line={c['line']}";label=f"{c['database']} row {c['line']}"
            else:
                url=f"{origin}/api/quotes/{qid}/sources/{quote(c['source'])}?line={c['line']}";label=f"Source {c['source']} line {c['line']}"
            story.append(Paragraph('<link href="'+escape(url,{'"':'&quot;'})+'" color="#28674e">'+escape(label)+'</link>',styles['Normal']))
        story.append(Spacer(1,12))
    SimpleDocTemplate(data,pagesize=A4,title=doc['title'],author='Ivy Hopper Works — fictional demo',leftMargin=45,rightMargin=45).build(story)
    return data.getvalue()
