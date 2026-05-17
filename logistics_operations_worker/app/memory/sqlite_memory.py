import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List


class SQLiteConversationMemory:
    def __init__(self, db_path: str = "logistics_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_context (
            session_id TEXT PRIMARY KEY,
            context_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, message: Any):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (session_id, role, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                json.dumps(message, default=str),
                datetime.utcnow().isoformat(),
            )
        )

        conn.commit()
        conn.close()

    def get_history(self, session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, message, created_at
            FROM conversations
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit)
        )

        rows = cursor.fetchall()
        conn.close()

        history = []

        for role, message, created_at in reversed(rows):
            try:
                parsed_message = json.loads(message)
            except Exception:
                parsed_message = message

            history.append({
                "role": role,
                "message": parsed_message,
                "created_at": created_at,
            })

        return history

    def get_context(self, session_id: str) -> Dict[str, Any]:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT context_json
            FROM session_context
            WHERE session_id = ?
            """,
            (session_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {}

        try:
            return json.loads(row[0])
        except Exception:
            return {}

    def update_context(self, session_id: str, context: Dict[str, Any]):
        old_context = self.get_context(session_id)

        old_context.update({
            key: value
            for key, value in context.items()
            if value is not None
        })

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO session_context (session_id, context_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id)
            DO UPDATE SET
                context_json = excluded.context_json,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                json.dumps(old_context, default=str),
                datetime.utcnow().isoformat(),
            )
        )

        conn.commit()
        conn.close()

    def clear_session(self, session_id: str):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM session_context WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()