from collections import defaultdict
from typing import Dict, List


class SessionMemory:
    def __init__(self):
        self.memory: Dict[str, List[dict]] = defaultdict(list)

    def add(self, session_id: str, role: str, content: str):
        self.memory[session_id].append({
            "role": role,
            "content": content,
        })

    def get(self, session_id: str) -> List[dict]:
        return self.memory.get(session_id, [])

    def clear(self, session_id: str):
        self.memory.pop(session_id, None)


session_memory = SessionMemory()