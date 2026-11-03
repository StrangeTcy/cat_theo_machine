"""Session store: recordings of observed Machine runs, as JSON files.

A session file is self-contained: metadata plus the event sequence, beginning
with a checkpoint of the state that existed when recording started. Replaying it
needs no Machine process, no journal and no server-side state.
"""
import json
import os
import time

from .protocol import SESSION_FORMAT, SESSION_VERSION


def _safe_name(name):
    cleaned = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in str(name))
    cleaned = cleaned.strip("-.")
    return cleaned[:80] or "session"


class SessionStore:
    def __init__(self, root):
        self.root = root
        os.makedirs(self.root, exist_ok=True)

    def _path(self, session_id):
        return os.path.join(self.root, _safe_name(session_id) + ".json")

    def new_id(self, name=None):
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        return _safe_name(name) + "-" + stamp if name else "session-" + stamp

    def save(self, session_id, meta, events):
        document = {
            "format": SESSION_FORMAT,
            "version": SESSION_VERSION,
            "meta": meta,
            "events": events,
        }
        path = self._path(session_id)
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(document, handle, separators=(",", ":"))
        os.replace(temporary, path)
        return path

    def load(self, session_id):
        with open(self._path(session_id), encoding="utf-8") as handle:
            document = json.load(handle)
        if document.get("format") != SESSION_FORMAT:
            raise ValueError("not a visualiser session file: " + session_id)
        return document

    def delete(self, session_id):
        path = self._path(session_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def listing(self):
        out = []
        for entry in sorted(os.listdir(self.root)):
            if not entry.endswith(".json"):
                continue
            session_id = entry[: -len(".json")]
            path = os.path.join(self.root, entry)
            try:
                with open(path, encoding="utf-8") as handle:
                    document = json.load(handle)
                meta = document.get("meta") or {}
                out.append(
                    {
                        "id": session_id,
                        "bytes": os.path.getsize(path),
                        "modified": os.path.getmtime(path),
                        "events": len(document.get("events") or []),
                        "format": document.get("format"),
                        "meta": meta,
                    }
                )
            except (OSError, ValueError):
                out.append(
                    {
                        "id": session_id,
                        "bytes": os.path.getsize(path),
                        "modified": os.path.getmtime(path),
                        "events": 0,
                        "error": "unreadable session file",
                    }
                )
        out.sort(key=lambda item: item.get("modified") or 0, reverse=True)
        return out
