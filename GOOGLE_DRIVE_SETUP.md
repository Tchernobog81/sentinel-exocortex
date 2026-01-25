# 🔗 Intégration Google Drive × Google Apps Script

## 📋 Architecture

```
Google Drive
├── LOOM_DATA/
│   ├── LOOM_DB.json (principal)
│   └── LOOM_BACKUPS/
│       ├── LOOM_DB_2026-01-25_14-30-00.json
│       └── ... (garder 10 derniers)
```

## 🚀 Déploiement du Script Google

### 1. Créer le Google Apps Script
1. Aller sur [script.google.com](https://script.google.com)
2. Créer un nouveau projet
3. Copier le contenu de `Update_Loom.gs` dans l'éditeur
4. **Enregistrer** (Ctrl+S)

### 2. Déployer comme Web App
1. Cliquer sur **"Déployer"** (en haut à droite)
2. Sélectionner **"Nouveau déploiement"**
3. Type: **"Application Web"**
4. Exécuter en tant que: **Vous**
5. Accès: **"Tout le monde"** (permet les requêtes externes)
6. Cliquer **"Déployer"**
7. Copier l'URL générée (ex: `https://script.google.com/macros/s/AKfy.../exec`)

### 3. Mettre à jour l'URL dans index.html
```javascript
// Dans index.html, ligne ~66
const CLOUD_URL = 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec';
```

## 📡 Fonctionnalités

### GET - Récupérer les données
```javascript
// Automatique via fetch() dans index.html
fetch(CLOUD_URL)
  .then(r => r.json())
  .then(data => console.log(data));
```

**Réponse:**
```json
{
  "strands": [
    { "name": "💗 ORACLES", "color": "#f472b6", "events": [...] }
  ],
  "metadata": { "lastUpdate": "2026-01-25T...", "version": "1.0" }
}
```

### POST - Envoyer/modifier les données
```javascript
const newData = {
  "strands": [
    {
      "name": "🟡 SUBSTRAT",
      "color": "#fbbf24",
      "events": [
        {
          "year": 2026.06,
          "value": 40000,
          "label": "Mon Événement",
          "whoWhat": "Source",
          "how": "Description",
          "img": "https://...",
          "realYear": 2030.5
        }
      ]
    }
  ]
};

fetch(CLOUD_URL, {
  method: 'POST',
  body: JSON.stringify(newData),
  headers: { "Content-Type": "application/json" }
})
.then(r => r.json())
.then(res => console.log(res));
```

**Réponse:**
```json
{
  "status": "ok",
  "items": 16,
  "timestamp": "2026-01-25T14:30:00.000Z"
}
```

## 🔐 Sécurité

- **Verrous automatiques** (LockService) = pas de race conditions
- **Sauvegardes automatiques** = avant chaque écriture
- **Validation JSON** = rejet des données malformées
- **Métadonnées** = tracking des modifications

## 🛠️ Commandes de gestion

### Dans la console Apps Script (Debug):

```javascript
// Infos du fichier
getDbInfo()
// → { fileName, fileId, lastModified, strands, events, metadata }

// Lister les sauvegardes
listBackups()
// → [{ name, date, size }, ...]

// Restaurer une sauvegarde
restoreBackup("LOOM_DB_2026-01-25_14-30-00.json")
// → { status: "ok", message: "..." }

// Nettoyer (garder 10 derniers)
cleanOldBackups(10)
// → { status: "ok", deleted: 3 }
```

## 🔄 Flux de travail

### Ajouter un événement via UI
1. Cliquer **"Data Inject"** dans index.html
2. Coller le JSON
3. Cliquer **"Inject & Save to Cloud"**
4. ✅ Sauvegardé dans Drive + Backup créé

### Sync automatique
- Rafraîchissement **toutes les 5 minutes** (index.html)
- Affichage "LIVE" + timestamp dans le header

### Restauration d'urgence
- Toutes les sauvegardes sont conservées
- Utiliser `restoreBackup()` si besoin

## 📊 Format de données complet

```json
{
  "year": 2026.06,           // Année (décimale = T1-T4)
  "weight": 9,                // Importance (1-10)
  "value": 40000,             // Valeur/Amplitude
  "label": "Événement",       // Titre
  "whoWhat": "Source",        // Origine
  "how": "Description",       // Impact
  "img": "https://...",       // Image (optionnel)
  "url": "https://...",       // Lien (optionnel)
  "realYear": 2030.5,         // Réalité prédite (optionnel)
  "tipping": true             // Point d'inflexion? (optionnel)
}
```

## ⚠️ Troubleshooting

**"Erreur: 403 Forbidden"**
- Vérifier l'URL du déploiement
- Accès doit être "Tout le monde"

**"Erreur: Invalid JSON"**
- Vérifier la structure: doit avoir `strands` array
- Utiliser un validateur JSON

**"Les données ne se synchronisent pas"**
- Vérifier la console (F12 > Network)
- S'assurer que CLOUD_URL est correcte dans index.html

## 🎯 Prochaines étapes

1. ✅ Déployer le script
2. ✅ Ajouter l'URL dans index.html
3. ✅ Tester GET (reload page)
4. ✅ Tester POST (Data Inject)
5. ✅ Vérifier Drive pour LOOM_DATA/LOOM_BACKUPS
