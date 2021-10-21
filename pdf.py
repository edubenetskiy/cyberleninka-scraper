import io

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage


def extract_text_from_pdf(pdf_path: str) -> str:
    resource_manager = PDFResourceManager()
    text_output = io.StringIO()
    converter = TextConverter(resource_manager, text_output)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    try:
        with open(pdf_path, 'rb') as file_handle:
            for page in PDFPage.get_pages(file_handle, caching=True, check_extractable=True):
                page_interpreter.process_page(page)
        text = text_output.getvalue()
        if text:
            return text
        else:
            raise f"Could not extract text from PDF file {str}"
    finally:
        text_output.close()
        converter.close()
