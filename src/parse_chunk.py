import pdfplumber
from utilities.utils import chunk_text

text = ""
pdf_filename = "data/ch02-downloaded.pdf"

with pdfplumber.open(pdf_filename) as pdf:
    for page in pdf.pages:
        text += page.extract_text()

chunks = chunk_text(text, 500, 40)
print(f"Document chunked into {len(chunks)} chunks.")
