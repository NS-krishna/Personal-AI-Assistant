"""
episodic_memory.py — Raw conversation history storage.

Stores timestamped user↔assistant exchanges in ChromaDB
for retrieval-augmented context in future conversations.
Uses ChromaDB's built-in default embedding function.
"""

import uuid
from datetime import datetime

import chromadb

from config import settings


class EpisodicMemory:
    """Stores and retrieves raw conversation history."""

    def __init__(self, persist_dir: str = None):
        path = persist_dir or settings.CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="episodic_memory",
            metadata={"description": "Timestamped conversation history"},
        )

    def add(self, user_message: str, ai_reply: str) -> str:
        """
        Store a single conversation turn.

        Args:
            user_message: What the user said.
            ai_reply: What the assistant replied.

        Returns:
            The generated document ID.
        """
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        document = f"User: {user_message}\nAssistant: {ai_reply}"

        self.collection.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[{
                "user_message": user_message,
                "ai_reply": ai_reply,
                "timestamp": timestamp,
            }],
        )
        return doc_id

    def get_recent(self, k: int = 5) -> list[dict]:
        """
        Retrieve the K most recent interactions (chronological).

        Args:
            k: Number of recent interactions to return.

        Returns:
            List of dicts with keys: user_message, ai_reply, timestamp
        """
        results = self.collection.get(
            limit=k,
            include=["metadatas", "documents"],
        )

        interactions = []
        for meta in (results.get("metadatas") or []):
            interactions.append({
                "user_message": meta.get("user_message", ""),
                "ai_reply": meta.get("ai_reply", ""),
                "timestamp": meta.get("timestamp", ""),
            })

        # Sort by timestamp descending (most recent first)
        interactions.sort(key=lambda x: x["timestamp"], reverse=True)
        return interactions[:k]

    def search(self, query: str, k: int = 3) -> list[dict]:
        """
        Semantic search over past conversations.

        Args:
            query: Search query text.
            k: Number of results to return.

        Returns:
            List of dicts with keys: user_message, ai_reply, timestamp, score
        """
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(k, count),
            include=["metadatas", "distances"],
        )

        matches = []
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for meta, dist in zip(metadatas, distances):
            matches.append({
                "user_message": meta.get("user_message", ""),
                "ai_reply": meta.get("ai_reply", ""),
                "timestamp": meta.get("timestamp", ""),
                "score": round(1 - dist, 4),  # convert distance to similarity
            })
        return matches

    def clear(self):
        """Delete all stored episodes."""
        self.client.delete_collection("episodic_memory")
        self.collection = self.client.get_or_create_collection(
            name="episodic_memory",
            metadata={"description": "Timestamped conversation history"},
        )
