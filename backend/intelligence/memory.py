import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any

class EpisodicMemory:
    """Persistent local episodic memory allowing Stacky to recall facts, contacts, and discussions."""
    
    def __init__(self, db_path: str = None):
        if not db_path:
            # Store in project workspace directory for safe sandboxed read/write
            base_dir = Path(__file__).resolve().parent.parent.parent
            db_path = str(base_dir / "stacky_memory.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    key_entity TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM memories")
            if cur.fetchone()[0] == 0:
                conn.executemany("""
                    INSERT INTO memories (category, key_entity, content) VALUES (?, ?, ?)
                """, [
                    ("recommendation", "restaurant", "Alex recommended 'Trattoria Bella' on 3rd Avenue for authentic pasta via WhatsApp."),
                    ("finance", "accountant", "Accountant advised holding 28% for quarterly tax deductions and saving hardware equipment receipts."),
                    ("preferences", "work_style", "Prefers morning focus sessions without meetings before 11:00 AM.")
                ])

    def store_memory(self, category: str, key_entity: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memories (category, key_entity, content) VALUES (?, ?, ?)",
                (category, key_entity, content)
            )

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        query_words = [f"%{w}%" for w in query.lower().split() if len(w) > 2]
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            results = []
            for qw in query_words:
                cur.execute(
                    "SELECT category, key_entity, content, created_at FROM memories WHERE content LIKE ? OR key_entity LIKE ?",
                    (qw, qw)
                )
                for row in cur.fetchall():
                    results.append(dict(row))
            seen = set()
            deduped = []
            for r in results:
                if r["content"] not in seen:
                    seen.add(r["content"])
                    deduped.append(r)
            return deduped if deduped else [{"content": f"No previous records matching '{query}' found in episodic archives, Sir."}]
