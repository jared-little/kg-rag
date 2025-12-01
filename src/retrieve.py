from utilities.utils import chunk_text, embed, get_neo4j_driver, get_openai_client, chat
from typing import List


def generate_answer(question: str, documents: List[str]) -> str:
    """Generates an answer to a question using provided documents."""
    answer_system_message = "You're an expert, but can only use the provided documents to respond to the questions."
    user_message = f"""
    Use the following documents to answer the question that will follow:
    {documents}

    ---

    The question to answer using information only from the above documents: {question}
    """
    result = chat(
        messages=[
            {"role": "system", "content": answer_system_message},
            {"role": "user", "content": user_message},
        ]
    )
    print("Response:", result)


def parent_retrieval(question: str, k: int = 4) -> List[str]:
    """Retrieves the most relevant parent chunks from Neo4j based on the question."""
    driver = get_neo4j_driver()
    retrieval_query = """
    CALL db.index.vector.queryNodes($index_name, $k * 4, $question_embedding)
    YIELD node, score
    MATCH (node)<-[:HAS_CHILD]-(parent)
    WITH parent, max(score) AS score
    RETURN parent.text AS text, score
    ORDER BY score DESC
    LIMIT toInteger($k)
    """

    question_embedding = embed([question])[0]
    index_name = "parent"
    similar_records, _, _ = driver.execute_query(
        retrieval_query,
        question_embedding=question_embedding,
        k=k,
        index_name=index_name,
    )

    return [record["text"] for record in similar_records]


def generate_stepback(question: str):
    stepback_system_message = """
        You are an expert at world knowledge. Your task is to step back
        and paraphrase a question to a more generic step-back question, which
        is easier to answer. Here are a few examples

        "input": "Could the members of The Police perform lawful arrests?"
        "output": "what can the members of The Police do?"

        "input": "Jan Sindel’s was born in what country?"
        "output": "what is Jan Sindel’s personal history?"
        """
    user_message = f"""{question}"""
    step_back_question = chat(
        messages=[
            {"role": "system", "content": stepback_system_message},
            {"role": "user", "content": user_message},
        ]
    )
    return step_back_question


def rag_pipeline(question: str) -> str:
    stepback_prompt = generate_stepback(question)
    print(f"Stepback prompt: {stepback_prompt}")
    documents = parent_retrieval(stepback_prompt)
    answer = generate_answer(question, documents)
    return answer


if __name__ == "__main__":

    rag_pipeline("What is gfex?")
