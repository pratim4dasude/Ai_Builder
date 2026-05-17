from typing import Dict, List, Any, Optional
from datetime import datetime


class ConversationMemoryService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "history": [],
                "last_context": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        return self.sessions[session_id]

    def add_user_message(self, session_id: str, message: str):
        session = self.get_session(session_id)
        session["history"].append({
            "role": "user",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session["updated_at"] = datetime.utcnow().isoformat()

    def add_assistant_message(self, session_id: str, message: Any):
        session = self.get_session(session_id)
        session["history"].append({
            "role": "assistant",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session["updated_at"] = datetime.utcnow().isoformat()

    def update_context(self, session_id: str, context: Dict[str, Any]):
        session = self.get_session(session_id)
        session["last_context"].update({
            k: v for k, v in context.items() if v is not None
        })
        session["updated_at"] = datetime.utcnow().isoformat()

    def get_context(self, session_id: str) -> Dict[str, Any]:
        return self.get_session(session_id).get("last_context", {})

    def get_history(self, session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        history = self.get_session(session_id).get("history", [])
        return history[-limit:]

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]