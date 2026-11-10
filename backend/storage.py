"""
Storage backends for Cortex Loom.
Supports JSON files and SQLite.

Sûr pour la concurrence (multi-workers gunicorn / processus externes) :
- verrou fichier (fcntl.flock) autour de tout read-modify-write
- écriture atomique (tmp + os.replace)
- backup automatique avant chaque écriture (garde MAX_BACKUPS derniers)
- upsert par id stable (idempotent)
"""
import fcntl
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from .models import Event, compute_event_id

BACKUP_DIR_NAME = "loom_backups"
MAX_BACKUPS = 10


def _lockfile_path(file_path: Path) -> Path:
    return Path(str(file_path) + ".lock")


@contextmanager
def file_lock(file_path: Path, exclusive: bool = True):
    """Verrou fichier multi-processus autour de file_path."""
    lock_path = _lockfile_path(file_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _prune_backups(backup_dir: Path, keep: int = MAX_BACKUPS):
    files = sorted(backup_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        old.unlink(missing_ok=True)


def _make_backup(file_path: Path, backup_dir: Path) -> Optional[Path]:
    if not file_path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    dest = backup_dir / f"{file_path.stem}_{ts}{file_path.suffix}"
    shutil.copy2(file_path, dest)
    _prune_backups(backup_dir, MAX_BACKUPS)
    return dest


class BaseStorage:
    """Abstract base class for storage backends"""

    def load(self) -> List[Event]:
        """Load all events"""
        raise NotImplementedError

    def save(self, events: List[Event]) -> bool:
        """Save all events (replaces existing)"""
        raise NotImplementedError

    def upsert_events(self, events: List[Event]) -> Tuple[int, int]:
        """Ajoute ou met à jour des événements (idempotent par id).

        Retourne (nb_ajouts, nb_mises_a_jour).
        """
        existing = self.load()
        index = {}
        for e in existing:
            e.ensure_id()
            index[e.id] = e
        added = updated = 0
        for ev in events:
            ev.ensure_id()
            if ev.id in index:
                index[ev.id] = ev  # remplacement complet (update)
                updated += 1
            else:
                index[ev.id] = ev
                added += 1
        self.save(list(index.values()))
        return added, updated

    # --- compat ancienne API ---
    def add_event(self, event: Event) -> bool:
        self.upsert_events([event])
        return True

    def add_events(self, events: List[Event]) -> bool:
        self.upsert_events(events)
        return True

    def get_recent(self, hours: int = 12) -> List[Event]:
        """Get recent events"""
        from datetime import timedelta
        all_events = self.load()
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            e for e in all_events
            if e.timestamp and datetime.fromisoformat(e.timestamp) >= cutoff
        ]

    def list_backups(self) -> List[dict]:
        raise NotImplementedError

    def restore_backup(self, name: str) -> bool:
        raise NotImplementedError


class JSONStorage(BaseStorage):
    """JSON file storage backend (atomic + locked + backups)"""

    def __init__(self, file_path: str = "loom_data.json"):
        self.file_path = Path(file_path)
        if not self.file_path.is_absolute():
            # Résolu depuis la racine du projet (parent du package backend/)
            self.file_path = Path(__file__).resolve().parent.parent / self.file_path
        self.backup_dir = self.file_path.parent / BACKUP_DIR_NAME
        self._ensure_file()

    def _ensure_file(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps([], indent=2))

    def load(self) -> List[Event]:
        with file_lock(self.file_path, exclusive=False):
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        events = [Event.from_dict(item) for item in data]
        for e in events:
            e.ensure_id()
        return events

    def save(self, events: List[Event], backup: bool = True) -> bool:
        with file_lock(self.file_path, exclusive=True):
            if backup:
                _make_backup(self.file_path, self.backup_dir)
            sorted_events = sorted(events, key=lambda e: e.year)
            data = [event.to_dict() for event in sorted_events]
            # Écriture atomique : fichier temporaire dans le même répertoire + rename
            fd, tmp = tempfile.mkstemp(dir=self.file_path.parent, prefix=".loom_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp, self.file_path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        return True

    def list_backups(self) -> List[dict]:
        if not self.backup_dir.exists():
            return []
        out = []
        for p in sorted(self.backup_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            out.append({"name": p.name, "date": datetime.fromtimestamp(p.stat().st_mtime).isoformat(), "size": p.stat().st_size})
        return out

    def restore_backup(self, name: str) -> bool:
        name = Path(name).name  # protection contre les chemins relatifs (path traversal)
        src = self.backup_dir / name
        if not src.exists() or src.suffix != ".json":
            raise FileNotFoundError(f"Backup introuvable: {name}")
        with file_lock(self.file_path, exclusive=True):
            _make_backup(self.file_path, self.backup_dir)  # backup de l'état courant avant restore
            shutil.copy2(src, self.file_path)
        return True


class SQLiteStorage(BaseStorage):
    """SQLite storage backend (upsert par id)"""

    COLUMNS = [
        "year", "value", "label", "category", "whoWhat", "description", "url",
        "timestamp", "tipping", "s_curve_phase", "pharmakon_remedy_percent",
        "pharmakon_poison_percent", "convergences", "grand_filter_analysis", "final_note",
    ]

    def __init__(self, db_path: str = "loom.db"):
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = Path(__file__).resolve().parent.parent / self.db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                year REAL NOT NULL,
                value INTEGER NOT NULL,
                label TEXT NOT NULL,
                category TEXT NOT NULL,
                whoWhat TEXT,
                description TEXT,
                url TEXT,
                timestamp TEXT,
                tipping BOOLEAN DEFAULT FALSE,
                s_curve_phase INTEGER,
                pharmakon_remedy_percent INTEGER,
                pharmakon_poison_percent INTEGER,
                convergences TEXT,
                grand_filter_analysis TEXT,
                final_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration : ajout de la colonne id sur les anciennes bases
        cols = [r[1] for r in conn.execute("PRAGMA table_info(events)").fetchall()]
        if "id" not in cols:
            conn.execute("ALTER TABLE events ADD COLUMN id TEXT")
        conn.commit()
        conn.close()

    def _row_to_event(self, row) -> Event:
        event_data = dict(row)
        event_data.pop("created_at", None)
        return Event.from_dict(event_data)

    def _values(self, event: Event):
        a = event.analysis
        return (
            event.id, event.year, event.value, event.label, event.category,
            event.whoWhat, event.description, event.url, event.timestamp, event.tipping,
            a.s_curve_phase if a else None,
            a.remedy_percent if a else None,
            a.poison_percent if a else None,
            a.convergences if a else None,
            a.grand_filter_analysis if a else None,
            a.final_note if a else None,
        )

    def load(self) -> List[Event]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM events ORDER BY year").fetchall()
        conn.close()
        events = [self._row_to_event(r) for r in rows]
        for e in events:
            e.ensure_id()
        return events

    def save(self, events: List[Event], backup: bool = True) -> bool:
        # Sauvegarde du fichier db avant réécriture complète
        if backup and self.db_path.exists():
            self.backup_dir = self.db_path.parent / BACKUP_DIR_NAME
            _make_backup(self.db_path, self.backup_dir)
        conn = self._connect()
        with conn:
            conn.execute("DELETE FROM events")
            for event in events:
                event.ensure_id()
                cols = ", ".join(["id"] + self.COLUMNS)
                conn.execute(
                    f"INSERT INTO events ({cols}) VALUES ({', '.join(['?'] * (len(self.COLUMNS) + 1))})",
                    self._values(event),
                )
        conn.close()
        return True

    def upsert_events(self, events: List[Event]) -> Tuple[int, int]:
        conn = self._connect()
        added = updated = 0
        with conn:
            for event in events:
                event.ensure_id()
                cur = conn.execute("SELECT 1 FROM events WHERE id = ?", (event.id,)).fetchone()
                cols = ", ".join(["id"] + self.COLUMNS)
                if cur:
                    conn.execute(
                        f"INSERT OR REPLACE INTO events ({cols}) VALUES ({', '.join(['?'] * (len(self.COLUMNS) + 1))})",
                        self._values(event),
                    )
                    updated += 1
                else:
                    conn.execute(
                        f"INSERT INTO events ({cols}) VALUES ({', '.join(['?'] * (len(self.COLUMNS) + 1))})",
                        self._values(event),
                    )
                    added += 1
        conn.close()
        return added, updated

    def list_backups(self) -> List[dict]:
        backup_dir = self.db_path.parent / BACKUP_DIR_NAME
        if not backup_dir.exists():
            return []
        return [
            {"name": p.name, "date": datetime.fromtimestamp(p.stat().st_mtime).isoformat(), "size": p.stat().st_size}
            for p in sorted(backup_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        ]

    def restore_backup(self, name: str) -> bool:
        name = Path(name).name
        src = self.db_path.parent / BACKUP_DIR_NAME / name
        if not src.exists():
            raise FileNotFoundError(f"Backup introuvable: {name}")
        if self.db_path.exists():
            _make_backup(self.db_path, self.db_path.parent / BACKUP_DIR_NAME)
        shutil.copy2(src, self.db_path)
        return True


# Factory function
storage_factory = {
    "json": JSONStorage,
    "sqlite": SQLiteStorage,
}


def get_storage(storage_type: str = "json", **kwargs) -> BaseStorage:
    """Get storage backend by type"""
    storage_class = storage_factory.get(storage_type)
    if not storage_class:
        raise ValueError(f"Unknown storage type: {storage_type}")
    return storage_class(**kwargs)
