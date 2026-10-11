from pathlib import Path
import json
import os
import urllib.request


KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge_base"
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/generate"
)
OLLAMA_MODEL = "llama3.2:3b"


def load_knowledge_base():
    documents = []

    for file_path in KNOWLEDGE_BASE_PATH.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            {
                "source": file_path.name,
                "content": content,
            }
        )

    return documents


def retrieve_context(question, documents):
    question_terms = set(
        question.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace(":", " ")
        .split()
    )

    scored_documents = []

    for document in documents:
        content_lower = document["content"].lower()

        score = sum(
            1
            for term in question_terms
            if term in content_lower
        )

        scored_documents.append(
            (
                score,
                document
            )
        )

    scored_documents.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_document = scored_documents[0][1]

    return best_document


def ask_ollama(question, context):
    prompt = f"""
Você é um assistente de Cyber Threat Intelligence.

Use somente o contexto abaixo como base principal para responder.

CONTEXTO:
{context}

PERGUNTA:
{question}

Responda em português do Brasil.

Estruture a resposta, quando fizer sentido, em:

1. O que aconteceu
2. Impacto possível
3. Ações recomendadas

Não invente informações que não estejam apoiadas no contexto.
"""

    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=300
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["response"]


def answer_question(question):
    documents = load_knowledge_base()

    if not documents:
        raise RuntimeError(
            "Nenhum documento encontrado na base de conhecimento."
        )

    selected_document = retrieve_context(
        question,
        documents
    )

    answer = ask_ollama(
        question,
        selected_document["content"]
    )

    return {
        "source": selected_document["source"],
        "answer": answer,
    }


if __name__ == "__main__":
    question = (
        "Foi detectado um possível ataque DDoS "
        "com alta confiança. Explique o incidente "
        "e indique ações recomendadas."
    )

    result = answer_question(question)

    print(
        f"\nFonte recuperada: {result['source']}\n"
    )

    print(result["answer"])