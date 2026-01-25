# Architecture - Intégration Google Drive × Google Apps Script

## 📊 Vue globale

```
┌─────────────────────────────────────────────────────────────┐
│                     ÉCOSYSTÈME LOOM                          │
└─────────────────────────────────────────────────────────────┘

                    index.html (Client)
                    ├─ Load Data (GET)
                    ├─ Inject Data (POST)
                    └─ Auto-Refresh (5 min)
                           ↕
                           │
         ┌─────────────────────────────────────┐
         │  Google Apps Script (Web App)       │
         │  ├─ doGet()  → Récupère            │
         │  ├─ doPost() → Enregistre          │
         │  └─ LockService (Verrous)          │
         └─────────────────────────────────────┘
                           ↕
         ┌─────────────────────────────────────┐
         │      Google Drive (Storage)         │
         │  ├─ LOOM_DATA/                      │
         │  │  ├─ LOOM_DB.json (Principal)   │
         │  │  └─ LOOM_BACKUPS/              │
         │  │     ├─ LOOM_DB_*_1.json       │
         │  │     ├─ LOOM_DB_*_2.json       │
         │  │     └─ ... (Max 10)            │
         │  └─ (Accès: Vous)                 │
         └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  External Integrations (Optional)                           │
├─────────────────────────────────────────────────────────────┤
│ • Python Scripts (test_integration.py)                       │
│ • cURL / HTTP Clients (curl_examples.sh)                    │
│ • Webhooks / Zapier / IFTTT                                 │
│ • CI/CD Pipelines (GitHub Actions)                          │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Flux de données

### Scénario 1: Récupération (GET)
```
User clicks "Reload"
       ↓
index.html fetch(CLOUD_URL)
       ↓
Google Apps Script doGet()
       ↓
Drive API.getDbFile().read()
       ↓
JSON Response { strands: [...] }
       ↓
Chart.js update()
```

### Scénario 2: Injection (POST)
```
User pastes JSON
       ↓
Click "Inject & Save"
       ↓
index.html fetch(CLOUD_URL, {method: POST, body: JSON})
       ↓
Google Apps Script doPost()
       ↓
LockService.waitLock(30s)
       ↓
createBackup() → LOOM_BACKUPS/LOOM_DB_*.json
       ↓
getDbFile().setContent(newData)
       ↓
Response { status: ok, items: N, timestamp }
       ↓
Status message + Close console (1.5s)
```

### Scénario 3: Sync Automatique
```
Initial Load
       ↓
setInterval(loadData, 300000) [5 min]
       ↓
Fetch from Cloud
       ↓
Update Chart if different
       ↓
Update "LIVE" timestamp
```

## 🗂️ Structure des fichiers

```
f:\Cortex_Loom/
├── index.html                    [Client Web App]
├── loom_data.json               [Données complètes]
├── input.json                   [Données à injecter]
├── Update_Loom.gs              [Google Apps Script]
├── sentinel.py                  [Monitoring]
├── watchdog.yml                 [Config Sentinel]
│
├── GOOGLE_DRIVE_SETUP.md        [Documentation ← LIRE EN PREMIER]
├── test_integration.py          [Script de test]
├── curl_examples.sh             [Exemples HTTP]
│
└── sentinel-exocortex/
    ├── README.md
    ├── sentinel.py
    └── requirements.txt
```

## 🔐 Sécurité & Fiabilité

```
┌──────────────────────────────────────────┐
│ Verrou automatique (LockService)         │
│ Pas de race conditions                   │
│ Max 30s d'attente par requête            │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Sauvegarde automatique avant chaque POST │
│ Versioning avec timestamps               │
│ Garder 10 derniers backups               │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Validation JSON stricte                  │
│ Rejet format invalide                    │
│ Message d'erreur explicite               │
└──────────────────────────────────────────┘
```

## 📡 Points d'intégration

### 1. index.html
- Constante `CLOUD_URL` (ligne ~66)
- Fonction `loadData()` (GET)
- Fonction `injectAndSave()` (POST)
- Auto-refresh toutes les 5 minutes

### 2. Google Apps Script
- Déployer comme Web App
- Accès: "Tout le monde"
- Exécuter en tant que: Vous

### 3. Google Drive
- Créé automatiquement: `LOOM_DATA/`
- Créé automatiquement: `LOOM_DATA/LOOM_BACKUPS/`
- Accès: "Vous uniquement" (via Apps Script)

## ⚙️ Configuration requise

```json
{
  "client": {
    "framework": "Vanilla JS + Chart.js",
    "dependencies": ["chart.js", "chartjs-plugin-zoom", "chartjs-plugin-datalabels"],
    "targetUrl": "Your Google Apps Script URL"
  },
  "server": {
    "platform": "Google Apps Script",
    "storage": "Google Drive",
    "concurrency": "LockService (30s timeout)",
    "versioning": "Automatic backups"
  },
  "formats": {
    "data": "JSON (strands array)",
    "transport": "application/json",
    "encoding": "UTF-8"
  }
}
```

## 🎯 Checklist de déploiement

- [ ] Google Account connecté
- [ ] Créer le projet Apps Script
- [ ] Copier `Update_Loom.gs` complet
- [ ] Déployer comme Web App
- [ ] Copier l'URL générée
- [ ] Mettre à jour `index.html` (ligne ~66)
- [ ] Tester GET (reload page)
- [ ] Tester POST (Data Inject)
- [ ] Vérifier Drive: `LOOM_DATA/` créé
- [ ] Vérifier Drive: `LOOM_BACKUPS/` créé
- [ ] Vérifier sync auto (5 min)
- [ ] Tester `test_integration.py` (optionnel)

## 📞 Support

Si ça ne marche pas:
1. Vérifier URL dans index.html
2. Ouvrir console (F12 > Console)
3. Chercher erreurs réseau
4. Vérifier permissions Google Apps Script
5. Vérifier que "Tout le monde" peut accéder
