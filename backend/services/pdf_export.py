import logging

try:
    from weasyprint import HTML
    WEASYPRINT_INSTALLED = True
except ImportError:
    WEASYPRINT_INSTALLED = False

logger = logging.getLogger('ats_resume_scorer')

def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if not WEASYPRINT_INSTALLED:
        raise ImportError("WeasyPrint library is not installed on this system. PDF generation unavailable.")

    documents = []
    for name, html_str in html_docs.items():
        doc = HTML(string=html_str).render()
        documents.append(doc)

    first_doc = documents[0]
    for other_doc in documents[1:]:
        for page in other_doc.pages:
            first_doc.pages.append(page)

    return first_doc.write_pdf()
