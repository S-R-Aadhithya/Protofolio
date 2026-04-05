"""
rag_ingestor.py — Direct ChromaDB RAG pipeline.

Bypasses Mem0's internal LLM overhead for maximum token efficiency.
Chunks + embeds raw text (resume, linkedin, github) directly into ChromaDB
with per-user, per-source metadata, enabling precise retrieval for the
Chairman SME synthesis call.
"""

import os
import uuid
from typing import Optional


class RAGIngestor:
    """
    Splits professional content (resume / LinkedIn / GitHub) into semantic
    chunks and embeds them directly into ChromaDB using Gemini embeddings
    (or a default SentenceTransformer fallback when no API key is present).
    """

    CHUNK_SIZE = 500       # characters per chunk
    CHUNK_OVERLAP = 80     # overlap to preserve context across boundaries

    def __init__(self):
        self._collection = None
        self._splitter = self._init_splitter()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _init_splitter():
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        return RecursiveCharacterTextSplitter(
            chunk_size=RAGIngestor.CHUNK_SIZE,
            chunk_overlap=RAGIngestor.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _get_collection(self):
        """Lazily initialize the ChromaDB persistent collection."""
        if self._collection is not None:
            return self._collection

        import chromadb
        from chromadb.utils import embedding_functions

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        db_path = os.path.join("instance", "chromadb")
        os.makedirs(db_path, exist_ok=True)

        client = chromadb.PersistentClient(path=db_path)

        if api_key:
            try:
                ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                    api_key=api_key,
                    model_name="models/embedding-001",
                )
            except Exception as e:
                print(f"WARNING: Gemini EF failed ({e}), using default SentenceTransformer.")
                ef = embedding_functions.DefaultEmbeddingFunction()
        else:
            print("WARNING: No Gemini API key found — using default embedding function.")
            ef = embedding_functions.DefaultEmbeddingFunction()

        self._collection = client.get_or_create_collection(
            name="protofolio_rag",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #

    def ingest(self, user_id: str, text: str, source: str) -> int:
        """
        Chunk `text` and upsert into ChromaDB for `user_id`.

        Args:
            user_id: User's email / unique ID (used as partition key).
            text:    Raw extracted text (resume PDF, LinkedIn HTML, GitHub JSON).
            source:  One of "resume", "resume_summary", "linkedin",
                     "linkedin_summary", "github", "github_summary".

        Returns:
            Number of chunks stored (0 on failure).
        """
        if not text or not text.strip():
            print(f"INFO: RAGIngestor.ingest — empty text for source={source}, skipping.")
            return 0

        try:
            collection = self._get_collection()
            chunks = self._splitter.split_text(text)
            if not chunks:
                return 0

            # Delete stale chunks for this user+source before re-indexing
            try:
                existing = collection.get(
                    where={"$and": [
                        {"user_id": {"$eq": user_id}},
                        {"source":  {"$eq": source}},
                    ]}
                )
                if existing["ids"]:
                    collection.delete(ids=existing["ids"])
            except Exception:
                pass  # collection may be empty — safe to ignore

            ids = [
                f"{user_id}__{source}__{i}__{uuid.uuid4().hex[:6]}"
                for i in range(len(chunks))
            ]
            metadatas = [
                {"user_id": user_id, "source": source, "chunk_index": i}
                for i in range(len(chunks))
            ]

            collection.add(documents=chunks, ids=ids, metadatas=metadatas)
            print(
                f"INFO: RAGIngestor ✓ stored {len(chunks)} chunks "
                f"[user={user_id}, source={source}]"
            )
            return len(chunks)

        except Exception as e:
            print(f"WARNING: RAGIngestor.ingest failed: {e}")
            return 0

    def retrieve(self, user_id: str, query: str, top_k: int = 8) -> str:
        """
        Semantic retrieval of the most relevant chunks for `user_id`.

        Returns chunks concatenated with separators, ready to be fed
        directly into the Chairman SME prompt.
        """
        try:
            collection = self._get_collection()
            total = collection.count()
            if total == 0:
                return ""

            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, total),
                where={"user_id": {"$eq": user_id}},
            )
            docs = results.get("documents", [[]])[0]
            return "\n\n---\n\n".join(docs) if docs else ""

        except Exception as e:
            print(f"WARNING: RAGIngestor.retrieve failed: {e}")
            return ""

    def get_chunk_counts(self, user_id: str) -> dict:
        """
        Returns how many chunks per primary source are indexed for `user_id`.
        Keys: resume, linkedin, github  (summaries rolled into parent source).
        """
        counts = {"resume": 0, "linkedin": 0, "github": 0}
        try:
            collection = self._get_collection()
            for source in list(counts.keys()) + [
                "resume_summary", "linkedin_summary", "github_summary"
            ]:
                try:
                    res = collection.get(
                        where={"$and": [
                            {"user_id": {"$eq": user_id}},
                            {"source":  {"$eq": source}},
                        ]}
                    )
                    parent = source.replace("_summary", "")
                    counts[parent] = counts.get(parent, 0) + len(res["ids"])
                except Exception:
                    pass
        except Exception:
            pass
        return counts
