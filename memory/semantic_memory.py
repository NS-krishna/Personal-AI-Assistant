"""
semantic_memory.py — Learned facts and user preferences.

Stores distilled knowledge extracted from conversations:
    - User preferences ("I prefer morning meetings")
    - Recurring contacts ("Rahul is my project partner")
    - Learned facts ("My timezone is IST")

Uses ChromaDB's built-in default embedding function.
"""

import uuid
from datetime import datetime

import chromadb

from config import settings


class SemanticMemory:
    """Stores and retrieves learned facts about the user."""

    def __init__(self, persist_dir: str = None):
        path = persist_dir or settings.CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="semantic_memory",
            metadata={"description": "Learned facts about the user"},
        )

    def add_fact(self, fact: str, category: str = "general") -> str:
        """
        Store a learned fact.

        Args:
            fact: The fact text (e.g., "User prefers morning meetings").
            category: Category tag (e.g., "preference", "contact", "schedule").

        Returns:
            The generated fact ID.
        """
        fact_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        self.collection.add(
            ids=[fact_id],
            documents=[fact],
            metadatas=[{
                "fact": fact,
                "category": category,
                "timestamp": timestamp,
            }],
        )
        return fact_id

    def get_all_facts(self) -> list[dict]:
        """
        Retrieve all stored facts.

        Returns:
            List of dicts with keys: fact, category, timestamp
        """
        results = self.collection.get(include=["metadatas", "documents"])
        facts = []
        for meta in (results.get("metadatas") or []):
            facts.append({
                "fact": meta.get("fact", ""),
                "category": meta.get("category", "general"),
                "timestamp": meta.get("timestamp", ""),
            })
        return facts

    def search_facts(self, query: str, k: int = 3) -> list[dict]:
        """
        Find facts relevant to a query via semantic search.

        Args:
            query: Search query text.
            k: Number of results to return.

        Returns:
            List of dicts with keys: fact, category, timestamp, score
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
                "fact": meta.get("fact", ""),
                "category": meta.get("category", "general"),
                "timestamp": meta.get("timestamp", ""),
                "score": round(1 - dist, 4),
            })
        return matches

    def clear(self):
        """Delete all stored facts."""
        self.client.delete_collection("semantic_memory")
        self.collection = self.client.get_or_create_collection(
            name="semantic_memory",
            metadata={"description": "Learned facts about the user"},
        )

    def delete_fact(self, fact_text: str):
        """Delete a specific fact by text."""
        results = self.collection.get()
        for i, doc in enumerate(results.get("documents", [])):
            if fact_text in doc:
                self.collection.delete(ids=[results["ids"][i]])
