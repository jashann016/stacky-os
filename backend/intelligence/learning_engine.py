import json
import logging
import sqlite3
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.intelligence.memory import EpisodicMemory

logger = logging.getLogger("LearningEngine")

PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "user_profile.json"

class SelfEvolvingMemoryEngine:
    """Continuous self-learning engine that adapts Stacky to the user over time."""

    def __init__(self):
        self.memory = EpisodicMemory()
        self._ensure_evolution_table()

    def _ensure_evolution_table(self):
        with sqlite3.connect(self.memory.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    insight TEXT,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def analyze_and_learn(self, user_text: str) -> Optional[Dict[str, Any]]:
        """Extract habits, tone preferences, college/work facts, or explicit instructions from user speech/text."""
        text_lower = user_text.lower().strip()
        learned_item = None

        # 1. Explicit preference cues ("I prefer", "I like", "From now on", "Always", "Never", "Don't")
        if any(p in text_lower for p in ["i prefer", "i like", "always use", "from now on", "don't ever", "never use", "remember that"]):
            insight = user_text
            topic = "preference"
            if "email" in text_lower or "reply" in text_lower:
                topic = "email_style"
            elif "code" in text_lower or "programming" in text_lower or "python" in text_lower or "swift" in text_lower:
                topic = "coding_preference"
            elif "meeting" in text_lower or "calendar" in text_lower:
                topic = "schedule_habit"
            
            self._save_pattern(topic, insight, source="explicit_user_statement")
            self.memory.store_memory("preference", topic, insight)
            self._sync_profile_evolution(topic, insight)
            learned_item = {"type": topic, "insight": insight}

        # 2. College / Project / Routine cues ("My class", "My assignment", "Professor", "Lab", "Semester", "Project")
        elif any(c in text_lower for c in ["professor", "assignment", "deadline", "semester", "exam", "college", "lab report", "project"]):
            topic = "college_and_projects"
            insight = user_text
            self._save_pattern(topic, insight, source="contextual_statement")
            self.memory.store_memory("context", "college_project", insight)
            self._sync_profile_evolution(topic, insight)
            learned_item = {"type": topic, "insight": insight}

        # 3. People & Relationships ("is my friend", "my teammate", "my partner", "my brother")
        elif any(r in text_lower for r in ["my friend", "my teammate", "my partner", "my brother", "my colleague"]):
            topic = "relationship_network"
            insight = user_text
            self._save_pattern(topic, insight, source="social_context")
            self.memory.store_memory("relationship", "contact", insight)
            learned_item = {"type": topic, "insight": insight}

        return learned_item

    def _save_pattern(self, topic: str, insight: str, source: str = "conversation"):
        with sqlite3.connect(self.memory.db_path) as conn:
            conn.execute(
                "INSERT INTO learned_patterns (topic, insight, source) VALUES (?, ?, ?)",
                (topic, insight, source)
            )
        logger.info(f"[Self-Evolution Engine]: Learned new user insight [{topic}]: '{insight}'")

    def _sync_profile_evolution(self, key: str, value: str):
        """Persist newly adapted learning into user_profile.json."""
        try:
            if PROFILE_PATH.exists():
                data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                if "evolved_learnings" not in data:
                    data["evolved_learnings"] = []
                
                # Append if not duplicate
                if value not in data["evolved_learnings"]:
                    data["evolved_learnings"].append(value)
                    PROFILE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to sync evolution to profile: {e}")

    def get_learned_insights(self) -> List[Dict[str, Any]]:
        """Retrieve all accumulated knowledge about the user."""
        with sqlite3.connect(self.memory.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT topic, insight, source, created_at FROM learned_patterns ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

learning_engine = SelfEvolvingMemoryEngine()
