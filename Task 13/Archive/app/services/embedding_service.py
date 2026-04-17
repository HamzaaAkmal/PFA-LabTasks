from sentence_transformers import SentenceTransformer

from app.config import Config


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME)

    def embed_texts(self, texts):
        if not texts:
            return []
        return self.model.encode(texts, normalize_embeddings=True)

    def embed_query(self, query):
        return self.model.encode([query], normalize_embeddings=True)[0]
