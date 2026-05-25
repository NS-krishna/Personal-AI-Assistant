"""
memory_manager.py — Orchestrates both memory layers.

Provides a unified interface to:
    - Store interactions in episodic memory
    - Store learned facts in semantic memory
    - Build combined context for the agent from both layers
"""

from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from config import settings


class MemoryManager:
    """Unified memory orchestrator across episodic and semantic layers."""

    def __init__(self, persist_dir: str = None):
        path = persist_dir or settings.CHROMA_PERSIST_DIR
        self.episodic = EpisodicMemory(persist_dir=path)
        self.semantic = SemanticMemory(persist_dir=path)

    def save_interaction(self, user_message: str, ai_reply: str) -> str:
        """
        Store a conversation turn in episodic memory.

        Args:
            user_message: What the user said.
            ai_reply: What the assistant replied.

        Returns:
            The generated document ID.
        """
        return self.episodic.add(user_message, ai_reply)

    def add_fact(self, fact: str, category: str = "general") -> str:
        """
        Store a learned fact in semantic memory.

        Args:
            fact: The fact text.
            category: Category tag.

        Returns:
            The generated fact ID.
        """
        return self.semantic.add_fact(fact, category=category)

    def get_context(self, query: str, max_episodes: int = 5, max_facts: int = 3) -> str:
        """
        Build a context string for the agent by combining
        relevant conversation episodes and semantic facts.

        Args:
            query: Current user query.
            max_episodes: Number of past conversations to include.
            max_facts: Number of semantic facts to include.

        Returns:
            Formatted context string for LLM prompt injection.
        """
        parts = []

        # --- Episodic context ---
        episodes = self.episodic.search(query, k=max_episodes)
        if episodes:
            parts.append("=== Relevant Past Conversations ===")
            for ep in episodes:
                parts.append(
                    f"[{ep['timestamp']}]\n"
                    f"  User: {ep['user_message']}\n"
                    f"  Assistant: {ep['ai_reply']}"
                )

        # --- Semantic context ---
        facts = self.semantic.search_facts(query, k=max_facts)
        if facts:
            parts.append("\n=== Known Facts About the User ===")
            for f in facts:
                parts.append(f"- {f['fact']}")

        if not parts:
            return "(No relevant memory found)"

        return "\n".join(parts)

    def get_all_facts(self) -> list[dict]:
        """Return all stored semantic facts."""
        return self.semantic.get_all_facts()

    def get_recent_conversations(self, k: int = 5) -> list[dict]:
        """Return the K most recent conversation turns."""
        return self.episodic.get_recent(k)

    def clear_all(self):
        """Delete all episodic and semantic memory."""
        self.episodic.clear()
        self.semantic.clear()
