#!/bin/bash
# Boucle agent Sentinel : scrute le net toutes les ~60 s (analyse LLM local, focus AI2027)
# et push les nouveaux événements sur GitHub (main) → la page GitHub Pages se met à jour.
# Usage : ./scripts/run_push_agent.sh   (arrêt : Ctrl+C)
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOCKDIR="$ROOT/.push_agent.lockdir"
if ! mkdir "$LOCKDIR" 2>/dev/null; then echo "Une instance tourne déjà."; exit 0; fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

PY="$ROOT/backend/venv/bin/python"
[ -x "$PY" ] || PY="python3"

GIT_AUTHOR_NAME="Tchernobog81" GIT_AUTHOR_EMAIL="tcherno@tuta.io" \
GIT_COMMITTER_NAME="Tchernobog81" GIT_COMMITTER_EMAIL="tcherno@tuta.io" \
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL

echo "[$(date +%H:%M:%S)] Démarrage boucle push agent (sentinel v171, intervalle ~60s)"

while true; do
  # export statique V2 (telemetry.json + rag.json pour GitHub Pages)
  node v2/server/export-static.mjs >> "$ROOT/sentinel_push.log" 2>&1 || true
  BEFORE=$(cat loom_data.json telemetry.json rag.json scan_heartbeat.json 2>/dev/null | git hash-object --stdin 2>/dev/null || echo none)
  echo "[$(date +%H:%M:%S)] Cycle sentinel..."
  (cd sentinel && BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000/api/data}" ANALYSIS_MODE=llm "$PY" sentinel.py >> "$ROOT/sentinel_push.log" 2>&1)
  AFTER=$(cat loom_data.json telemetry.json rag.json scan_heartbeat.json 2>/dev/null | git hash-object --stdin 2>/dev/null || echo none)
  if [ "$BEFORE" != "$AFTER" ]; then
    git add loom_data.json telemetry.json rag.json scan_heartbeat.json
    if git commit -q -m "🤖 Auto-update loom data (sentinel v171, $(date '+%Y-%m-%d %H:%M'))"; then
      if git push origin main; then
        echo "[$(date +%H:%M:%S)] ✅ push OK (nouveaux événements publiés)"
      else
        echo "[$(date +%H:%M:%S)] ⚠️ push FAILED (vérifier l'auth git/SSH)"
      fi
    fi
  else
    echo "[$(date +%H:%M:%S)] Aucun nouvel événement."
  fi
  sleep 300
done
