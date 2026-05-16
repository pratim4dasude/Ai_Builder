from typing import Dict, List, Any


class SessionMemory:
    def __init__(self):
        self.store: Dict[str, List[Dict[str, Any]]] = {}

    def add_run(self, session_id: str, run_data: Dict[str, Any]):
        if not session_id:
            return

        if session_id not in self.store:
            self.store[session_id] = []

        self.store[session_id].append(run_data)

    def get_history(self, session_id: str):
        if not session_id:
            return []

        return self.store.get(session_id, [])

    def get_last_run(self, session_id: str):
        history = self.get_history(session_id)

        if not history:
            return None

        return history[-1]


session_memory = SessionMemory()