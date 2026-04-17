import json
import threading

import numpy as np

from app.config import Config


class VectorStoreService:
    def __init__(self):
        self.store_dir = Config.VECTOR_STORE_DIR
        self.embeddings_path = self.store_dir / "embeddings.npy"
        self.metadata_path = self.store_dir / "metadata.json"

        self._lock = threading.Lock()
        self.embeddings = np.empty((0, 384), dtype=np.float32)
        self.metadata = []
        self._load()

    def add(self, embedding_rows, metadata_rows):
        if len(embedding_rows) != len(metadata_rows):
            raise ValueError("Embedding and metadata size mismatch")

        if len(metadata_rows) == 0:
            return 0

        incoming = np.array(embedding_rows, dtype=np.float32)
        if incoming.ndim != 2:
            raise ValueError("Embedding matrix must be 2D")

        with self._lock:
            self.embeddings = np.vstack([self.embeddings, incoming])
            self.metadata.extend(metadata_rows)
            self._persist()

        return len(metadata_rows)

    def search(self, query_embedding, top_k=5):
        if len(self.metadata) == 0:
            return []

        top_k = max(1, min(top_k, len(self.metadata)))
        scores = np.dot(self.embeddings, np.array(query_embedding, dtype=np.float32))
        best_idx = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in best_idx:
            row = dict(self.metadata[int(idx)])
            row["score"] = float(scores[int(idx)])
            results.append(row)
        return results

    def stats(self):
        unique_files = sorted({item.get("file_name", "unknown") for item in self.metadata})
        return {
            "chunks_indexed": len(self.metadata),
            "files_indexed": len(unique_files),
            "files": unique_files,
        }

    def _load(self):
        if self.embeddings_path.exists() and self.metadata_path.exists():
            self.embeddings = np.load(self.embeddings_path)
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

    def _persist(self):
        np.save(self.embeddings_path, self.embeddings)
        self.metadata_path.write_text(json.dumps(self.metadata, indent=2), encoding="utf-8")
