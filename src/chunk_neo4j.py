import time
import pdfplumber
from utilities.utils import chunk_text, embed, get_neo4j_driver, num_tokens_from_string
import re

driver = get_neo4j_driver()


def split_text_by_titles():
    """Extracts text from a PDF and splits it into sections based on titles."""

    text = ""
    # pdf_filename = "data/ch02-downloaded.pdf"
    pdf_filename = "data/ATL-COM-DAQ-2016-184.pdf"
    with pdfplumber.open(pdf_filename) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    # A regular expression pattern for titles that
    # match lines starting with one or more digits, an optional uppercase letter,
    # followed by a dot, a space, and then up to 50 characters
    title_pattern = re.compile(r"(\n\d+[A-Z]?\. {1,3}.{0,60}\n)", re.DOTALL)
    titles = title_pattern.findall(text)
    # Split the text at these titles
    sections = re.split(title_pattern, text)
    sections_with_titles = []
    # Append the first section
    sections_with_titles.append(sections[0])
    # Iterate over the rest of sections
    for i in range(1, len(titles) + 1):
        section_text = sections[i * 2 - 1].strip() + "\n" + sections[i * 2].strip()
        sections_with_titles.append(section_text)

    print(f"Total sections found: {len(sections_with_titles)}")

    return sections_with_titles


def store_sections_in_neo4j(sections):
    """Stores sections and their chunks in Neo4j.
    Splits sections into parent chunks and child chunks, and stores them in Neo4j with embeddings."""

    parent_chunks = []
    for s in sections:
        parent_chunks.extend(chunk_text(s, 2000, 40))
    
    cypher_import_query = """
    MERGE (pdf:PDF {id:$pdf_id})
    MERGE (p:Parent {id:$pdf_id + '-' + $id})
    SET p.text = $parent
    MERGE (pdf)-[:HAS_PARENT]->(p)
    WITH p, $children AS children, $embeddings as embeddings
    UNWIND range(0, size(children) - 1) AS child_index
    MERGE (c:Child {id: $pdf_id + '-' + $id + '-' + toString(child_index)})
    SET c.text = children[child_index], c.embedding = embeddings[child_index]
    MERGE (p)-[:HAS_CHILD]->(c);
    """
    
    for i, chunk in enumerate(parent_chunks):
        if num_tokens_from_string(chunk) < 40:
            print(f"chunk {i} is too small:")
            print(chunk)
            print("----")

    for i, chunk in enumerate(parent_chunks):
        # skip small chunks
        if num_tokens_from_string(chunk) < 40: continue
        child_chunks = chunk_text(chunk, 500, 20)
        embeddings = embed(child_chunks)
        # Add to neo4j
        driver.execute_query(
            cypher_import_query,
            id=str(i),
            pdf_id="gfex TDR",
            parent=chunk,
            children=child_chunks,
            embeddings=embeddings,
        )
    index_name = "parent"
    driver.execute_query("""CREATE VECTOR INDEX parent IF NOT EXISTS
    FOR (c:Child)
    ON c.embedding""")


def chunk_pdf():   
    """Extracts text from a PDF and splits it into chunks."""

    text = ""
    # pdf_filename = "data/ch02-downloaded.pdf"
    pdf_filename = "data/ATL-COM-DAQ-2016-184.pdf"

    with pdfplumber.open(pdf_filename) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    chunks = chunk_text(text, 500, 40)


def create_embeddings(chunks):
    """Generates embeddings for text chunks and stores them in Neo4j."""
    embeddings = embed(chunks)

    # print(f"Generated embeddings for {len(embeddings)} chunks.")
    # print(f"{len(embeddings)} embeddings of dimension {len(embeddings[0])} each.")

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

    # CREATE FULLTEXT INDEX
    try : driver.execute_query("CREATE FULLTEXT INDEX PdfChunkFulltext FOR (c:Chunk) ON EACH [c.text]")
    except: print("Fulltext Index already exists")

    print("Fulltext index created (if it did not already exist).")


if __name__ == "__main__":

    start_time = time.time()

    sections = split_text_by_titles()
    print(f"Number of sections: {len(sections)}")
    store_sections_in_neo4j(sections)
    end_time = time.time()

    print(f"Time taken to split text by titles: {end_time - start_time} seconds")
