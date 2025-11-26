from utilities.utils import chunk_text, embed, get_neo4j_driver, open_ai_client


def AskQuestion(question):

    driver = get_neo4j_driver()
    records, _, _ = driver.execute_query("MATCH (c:Chunk) WHERE c.index = 0 RETURN c.embedding, c.text")
    question_embedding = embed([question])[0]

    system_message = "You're an expert but can only use the provided documents to respond to the questions."

    hybrid_query = '''
    CALL {
        // vector index
        CALL db.index.vector.queryNodes('pdf', $k, $question_embedding) YIELD node, score
        WITH collect({node:node, score:score}) AS nodes, max(score) AS max
        UNWIND nodes AS n
        // Normalize scores
        RETURN n.node AS node, (n.score / max) AS score
        UNION
        // keyword index
        CALL db.index.fulltext.queryNodes('PdfChunkFulltext', $question, {limit: $k})
        YIELD node, score
        WITH collect({node:node, score:score}) AS nodes, max(score) AS max
        UNWIND nodes AS n
        // Normalize scores
        RETURN n.node AS node, (n.score / max) AS score
    }
    // deduplicate results from both queries
    WITH node, max(score) AS score ORDER BY score DESC LIMIT $k
    RETURN node, score
    '''
    similar_hybrid_records, _, _ = driver.execute_query(hybrid_query, question_embedding=question_embedding, question=question, k=4)

    user_message = f"""
    Use the following documents to answer the question that will follow:
    {[doc["node"]["text"] for doc in similar_hybrid_records]}

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

    answer = ""
    for chunk in stream:
        answer += chunk.choices[0].delta.content or ""

    print(answer)
    return answer


if __name__ == "__main__":
    AskQuestion("What is gfex?")
    # AskQuestion("Is gfex an acronym?")
