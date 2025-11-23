import requests

remote_pdf_url = "https://arxiv.org/pdf/1709.00666.pdf"
pdf_filename = "ch02-downloaded.pdf"

response = requests.get(remote_pdf_url)

if response.status_code == 200:
    with open(pdf_filename, "wb") as pdf_file:
        pdf_file.write(response.content)
else:
    print("Failed to download the PDF. Status code:", response.status_code)

print(f"PDF downloaded successfully and saved as {pdf_filename}")