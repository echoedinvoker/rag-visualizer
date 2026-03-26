"""Session lifecycle management with SQLite persistence."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.config import CHROMA_PERSIST_DIR


@dataclass
class Session:
    id: str
    created_at: datetime
    collection_name: str
    files: list[dict] = field(default_factory=list)  # [{id, name, size, uploaded_at}]


class SessionManager:
    """Manages session state in SQLite + in-memory cache."""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or str(Path(CHROMA_PERSIST_DIR) / "sessions.db")
        self._cache: dict[str, Session] = {}
        self._lock = Lock()
        self._init_db()
        self._load_cache()

    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    collection_name TEXT NOT NULL,
                    files TEXT NOT NULL DEFAULT '[]'
                )
            """)
            conn.commit()

    def _load_cache(self):
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT id, created_at, collection_name, files FROM sessions").fetchall()
        for row in rows:
            sid, created_str, collection, files_json = row
            self._cache[sid] = Session(
                id=sid,
                created_at=datetime.fromisoformat(created_str),
                collection_name=collection,
                files=json.loads(files_json),
            )

    def create_session(self) -> Session:
        sid = uuid.uuid4().hex[:12]
        collection_name = f"session_{sid}"
        now = datetime.now(timezone.utc)

        session = Session(id=sid, created_at=now, collection_name=collection_name)

        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO sessions (id, created_at, collection_name, files) VALUES (?, ?, ?, ?)",
                    (sid, now.isoformat(), collection_name, "[]"),
                )
                conn.commit()
            self._cache[sid] = session

        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._cache.get(session_id)

    def add_file(self, session_id: str, file_info: dict):
        with self._lock:
            session = self._cache.get(session_id)
            if not session:
                return
            session.files.append(file_info)
            files_json = json.dumps(session.files)
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("UPDATE sessions SET files = ? WHERE id = ?", (files_json, session_id))
                conn.commit()

    def remove_file(self, session_id: str, file_id: str):
        with self._lock:
            session = self._cache.get(session_id)
            if not session:
                return
            session.files = [f for f in session.files if f.get("id") != file_id]
            files_json = json.dumps(session.files)
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("UPDATE sessions SET files = ? WHERE id = ?", (files_json, session_id))
                conn.commit()

    def delete_session(self, session_id: str):
        with self._lock:
            self._cache.pop(session_id, None)
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                conn.commit()

    def list_expired(self, ttl_hours: int) -> list[Session]:
        now = datetime.now(timezone.utc)
        expired = []
        for session in self._cache.values():
            age_hours = (now - session.created_at).total_seconds() / 3600
            if age_hours > ttl_hours:
                expired.append(session)
        return expired

    def all_sessions(self) -> list[Session]:
        return list(self._cache.values())


# Singleton
_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
