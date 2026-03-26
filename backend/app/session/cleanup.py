"""Background task to clean up expired sessions."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.config import CHROMA_PERSIST_DIR, SESSION_TTL_HOURS
from app.rag.vectorstore import delete_collection
from app.session.manager import get_session_manager

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 3600  # 1 hour


async def cleanup_expired_sessions():
    """Periodically delete expired sessions and their Chroma collections."""
    while True:
        try:
            mgr = get_session_manager()
            expired = mgr.list_expired(SESSION_TTL_HOURS)

            for session in expired:
                logger.info(f"Cleaning up expired session {session.id}")
                try:
                    delete_collection(session.collection_name)
                except Exception as e:
                    logger.warning(f"Failed to delete collection {session.collection_name}: {e}")

                # Clean up uploaded files directory
                upload_dir = Path(CHROMA_PERSIST_DIR) / "uploads" / session.id
                if upload_dir.exists():
                    import shutil
                    shutil.rmtree(upload_dir, ignore_errors=True)

                mgr.delete_session(session.id)

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

        await asyncio.sleep(CLEANUP_INTERVAL)
