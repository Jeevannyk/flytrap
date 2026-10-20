"""SQLite store for sessions and a per-session SHA-256 hash-chained event log."""
import hashlib
import json
import sqlite3
import threading
import time

GENESIS = "0" * 64


def _digest(prev, session_id, idx, ts, etype, payload_json):
    raw = "|".join([prev, session_id, str(idx), repr(ts), etype, payload_json])
    return hashlib.sha256(raw.encode()).hexdigest()


class Store:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions(
                id TEXT PRIMARY KEY, scenario TEXT, protected INTEGER,
                status TEXT, created REAL);
            CREATE TABLE IF NOT EXISTS events(
                session_id TEXT, idx INTEGER, ts REAL, type TEXT, payload TEXT,
                prev_hash TEXT, hash TEXT, PRIMARY KEY(session_id, idx));
            """
        )

    def create_session(self, session_id, scenario, protected):
        with self.lock:
            self.db.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?)",
                (session_id, scenario, int(protected), "active", time.time()),
            )
            self.db.commit()

    def set_status(self, session_id, status):
        with self.lock:
            self.db.execute("UPDATE sessions SET status=? WHERE id=?", (status, session_id))
            self.db.commit()

    def get_session(self, session_id):
        row = self.db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None

    def list_sessions(self):
        rows = self.db.execute("SELECT * FROM sessions ORDER BY created DESC").fetchall()
        return [dict(r) for r in rows]

    def append(self, session_id, etype, payload):
        with self.lock:
            last = self.db.execute(
                "SELECT idx, hash FROM events WHERE session_id=? ORDER BY idx DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            idx = last["idx"] + 1 if last else 0
            prev = last["hash"] if last else GENESIS
            ts = time.time()
            payload_json = json.dumps(payload, sort_keys=True)
            h = _digest(prev, session_id, idx, ts, etype, payload_json)
            self.db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?)",
                (session_id, idx, ts, etype, payload_json, prev, h),
            )
            self.db.commit()
            return {"idx": idx, "ts": ts, "type": etype, "payload": payload, "hash": h}

    def events(self, session_id):
        rows = self.db.execute(
            "SELECT * FROM events WHERE session_id=? ORDER BY idx", (session_id,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out

    def verify(self, session_id):
        """Recompute the chain. Detects edits to retained records, not deletion of the tail."""
        rows = self.db.execute(
            "SELECT * FROM events WHERE session_id=? ORDER BY idx", (session_id,)
        ).fetchall()
        prev = GENESIS
        for r in rows:
            expected = _digest(prev, r["session_id"], r["idx"], r["ts"], r["type"], r["payload"])
            if r["prev_hash"] != prev or r["hash"] != expected:
                return {"ok": False, "bad_index": r["idx"], "length": len(rows)}
            prev = r["hash"]
        return {"ok": True, "bad_index": None, "length": len(rows)}

    def tamper(self, session_id, idx):
        """Demo only: edit a stored record without fixing the hashes."""
        with self.lock:
            self.db.execute(
                "UPDATE events SET payload=? WHERE session_id=? AND idx=?",
                (json.dumps({"tampered": True}), session_id, idx),
            )
            self.db.commit()
