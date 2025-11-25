import os

import tiktoken
from neo4j import GraphDatabase
from openai import OpenAI
from sentence_transformers import SentenceTransformer

open_ai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def get_neo4j_driver():
    neo4j_user = 'neo4j'
    neo4j_password = 'abcd1234'
    neo4j_URI = 'neo4j://127.0.0.1:7687'
    neo4j_driver = GraphDatabase.driver(
        neo4j_URI,
        auth=(neo4j_user, neo4j_password),
        notifications_min_severity="OFF"
    )
    return neo4j_driver

def chunk_text(text, chunk_size, overlap, split_on_whitespace_only=True):
    chunks = []
    index = 0

    while index < len(text):
        if split_on_whitespace_only:
            prev_whitespace = 0
            left_index = index - overlap
            while left_index >= 0:
                if text[left_index] == " ":
                    prev_whitespace = left_index
                    break
                left_index -= 1
            next_whitespace = text.find(" ", index + chunk_size)
            if next_whitespace == -1:
                next_whitespace = len(text)
            chunk = text[prev_whitespace:next_whitespace].strip()
            chunks.append(chunk)
            index = next_whitespace + 1
        else:
            start = max(0, index - overlap + 1)
            end = min(index + chunk_size + overlap, len(text))
            chunk = text[start:end].strip()
            chunks.append(chunk)
            index += chunk_size

    return chunks


def num_tokens_from_string(string: str, model: str = "gpt-4") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def embed(texts, model=SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')):
    embedding = model.encode(texts)

    return list(map(lambda n: n.tolist(), embedding))


def chat(messages, model="gpt-4o", temperature=0, config={}):
    response = open_ai_client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        **config,
    )
    return response.choices[0].message.content


def tool_choice(messages, model="gpt-4o", temperature=0, tools=[], config={}):
    response = open_ai_client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        tools=tools or None,
        **config,
    )
    return response.choices[0].message.tool_calls