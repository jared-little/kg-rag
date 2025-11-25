import pdfplumber
from utilities.utils import chunk_text, embed, get_neo4j_driver

driver = get_neo4j_driver()

text = ""
pdf_filename = "data/ch02-downloaded.pdf"
# pdf_filename = "data/ATL-COM-DAQ-2016-184.pdf"

with pdfplumber.open(pdf_filename) as pdf:
    for page in pdf.pages:
        text += page.extract_text()

chunks = chunk_text(text, 500, 40)

embeddings = embed(chunks)

print(f"Generated embeddings for {len(embeddings)} chunks.")
print(f"{len(embeddings)} embeddings of dimension {len(embeddings[0])} each.")

driver.execute_query("""CREATE VECTOR INDEX pdf IF NOT EXISTS
FOR (c:Chunk)
ON c.embedding""")

# Add to neo4j
cypher_query = '''
WITH $chunks as chunks, range(0, size($chunks)) AS index
UNWIND index AS i
WITH i, chunks[i] AS chunk, $embeddings[i] AS embedding
MERGE (c:Chunk {index: i})
SET c.text = chunk, c.embedding = embedding
'''

driver.execute_query(cypher_query, chunks=chunks, embeddings=embeddings)

print("Chunks and embeddings have been added to Neo4j.")
