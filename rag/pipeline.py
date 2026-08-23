"""Application adapter for the RAG pipeline built in Notebook/introduction.ipynb.

This module reuses the persisted Chroma collection and the notebook's embedding
and retrieval choices. It does not ingest or re-index documents at app startup.
"""

import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VECTOR_STORE_PATH = PROJECT_ROOT / "Data" / "vector_store"
ENV_PATH = PROJECT_ROOT / "Notebook" / ".env"


def _load_environment() -> None:
	try:
		from dotenv import load_dotenv

		load_dotenv()
		load_dotenv(PROJECT_ROOT / ".env")
		load_dotenv(PROJECT_ROOT / "Notebook" / ".env")
	except ImportError:
		# Environment variables still work when python-dotenv is unavailable.
		pass


class RAGPipeline:
	"""Load the existing embedding, Chroma retrieval, and Groq generation flow."""

	def __init__(
		self,
		persist_directory: Path = VECTOR_STORE_PATH,
		model_name: str = "all-MiniLM-L6-v2",
		collection_name: str = "pdf_documents",
	) -> None:
		_load_environment()
		from sentence_transformers import SentenceTransformer
		import chromadb

		self.embedding_model = SentenceTransformer(model_name)
		self.client = chromadb.PersistentClient(path=str(persist_directory))
		self.collection = self.client.get_collection(name=collection_name)
		self.model_name = model_name
		self.llm = self._create_llm()

	def _create_llm(self) -> Any:
		api_key = os.getenv("GROQ_API_KEY")
		if not api_key:
			return None

		from langchain_groq import ChatGroq

		return ChatGroq(
			groq_api_key=api_key,
			model_name=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
			temperature=0.1,
			max_tokens=1024,
		)

	def _retrieve(self, question: str, top_k: int = 5, min_score: float = 0.0) -> list[dict[str, Any]]:
		query_embedding = self.embedding_model.encode([question])[0]
		results = self.collection.query(
			query_embeddings=[query_embedding.tolist()],
			n_results=top_k,
		)
		if not results.get("documents") or not results["documents"][0]:
			return []

		retrieved: list[dict[str, Any]] = []
		for rank, (document, metadata, distance) in enumerate(
			zip(
				results["documents"][0],
				results["metadatas"][0],
				results["distances"][0],
			),
			start=1,
		):
			similarity_score = 1 - distance
			if similarity_score >= min_score:
				retrieved.append(
					{
						"content": document,
						"metadata": metadata or {},
						"similarity_score": similarity_score,
						"rank": rank,
					}
				)
		return retrieved

	def ask(self, question: str, subject: str = "") -> dict[str, Any]:
		question = question.strip()
		if not question:
			return {"answer": "Please enter a question.", "sources": []}

		results = self._retrieve(question)
		if not results:
			return {"answer": "No relevant context found for this question.", "sources": []}

		context = "\n\n".join(item["content"] for item in results)
		sources = [
			{
				"document": metadata.get("source_file", metadata.get("source", "Unknown document")),
				"page": metadata.get("page"),
				"score": item["similarity_score"],
				"preview": item["content"][:300],
			}
			for item in results
			for metadata in [item["metadata"]]
		]

		if self.llm is None:
			return {
				"answer": "The relevant study material was found, but the response service is not configured. Set GROQ_API_KEY to generate an answer.",
				"sources": sources,
			}

		prompt = (
			"Use the following context to answer the question accurately and concisely. "
			"If the context does not contain enough information, say so.\n\n"
			f"Context:\n{context}\n\nQuestion: {question}\n"
			f"Subject: {subject}\n\nAnswer:"
		)
		response = self.llm.invoke([prompt])
		answer = getattr(response, "content", "")
		if not isinstance(answer, str) or not answer.strip():
			return {"answer": "The response was empty. Please try the question again.", "sources": sources}
		return {"answer": answer.strip(), "sources": sources}


def create_pipeline() -> RAGPipeline:
	"""Create one pipeline instance for Streamlit's resource cache."""
	return RAGPipeline()