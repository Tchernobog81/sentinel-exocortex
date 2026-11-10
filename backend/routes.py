"""
API routes for Cortex Loom backend.

POST /api/data est idempotent : upsert par id stable (pas d'insert aveugle).
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import Event, EventList
from .storage import get_storage, BaseStorage
import os

router = APIRouter()

# Dependency to get storage
async def get_storage_dependency() -> BaseStorage:
    storage_type = os.environ.get("STORAGE_TYPE", "json")
    storage_path = os.environ.get("STORAGE_PATH", "loom_data.json")
    return get_storage(storage_type, file_path=storage_path if storage_type == "json" else None)


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    if not since:
        return None
    try:
        return datetime.fromisoformat(since)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Paramètre 'since' invalide (ISO 8601 attendu): {since!r}")


@router.get("/data", response_model=List[Dict[str, Any]])
async def get_data(
    since: Optional[str] = None,
    storage: BaseStorage = Depends(get_storage_dependency)
):
    """Get all events (format aplati, compatible front), optionnellement filtrés par timestamp >= since"""
    try:
        events = storage.load()
        cutoff = _parse_since(since)
        if cutoff:
            events = [e for e in events if e.timestamp and datetime.fromisoformat(e.timestamp) >= cutoff]
        return [e.to_dict() for e in events]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/recent", response_model=List[Dict[str, Any]])
async def get_recent_data(
    hours: int = 12,
    storage: BaseStorage = Depends(get_storage_dependency)
):
    """Get recent events (default: last 12 hours), format aplati"""
    try:
        return [e.to_dict() for e in storage.get_recent(hours=hours)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data", response_model=dict)
async def add_data(
    events: List[Event],
    storage: BaseStorage = Depends(get_storage_dependency)
):
    """Ajoute ou met à jour des événements (upsert idempotent par id stable)"""
    try:
        for event in events:
            if not event.timestamp:
                event.timestamp = datetime.now().isoformat()
            event.ensure_id()
        added, updated = storage.upsert_events(events)
        total = len(storage.load())
        return {
            "status": "ok",
            "items": added,            # compat réponse ancienne
            "items_added": added,
            "items_updated": updated,
            "total_events": total,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/data/stats", response_model=dict)
async def get_stats(storage: BaseStorage = Depends(get_storage_dependency)):
    """Get statistics about the data"""
    try:
        events = storage.load()
        if not events:
            return {"total": 0, "categories": {}, "years": {}}

        categories = {}
        for event in events:
            cat = event.category
            categories[cat] = categories.get(cat, 0) + 1

        years = [e.year for e in events]
        year_range = {"min": min(years), "max": max(years), "span": max(years) - min(years)}
        tipping_count = sum(1 for e in events if e.tipping)

        return {
            "total_events": len(events),
            "categories": categories,
            "years": year_range,
            "tipping_points": tipping_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups", response_model=List[dict])
async def list_backups(storage: BaseStorage = Depends(get_storage_dependency)):
    """Liste les sauvegardes disponibles (plus récentes d'abord)"""
    try:
        return storage.list_backups()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups/{name}/restore", response_model=dict)
async def restore_backup(name: str, storage: BaseStorage = Depends(get_storage_dependency)):
    """Restaure une sauvegarde par nom (l'état courant est lui-même sauvegardé avant)"""
    try:
        storage.restore_backup(name)
        return {"status": "ok", "restored": name, "total_events": len(storage.load())}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
