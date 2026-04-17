from app.config import Config
from app.utils.text_utils import keyword_overlap_score, split_sentences


class RagService:
    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(self, query, top_k=None):
        if not query.strip():
            return []

        query_embedding = self.embedding_service.embed_query(query)
        limit = top_k or Config.DEFAULT_TOP_K
        return self.vector_store.search(query_embedding, top_k=limit)

    def answer_question(self, question, top_k=None):
        retrieved = self.retrieve(question, top_k=top_k)
        if not retrieved:
            return {
                "answer": "No relevant study content was found. Upload notes or PDFs first.",
                "contexts": [],
            }

        ranked_sentences = []
        for item in retrieved:
            text = item.get("text", "")
            for sentence in split_sentences(text):
                score = keyword_overlap_score(sentence, question) + (item.get("score", 0.0) * 0.15)
                ranked_sentences.append((score, sentence))

        ranked_sentences.sort(key=lambda pair: pair[0], reverse=True)
        best = [sentence for _, sentence in ranked_sentences[:4]]

        if not best:
            best = [item.get("text", "")[:260].strip() for item in retrieved[:2]]

        answer = " ".join(best).strip()
        answer = answer if answer else "The material was retrieved, but no clear sentence-level answer was found."

        contexts = [
            {
                "file_name": item.get("file_name", "unknown"),
                "score": round(float(item.get("score", 0.0)), 4),
                "text": item.get("text", "")[:500],
            }
            for item in retrieved
        ]

        return {
            "answer": answer,
            "contexts": contexts,
        }
