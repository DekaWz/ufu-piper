from pathlib import Path
from typing import Union

from files_parser import Parser

import pypdfium2 as pdfium


class PdfParser(Parser):
    def __init__(self):
        pass

    def get_pdf_text(self, file_name):
        doc = pdfium.PdfDocument(file_name)
        text_list = []
        
        for page in doc:
            text_page = page.get_textpage()
            text_list.append(text_page.get_text_bounded())
            
        return "".join(text_list)


if __name__ == "__main__":
    pass