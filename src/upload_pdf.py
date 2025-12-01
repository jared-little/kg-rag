import time
import pdfplumber
from utilities.utils import chunk_text, embed, get_neo4j_driver, num_tokens_from_string
import re

driver = get_neo4j_driver()


def extract_text_from_pdf(pdf_filename):
    """Extracts text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_filename) as pdf:
        title = pdf.metadata.get('Title')
        if title is None: title = pdf_filename.split("/")[-1].replace(".pdf", "")
        print(f"Extracted title: {title}")
        for page in pdf.pages:
            text += page.extract_text()
    return title, text


def split_text_by_titles(pdf_filename="data/ATL-COM-DAQ-2016-184.pdf"):
    """Extracts text from a PDF and splits it into sections based on titles."""

    # text = ""
    # with pdfplumber.open(pdf_filename) as pdf:
    #     for page in pdf.pages:
    #         text += page.extract_text()

    title, text = extract_text_from_pdf(pdf_filename)

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

    return title, sections_with_titles


def store_sections_in_neo4j(title, sections):
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
            pdf_id=title,
            parent=chunk,
            children=child_chunks,
            embeddings=embeddings,
        )
    index_name = "parent"
    driver.execute_query("""CREATE VECTOR INDEX parent IF NOT EXISTS
    FOR (c:Child)
    ON c.embedding""")


def main(pdf_list):
    for pdf in pdf_list:
        print(f"Processing PDF: {pdf}")
        title, sections = split_text_by_titles(pdf)
        store_sections_in_neo4j(title, sections)

if __name__ == "__main__":
    pdf_list = ["data/ATL-COM-DAQ-2016-184.pdf", "data/ATL-DAQ-PROC-2016-023.pdf"]

    start_time = time.time()
    main(pdf_list)
    end_time = time.time()
    print(f"Time taken to store sections in Neo4j: {end_time - start_time} seconds")
