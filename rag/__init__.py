"""Existing academic RAG pipeline exposed for the Streamlit application."""

from .pipeline import RAGPipeline, create_pipeline

__all__ = ["RAGPipeline", "create_pipeline"]