#!/bin/bash
# Boucle agent Sentinel : scrute le net toutes les ~5 min (analyse LLM local, focus AI2027)
# et push les nouveaux événements sur GitHub (main) → la page GitHub Pages se met à jour.
# Usage : ./scripts/run_push_agent.sh   (arrêt : Ctrl+C)
# Lancé aussi en launchd (com.tcherno.sentinel-push-agent, KeepAlive) : le push ne dépend
# plus d'une session interactive (SSH : bloc Host github.com épinglé dans ~/.ssh/config,
# clé sans passphrase, IdentitiesOnly — aucun besoin de SSH_AUTH_SOCK).
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOCKDIR="$ROOT/.push_agent.lockdir"
AGENT_LOG="$ROOT/push_agent.log"

# --- lock anti-instance, résistant aux kill -9 (le pid est vérifié) ---
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  oldpid=$(cat "$LOCKDIR/pid" 2>/dev/null)
  if [ -n "$oldpid" ] && kill -0 "$oldpid" 2>/dev/null; then
    echo "Une instance tourne déjà (pid $oldpid)."
    exit 0
  fi
  # lock périmé (processus mort) : on le remplace
  rm -rf "$LOCKDIR" 2>/dev/null
  mkdir "$LOCKDIR" 2>/dev/null || { echo "Impossible de prendre le lock."; exit 1; }
fi
echo $$ > "$LOCKDIR/pid"
trap 'rm -rf "$LOCKDIR" 2>/dev/null' EXIT

PY="$ROOT/backend/venv/bin/python"
[ -x "$PY" ] || PY="python3"

# jamais de prompt interactif (launchd n'a pas de TTY) : un push qui demanderait
# des credentials échoue proprement au lieu de bloquer la boucle
GIT_TERMINAL_PROMPT=0
export GIT_TERMINAL_PROMPT
GIT_AUTHOR_NAME="Tchernobog81" GIT_AUTHOR_EMAIL="tcherno@tuta.io" \
GIT_COMMITTER_NAME="Tchernobog81" GIT_COMMITTER_EMAIL="tcherno@tuta.io" \
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$AGENT_LOG"; }

# push robuste : en cas de non-fast-forward (quelqu'un a pushé depuis ailleurs),
# on fetch + rebase puis on re-push, au lieu d'échouer en boucle
push_main() {
  if git push origin main >>"$AGENT_LOG" 2>&1; then
    log "✅ push OK (nouveaux événements publiés)"
    return 0
  fi
  log "⚠️ push FAILED — fetch + rebase + re-push"
  git fetch origin >>"$AGENT_LOG" 2>&1 || true
  if git rebase origin/main >>"$AGENT_LOG" 2>&1 && git push origin main >>"$AGENT_LOG" 2>&1; then
    log "✅ push OK après rebase"
    return 0
  fi
  log "❌ push toujours en échec — voir $AGENT_LOG (auth SSH ? branche protégée ?)"
  return 1
}

log "Démarrage boucle push agent (sentinel, intervalle ~300s)"

while true; do
  # export statique V2 (telemetry.json + rag.json pour GitHub Pages)
  node v2/server/export-static.mjs >> "$ROOT/sentinel_push.log" 2>&1 || true
  BEFORE=$(cat loom_data.json telemetry.json rag.json scan_heartbeat.json v2/web/public/loom_data.json 2>/dev/null | git hash-object --stdin 2>/dev/null || echo none)
  log "Cycle sentinel..."
  (cd sentinel && BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000/api/data}" ANALYSIS_MODE=llm "$PY" sentinel.py >> "$ROOT/sentinel_push.log" 2>&1) || true
  # V2.9 : régénère l'export lissé loom_data.json depuis loom.db (bucketing horloge 1/jour + EMA + raw)
  node db/export_snapshot.js >> "$ROOT/sentinel_push.log" 2>&1 || true
  AFTER=$(cat loom_data.json telemetry.json rag.json scan_heartbeat.json v2/web/public/loom_data.json 2>/dev/null | git hash-object --stdin 2>/dev/null || echo none)
  if [ "$BEFORE" != "$AFTER" ]; then
    git add loom_data.json telemetry.json rag.json scan_heartbeat.json v2/web/public/loom_data.json
    if git commit -q -m "🤖 Auto-update loom data (sentinel, $(date '+%Y-%m-%d %H:%M'))"; then
      push_main
    fi
  else
    log "Aucun nouvel événement."
  fi
  sleep 300
done
