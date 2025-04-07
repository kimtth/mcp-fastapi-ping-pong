# Session manager class to handle thread-safe session operations
import threading
import uuid


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def get_or_create(self, session_id=None):
        with self.lock:
            if session_id is None:
                session_id = str(uuid.uuid4())

            if session_id not in self.sessions:
                self.sessions[session_id] = 0

            return session_id

    def increment(self, session_id):
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id] += 1
            return self.sessions.get(session_id, 0)

    def get_count(self, session_id):
        with self.lock:
            return self.sessions.get(session_id, 0)