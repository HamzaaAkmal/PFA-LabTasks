from functools import lru_cache

from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.exam_service import ExamService
from app.services.rag_service import RagService
from app.services.vector_store_service import VectorStoreService


@lru_cache(maxsize=1)
def get_document_service():
	return DocumentService()


@lru_cache(maxsize=1)
def get_embedding_service():
	return EmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store_service():
	return VectorStoreService()


@lru_cache(maxsize=1)
def get_rag_service():
	return RagService(
		embedding_service=get_embedding_service(),
		vector_store=get_vector_store_service(),
	)


@lru_cache(maxsize=1)
def get_exam_service():
	return ExamService(rag_service=get_rag_service())
