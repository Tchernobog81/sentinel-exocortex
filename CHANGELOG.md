# CHANGELOG - Cortex Loom

## v110
- 🐛 UI Fix : Le bouton "Retour vers le Futur" est enfin correctement centré (correction du JS qui écrasait les classes CSS).
- 🖱️ UX : Amélioration des curseurs sur la légende et les éléments interactifs.

## v109
- 🤖 Agent : Sentinel peut maintenant scanner Google News (mode `RSS_NEWS`).
- 🤖 Agent : Ajout d'un classificateur de news par mots-clés.
- 🔧 Pipeline : Le workflow Sentinel sur GitHub utilise maintenant le mode `RSS_NEWS`.
- 🐛 UI Fix : Comportement du curseur (flèche/doigt) corrigé sur le graphique.

## v107
- 🖱️ UX : Curseur "pointer" (main) au survol des événements du graphique.
- 🚀 Pipeline : Push de déclenchement pour GitHub Actions.

## v106
- 🔧 Pipeline : Configuration de la source de déploiement sur "GitHub Actions".
- 🐛 Fix : Correction de la balise meta viewport pour une meilleure compatibilité mobile.

## v105
- 🎨 UI : Bouton "Retour vers le Futur" stylisé et centré.
- 🔍 UX : Zoom adaptatif sur 1985 (Focus étiquette).
- ⏱️ Timer : "Mise à jour dans..." synchronisé sur l'heure pile.
- 📚 Data : Ajout Barjavel (Ravage, Nuit des temps) & Iain M. Banks (Culture).

## v104 (Actuel)
- 🔧 Pipeline : Ajout du workflow GitHub Actions explicite (`static.yml`).
- 📝 Doc : Création du CHANGELOG.

## v103
- 🎨 UI : Refonte "Retour vers le Futur" (Bouton, Dégradés).
- ⚡ Core : Suppression de l'injection manuelle (remplacée par `inject_data.py`).
- 📊 Data : Injection massive (87 événements) et nouvelles catégories.
- 🐛 Fix : Correction de l'ordre d'affichage (Singularité au premier plan).

## v102
- 🏗️ Architecture : Migration vers format JSON plat (Array).
- 🛠️ Debug : Ajout console de logs et écran de chargement.
- 🤖 Agent : Sentinel v1 (Daemon).