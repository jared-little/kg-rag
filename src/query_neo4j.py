from utilities.utils import chunk_text, embed, get_neo4j_driver
from utilities.utils import open_ai_client

driver = get_neo4j_driver()

records, _, _ = driver.execute_query("MATCH (c:Chunk) WHERE c.index = 0 RETURN c.embedding, c.text")

question = "At what time was Einstein really interested in experimental works?"
question_embedding = embed([question])[0]

query = '''
CALL db.index.vector.queryNodes('pdf', $k, $question_embedding) YIELD node AS hits, score
RETURN hits.text AS text, score, hits.index AS index
'''
similar_records, _, _ = driver.execute_query(query, question_embedding=question_embedding, k=4)

system_message = "You're en Einstein expert, but can only use the provided documents to respond to the questions."
user_message = f"""
Use the following documents to answer the question that will follow:
{[doc["text"] for doc in similar_records]}

---

The question to answer using information only from the above documents: {question}
"""

print("Question:", question)

stream = open_ai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")