from datetime import datetime

from rag.rag_engine import answer_question


def analyze_incident(
    predicted_class,
    probability_ddos,
    created_at=None
):
    if created_at is None:
        created_at = datetime.now().isoformat()

    if predicted_class != "DDoS":
        return {
            "status": "no_threat",
            "message": "Nenhum incidente DDoS detectado."
        }

    question = f"""
Foi detectado um possível incidente de segurança.

Classe detectada: {predicted_class}
Probabilidade de DDoS: {probability_ddos:.2%}
Horário da detecção: {created_at}

Explique o incidente, o impacto possível e as ações recomendadas.
"""

    result = answer_question(question)

    return {
        "status": "threat_detected",
        "class": predicted_class,
        "probability_ddos": probability_ddos,
        "created_at": created_at,
        "knowledge_source": result["source"],
        "analysis": result["answer"]
    }


if __name__ == "__main__":
    incident = analyze_incident(
        predicted_class="DDoS",
        probability_ddos=0.9998
    )

    print("\n=== INCIDENTE ===\n")

    print(
        f"Classe: {incident['class']}"
    )

    print(
        f"Probabilidade DDoS: "
        f"{incident['probability_ddos']:.2%}"
    )

    print(
        f"Fonte RAG: "
        f"{incident['knowledge_source']}"
    )

    print("\n=== ANÁLISE DA IA ===\n")

    print(
        incident["analysis"]
    )