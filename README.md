GitHub Repository Description

Academic Study Assistant — a RAG-powered AI chatbot that helps students understand their study material using document retrieval, semantic search, and Groq-powered LLM generation.

A RAG-powered academic study assistant that answers questions from your study material with source-aware responses.

README opening

Academic Study Assistant

Academic Study Assistant is a Retrieval-Augmented Generation (RAG) based chatbot designed to help students interact with their academic study material.

Instead of relying entirely on an LLM’s general knowledge, the system retrieves relevant information from the provided academic documents and uses that context to generate grounded answers.

The application provides a simple Streamlit interface where users can ask questions and receive answers along with the relevant source information.

Tech Stack: Python · Streamlit · LangChain · FAISS · Sentence Transformers · PyMuPDF · Groq

Core Pipeline:

Academic Documents
        ↓
    Text Extraction
        ↓
      Chunking
        ↓
    Embeddings
        ↓
      FAISS
        ↓
     Retrieval
        ↓
 Relevant Context
        ↓
     Groq LLM
        ↓
 Answer + Sources

The project is currently focused on building a reliable academic RAG pipeline, with future plans for quiz generation, flashcards, exam preparation, hybrid retrieval, reranking, and other learning-focused features.
