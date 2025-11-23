import pdfplumber
from utils import chunk_text

text = ""
pdf_filename = "ch02-downloaded.pdf"

with pdfplumber.open(pdf_filename) as pdf:
    for page in pdf.pages:
        text += page.extract_text()

# print(text[0:20])


chunks = chunk_text(text, 500, 40)
print(len(chunks))
print(chunks[0])