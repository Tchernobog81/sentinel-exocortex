# 🌐 Cortex Loom - Exocortex & Veille Technologique

**Version locale avec backend FastAPI - Indépendant de Google Apps Script**

---

## 🎯 Vision du Projet

**Cortex Loom** est un système de veille technologique conçu pour suivre et visualiser l'avènement des singularités technologiques. Il combine :
- **Collecte** automatisée d'événements historiques et actuels
- **Analyse** selon le framework **Pharmakon** (remède vs poison)
- **Visualisation** interactive via une timeline (Chart.js)

**Nouveauté** : Cette version est **100% indépendante de Google Apps Script** et utilise un backend FastAPI local qui peut tourner sur ton Mac M4.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE HYBRIDE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐ │
│  │ sentinel.py │────▶│ FastAPI     │     │ JSON/SQLite     │ │
│  │ (Scanners)   │     │ (Backend)    │────▶│ (Storage)       │ │
│  └─────────────┘     └─────────────┘     └─────────────────┘ │
│         ↑                    ↑                              │
│         │                    │                              │
│  ┌──────┴──────┐       ┌─────▼─────┐                         │
│  │ Scanners    │       │ index.html │ ◄──────────────────────┘ │
│  │ (RSS, etc.) │       │ (Frontend)  │                         │
│  └─────────────┘       └───────────┘                         │
│                                                               │
│                    ┌─────────────────────────┐                 │
│                    │ GitHub Actions           │                 │
│                    │ (Fallback automatique)  │                 │
│                    └─────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Structure du Projet

```
sentinel-exocortex/
├── backend/                  # Backend FastAPI
│   ├── main.py              # Application principale
│   ├── models.py            # Modèles Pydantic
│   ├── storage.py           # Stockage (JSON/SQLite)
│   ├── routes.py            # Routes API
│   └── requirements.txt     # Dépendances Python
│
├── sentinel/                # Agent de veille
│   ├── sentinel.py          # Scanners et logique métier
│   └── requirements.txt     # Dépendances Python
│
├── .github/
│   └── workflows/
│       └── update_data.yml   # Workflow GitHub Actions
│
├── scripts/                 # Scripts utilitaires
│   ├── run_backend.sh       # Lancer le backend
│   ├── run_sentinel.sh      # Lancer un cycle unique
│   └── run_continuous.sh    # Lancer en mode continu
│
├── index.html               # Frontend (Chart.js)
├── loom_data.json           # Données par défaut
├── .env.example             # Exemple de configuration
└── README.md                # Documentation
```

---

## 🚀 Installation et Démarrage

### 1️⃣ Prérequis

- **Python 3.10+** (recommandé : 3.11)
- **pip** (gestionnaire de paquets Python)
- **Git** (pour le versionnage)

### 2️⃣ Installation

```bash
# Cloner le dépôt (si ce n'est pas déjà fait)
git clone https://github.com/Tchernobog81/sentinel-exocortex.git
cd sentinel-exocortex

# Installer les dépendances du backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Installer les dépendances de sentinel
cd sentinel
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
cd ..
```

### 3️⃣ Configuration

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Édater .env selon tes besoins (optionnel)
nano .env
```

---

## 🎛️ Utilisation

### Lancer le Backend FastAPI

**Pour le développement (avec reload automatique) :**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Pour la production (avec Gunicorn) :**
```bash
# Donner les permissions au script
chmod +x scripts/run_backend.sh

# Lancer
./scripts/run_backend.sh
```

Le backend sera accessible à : **http://localhost:8000**
- API : `/api/data` (GET/POST)
- Docs : `/api/docs` (Swagger UI)
- Health : `/health`

### Lancer l'Agent Sentinel

**Cycle unique :**
```bash
chmod +x scripts/run_sentinel.sh
./scripts/run_sentinel.sh
```

**Mode continu (toutes les heures) :**
```bash
chmod +x scripts/run_continuous.sh
./scripts/run_continuous.sh
```

### Visualiser les données

Ouvre `index.html` dans ton navigateur :
```bash
# Option 1 : Double-clique sur index.html
open index.html

# Option 2 : Via Python
python -m http.server 8001 --directory . &
# Puis ouvre http://localhost:8001
```

L'interface chargera automatiquement :
1. D'abord depuis le backend local (`http://localhost:8000/api/data`)
2. Si échoue, depuis `loom_data.json` (données locales)

---

## 📡 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data` | Récupère tous les événements |
| GET | `/api/data/recent?hours=12` | Récupère les événements récents |
| POST | `/api/data` | Ajoute de nouveaux événements |
| GET | `/api/data/stats` | Statistiques sur les données |
| GET | `/health` | Vérifie que le backend fonctionne |
| GET | `/api/docs` | Documentation Swagger |

---

## 💾 Stockage

### Options disponibles :

1. **JSON (par défaut)** - Fichier `loom_data.json`
   ```bash
   # Dans .env
   STORAGE_TYPE=json
   STORAGE_PATH=loom_data.json
   ```

2. **SQLite** - Base de données locale
   ```bash
   # Dans .env
   STORAGE_TYPE=sqlite
   STORAGE_PATH=loom.db
   ```

---

## 🤖 GitHub Actions (Fallback)

Le workflow `.github/workflows/update_data.yml` permet de :
- **Mettre à jour automatiquement** les données toutes les 12 heures
- **Lancer manuellement** depuis l'interface GitHub
- **Pousser les changements** dans le repo

**Pour l'activer :**
1. Push le code sur GitHub
2. Le workflow s'exécutera automatiquement
3. Les données seront mises à jour dans `loom_data.json`

---

## 🎨 Catégories et Couleurs

| Catégorie | Emoji | Couleur | Description |
|-----------|-------|---------|-------------|
| Singularité | ⚪ | Blanc | IA Forte + Nanotech + Bio-ingénierie |
| Noosphère | ✨ | Bleu ciel | Conscience collective + Internet |
| Imaginaire | 🔮 | Rose | Fiction + Réalité + Anticipation |
| Hardware | 🟡 | Jaune | Loi de Moore + GPU + Matériaux |
| Cognition | 🔵 | Bleu | IA + Raisonnement + AGI |
| Réseau | 🔴 | Rouge | Web + Décentralisation + Connectivité |
| Espace | 🟣 | Violet | Mars + SpaceX + Propulsion |
| Biotech | 🟢 | Vert | CRISPR + Neuralink + Génétique |
| Entropie | ☢️ | Orange | Risques existentiels + Menaces |
| Politique | 🏛️ | Mauve | Législation + Régulation |

---

## 🔍 Framework d'Analyse (Pharmakon)

Chaque événement est analysé selon 6 dimensions :

1. **s_curve_phase** (1-5) : Phase de la courbe en S
2. **pharmakon_remedy_percent** (0-100) : % Remède (bénéfice)
3. **pharmakon_poison_percent** (0-100) : % Poison (risque)
4. **convergences** : Liens avec d'autres domaines
5. **grand_filter_analysis** : Impact sur la survie humaine
6. **final_note** : Note cynique/humoristique

---

## 📊 Scanners Intégrés

| Scanner | Source | Fréquence |
|---------|--------|-----------|
| Doomsday Clock | Bulletin of Atomic Scientists | 1/jour |
| Google News RSS | Actualités IA/Singularité | 1/jour |
| Simulateur | Événements aléatoires plausibles | 1/jour |
| Singularity Stage | Estimation du stade global | 1/jour |

---

## 🛠️ Personnalisation

### Ajouter un nouveau scanner

1. Créer une fonction dans `sentinel/sentinel.py` :
```python
def scan_mon_nouveau_scanner() -> Optional[Dict[str, Any]]:
    # Ta logique ici
    return {
        "year": 2025.0,
        "value": 50000,
        "label": "Mon événement",
        "category": "🔵 COGNITION",
        "whoWhat": "Moi",
        "description": "Description...",
        "url": "https://...",
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": False,
        "s_curve_phase": 4,
        "pharmakon_remedy_percent": 60,
        "pharmakon_poison_percent": 40,
        "convergences": "...",
        "grand_filter_analysis": "...",
        "final_note": "..."
    }
```

2. L'ajouter à la liste des scanners dans `run_sentinel_cycle()` :
```python
scanners = [
    ...,
    ("Mon Scanner", scan_mon_nouveau_scanner),
]
```

### Ajouter une nouvelle catégorie

1. Ajouter à `DEFAULT_MATRIX` dans `sentinel/sentinel.py`
2. Ajouter à `COLORS` et `ICONS` dans `index.html`

---

## 🐛 Résolution des Problèmes

| Problème | Solution |
|----------|----------|
| Backend ne démarre pas | `pip install -r backend/requirements.txt` |
| Port 8000 occupé | Changer le port dans `.env` ou `uvicorn` |
| index.html ne charge pas | Ouvrir avec `python -m http.server` |
| GitHub Actions échoue | Vérifier les permissions du repo |
| Pas de nouvelles données | Vérifier la connexion internet |

---

## 📚 Ressources

- **Documentation Swagger** : `/api/docs` (quand le backend est lancé)
- **Repository GitHub** : https://github.com/Tchernobog81/sentinel-exocortex
- **fastapi.dev** : https://fastapi.tiangolo.com/
- **Chart.js** : https://www.chartjs.org/

---

## 🎯 Prochaines Étapes

- [ ] Déployer le backend sur un service cloud (Fly.io, Railway)
- [ ] Ajouter l'authentification pour les écritures API
- [ ] Intégrer Ollama pour l'analyse IA locale
- [ ] Ajouter plus de scanners (ArXiv, Twitter, Reddit)
- [ ] Implémenter la prédiction de courbes

---

## 📞 Support

Pour toute question ou problème, consulte :
- Les logs dans `sentinel.log`
- La console du navigateur (F12)
- Les logs du backend (quand il est lancé)

---

**"La technologie est à la fois le remède et le poison."** — Jacques Derrida (Pharmakon)

---

## 🛠️ Améliorations 2026-11 (mise à jour des événements + analyse locale)

### Backend (`backend/`)
- **Upsert idempotent** : chaque événement a un `id` stable (sha1 `label|year|whoWhat`). `POST /api/data` fait un upsert → plus de doublons ni de perte par concurrence.
- **Écriture atomique + verrouillée** : `fcntl.flock` + écriture `tmp` puis `os.replace` (sûr avec les 4 workers gunicorn).
- **Backups automatiques** avant chaque écriture (garde 10) : `GET /api/backups`, `POST /api/backups/{name}/restore`.
- **Synchro incrémentale** : `GET /api/data?since=<ISO8601>`.
- `GET /api/data` renvoie les événements **aplatis** (compatible front, alias `pharmakon_*` conservés).

### Sentinel (`sentinel/sentinel.py`)
- **Analyse par LLM local outillé** (Ollama) : `web_search` + `fetch_url`, focus **AI2027** (ai2027.com). Modèle par défaut `hermes3:8b`, fallback `qwen3:8b` (voir `.env.example`). Mode `ANALYSIS_MODE=simulate` pour retomber sur l'heuristique.
- Bug corrigé : `pharmakon_poison_percent` était tiré indépendamment du remède (somme ≠ 100).
- Label stable pour le stade de singularité (la valeur estimée est dans la description) → upsert au lieu d'injecter un doublon à chaque cycle.
- Miroir local `loom_data.json` écrit de façon atomique + verrouillée, en upsert par id.

### Front (`index.html`)
- **Zooms intelligents** : wheel/pinch/pan (chartjs-plugin-zoom, déjà chargé), double-clic = reset.
- **Auto-zoom animé** vers le cluster des *nouveaux* événements détectés à chaque rafraîchissement, fenêtre adaptative (plus ça s'accélère, plus on zoome serré).
- Zoom animé au clic sur une catégorie ; étiquettes textuelles quand on zoome (< 8 ans) ; transitions animées (`easeOutQuart`, 700 ms).

### Boucle de veille autonome (push GitHub toutes les ~60 s)
```bash
./scripts/run_push_agent.sh
```
L'agent scrute le net à chaque cycle (LLM local outillé, focus AI2027), met à jour
`loom_data.json` via le backend local, et **commit + push sur `main` uniquement si de
nouveaux événements** ont été détectés → la page GitHub Pages (v148) se met à jour
automatiquement (workflow `static.yml`). Pré-requis : accès SSH au dépôt
(`git@github.com:Tchernobog81/sentinel-exocortex.git`, clé enregistrée sur le compte).
Logs : `sentinel_push.log`. Verrou mono-instance : `.push_agent.lockdir/`.
