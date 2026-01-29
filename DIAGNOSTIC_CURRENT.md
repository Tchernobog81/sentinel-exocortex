# 🚀 DIAGNOSTIC & ARCHITECTURE - SENTINEL v2 (Ready for RPi5)

## 1. Contexte

L'agent `sentinel.py` actuel est devenu obsolète face aux nouvelles directives d'analyse de la **v117 du CHANGELOG**. Il souffre d'instabilités et son analyse est trop superficielle. Une refonte est nécessaire pour l'aligner sur la vision stratégique du projet Loom.

**Objectif :** Transformer Sentinel d'un simple collecteur de news en un **agent d'analyse intelligent** capable de qualifier les signaux faibles selon la nouvelle grille d'analyse.

---

## 2. Analyse des Lacunes de l'Agent Actuel

- **❌ Analyse Superficielle :** Se limite à une classification par mots-clés.
- **❌ Modèle de Données Rigide :** Ne peut pas stocker les résultats d'une analyse complexe (Pharmakon, courbe en S...).
- **❌ Capteurs Limités :** Incapable de suivre des concepts spécifiques comme l'Horloge de l'Apocalypse, la Noosphère ou l'échelle de Kardashev.
- **❌ Maintenance Difficile :** La structure monolithique rend les évolutions complexes.

---

## 3. Stratégie de Reprise : Sentinel v2

La nouvelle version de `sentinel.py` s'articule autour de 4 axes majeurs :

### Axe 1 : Le Cœur Analytique (`analyze_event`)
- **Rôle :** Remplace la simple classification. Applique la grille d'analyse v117 à n'importe quel événement.
- **Champs Générés :**
  - `s_curve_phase` (1-5)
  - `pharmakon_remedy_percent` / `pharmakon_poison_percent`
  - `convergences`
  - `grand_filter_analysis`
  - `final_note` (touche d'humour noir)
- **État :** ✅ Implémenté (en mode simulé, prêt pour une connexion à une IA externe).

### Axe 2 : Nouveaux Capteurs Spécifiques
- **`scan_doomsday_clock()` :**
  - **Rôle :** Crée un événement annuel pour l'Horloge de l'Apocalypse.
  - **Donnée Actuelle :** **89 secondes** (Mise à jour de Janvier 2025), avec les motifs du changement inclus dans la description. [5, 15, 16, 24]
  - **État :** ✅ Implémenté.
- **`scan_simulator()` (Amélioré) :**
  - **Rôle :** Génère des signaux faibles alignés sur les nouveaux horizons de surveillance.
  - **Thèmes :** Noosphère, Civilisation Type 1, IA avancée, Hardware neuromorphique.
  - **État :** ✅ Implémenté et utilise `analyze_event`.
- **`scan_google_news_rss()` :**
  - **Rôle :** Scanne les actualités généralistes sur l'IA et la singularité.
  - **Amélioration :** Chaque article trouvé est maintenant passé à `analyze_event` pour une analyse complète.
  - **État :** ✅ Implémenté.

### Axe 3 : Modèle de Données Enrichi
- Le format des événements injectés est désormais **compatible avec la v117**, contenant tous les champs d'analyse. Cela garantit que les données stockées dans `LOOM_DB.json` sont prêtes à être exploitées par le visualiseur `index.html` sans conversion.

### Axe 4 : Architecture Modulaire
- Le cycle principal (`run_sentinel_cycle`) a été revu pour orchestrer les différents scanners.
- Il est maintenant facile d'ajouter ou de désactiver un "capteur" sans impacter les autres.
- La gestion des doublons et l'injection des données ont été centralisées.

### Axe 5 : Suivi des Horizons de Convergence
- **`scan_singularity_stage()` :**
  - **Rôle :** Crée un événement dédié pour matérialiser le stade d'avancement vers la singularité.
  - **Donnée Actuelle :** Stade estimé entre **0.7 et 0.8**.
  - **État :** ✅ Implémenté.

---

## 4. Architecture Cible : Raspberry Pi 5 AI

Le projet est prêt à être déployé sur un Raspberry Pi 5.

### Pré-requis RPi 5 :
- **OS :** Raspberry Pi OS (Bookworm) 64-bit.
- **Python :** 3.11+ (Géré via environnement virtuel `venv` recommandé pour éviter les conflits système).
- **Hardware AI (Optionnel) :** Le code actuel utilise l'API Cloud Gemini. Une migration vers un modèle local (Ollama/Hailo-8L) nécessitera une adaptation de la fonction `analyze_with_gemini` dans `sentinel.py`.

### Installation RPi :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Prochaines Étapes

1.  **Validation :** Examiner et valider la nouvelle version de `sentinel.py`.
2.  **Déploiement :** Mettre à jour le fichier sur le serveur ou dans le workflow GitHub Actions.
3.  **Surveillance :** Observer les nouvelles données injectées dans `LOOM_DB.json` pour s'assurer qu'elles contiennent bien les champs d'analyse v117.
4.  **(Futur) Itération :** Remplacer l'analyse simulée dans `analyze_event` par un appel à une véritable API d'IA (ex: Gemini) en utilisant le prompt du "veilleur technologique" comme blueprint.

**Bilan :** ✅ L'agent est maintenant structurellement aligné avec la vision v117. Il est plus robuste, plus intelligent et prêt pour les futures évolutions.