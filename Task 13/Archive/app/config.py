from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    VECTOR_STORE_DIR = DATA_DIR / "vector_store"
    PROCESSED_DIR = DATA_DIR / "processed"
    FRONTEND_DIR = BASE_DIR / "frontend"

    MAX_CONTENT_LENGTH = 40 * 1024 * 1024  # 40 MB
    ALLOWED_EXTENSIONS = {"pdf", "txt", "md"}

    CHUNK_SIZE = 900
    CHUNK_OVERLAP = 180

    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_TOP_K = 5


    @classmethod
    def ensure_directories(cls) -> None:
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
