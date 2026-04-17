from pypdf import PdfReader

from app.config import Config
from app.utils.text_utils import normalize_text


class DocumentService:
    def __init__(self):
        self.upload_dir = Config.UPLOAD_DIR

    def save_upload(self, file_storage, file_name):
        destination = self.upload_dir / file_name
        file_storage.save(destination)
        return destination

    def extract_text(self, file_path):
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._extract_pdf_text(file_path)

        if suffix in {".txt", ".md"}:
            return normalize_text(file_path.read_text(encoding="utf-8", errors="ignore"))

        raise ValueError(f"Unsupported file type: {suffix}")

    def chunk_text(self, text):
        words = text.split()
        if not words:
            return []

        chunk_size = Config.CHUNK_SIZE
        overlap = Config.CHUNK_OVERLAP

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end]).strip()
            if len(chunk) > 40:
                chunks.append(chunk)

            if end >= len(words):
                break

            start = max(0, end - overlap)

        return chunks

    def _extract_pdf_text(self, file_path):
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        joined = "\n".join(pages)
        return normalize_text(joined)
