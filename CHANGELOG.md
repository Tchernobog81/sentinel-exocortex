# CHANGELOG - Cortex Loom

## v122
- 🐛 **UI Fix :** Le curseur "doigt" est maintenant **définitivement** fonctionnel au survol des étiquettes. Le conflit d'événements a été résolu.
- 📊 **Data Story :** La ligne "Singularité" est désormais une courbe visible grâce à l'ajout de points de données historiques (Vinge, Kurzweil).
- 📚 **Data :** Enrichissement de la description de l'événement "Tchernobyl" pour plus de contexte.
- ✨ **Nouvelle Catégorie :** Ajout de la courbe `🏛️ POLITIQUE` pour tracer les réactions sociales à la technologie.
- 📚 **Data :** Injection des événements fondateurs de la courbe politique (Luddites, Canuts, Unabomber, Accélérationnisme).
- 🔖 **Version :** Passage en v122.

## v121
- 🐛 **UI Fix :** Le curseur "doigt" est maintenant fonctionnel au survol des étiquettes.
- 🎨 **UI :** Les points sur le graphique sont plus visibles (style "donut") pour éviter les étiquettes flottantes.
- ✨ **UX :** Seuls les événements "points d'inflexion" (`tipping: true`) affichent une étiquette persistante pour clarifier le graphique.
- 📚 **Data :** Enrichissement de l'événement "Tchernobyl" (description, image, analyse Pharmakon).
- 📚 **Data :** Enrichissement de l'événement "Test de Turing" (description, analyse Pharmakon).
- 🔖 **Version :** Passage en v121.

## v120
- 🚀 **Pipeline :** Correction du workflow de déploiement GitHub Actions.
- 🔧 **CI/CD :** Ajout d'un fichier de workflow `sentinel_workflow.yml` dédié et robuste.
- 📦 **Dépendances :** Création d'un fichier `requirements.txt` pour fiabiliser l'installation.
- 🔖 **Version :** Passage en v120.

## v119
- 🐛 **UI Fix :** Le curseur se transforme désormais correctement en "doigt" au survol des étiquettes d'événements sur le graphique.
- 📚 **Data Injection :** Ajout d'événements historiques clés pour l'Horloge de l'Apocalypse (1949, 1984, 2018).
- 📚 **Data Injection :** Ajout d'une série d'événements retraçant notre progression sur l'échelle de Kardashev (Type 0.7 -> 0.73).
- 🔖 **Version :** Passage en v119.

## v117
- 🧠 **Nouvelles Directives d'Analyse & Évolution du Scope**
- **Horloge de l'Apocalypse (Doomsday Clock)** : La ligne "Risque" intègrera désormais toutes les mises à jour de l'horloge, avec les justifications de chaque changement. Niveau actuel : 90 secondes avant minuit (Mise à jour de Janvier 2024).
- **Références Culturelles** : Ajout de nouvelles œuvres de science-fiction et de culture populaire pour enrichir les parallèles (ex: *Pluribus*, *The Expanse*, *The Simpsons*).
- **Noosphère** : Une nouvelle ligne est créée pour suivre l'évolution du concept de noosphère, depuis sa conceptualisation par Pierre Teilhard de Chardin jusqu'à ses interprétations modernes.
- **Changement d'Horizons de Surveillance** : Le projet se concentre maintenant sur deux horizons de convergence :
    1.  **Civilisation de Type 1** : Suivi de notre progression sur l'échelle de Kardashev.
    2.  **Singularités Technologiques** : Détection des signaux faibles avec une évaluation du stade d'avancement (stade actuel estimé entre 0,7 et 0,8).
- **Analyse "Pharmakon"** : Chaque événement sera analysé comme un *pharmakon* (remède/poison), avec une attribution d'un pourcentage pour chaque potentiel.
- **Nouveau Prompt d'Analyse** : Adoption d'un nouveau modèle pour l'évaluation des événements, basé sur les directives suivantes :
    1.  **Signal & Contexte** : Résumé bref.
    2.  **Courbe en S** : Positionnement sur la courbe de la singularité (phase 1-5).
    3.  **Analyse Pharmakon** : Potentiel médicamenteux vs. toxique (%).
    4.  **Convergences & Grand Filtre** : Analyse des risques et bénéfices croisés.
    5.  **Note Finale** : Touche d'humour noir et désabusé.

## v116
- 🐛 Fix : Augmentation de la zone de survol (`hitRadius`) des points pour une détection plus fiable du curseur et de l'infobulle, même en survolant le texte du label.
- 🐛 Debug : Version v116 affichée au démarrage.

## v115
- 🐛 Debug : Affichage explicite de la version dans l'écran de chargement ("Init v115...").
- 🔖 Version : Passage en v115 pour forcer le rafraîchissement du cache.

## v114
- 🐛 Fix : Les labels sont maintenant coupés ("clippés") quand ils sortent de la zone du graphique.
- 🐛 Fix : Le "fil" de l'infobulle est maintenant correctement ancré au point de donnée survolé.
- 🐛 Fix : Le curseur "doigt" est maintenant correctement appliqué au survol des points.

## v113
- 🖱️ UX : "Focus Mode" sur la légende (clic = mise en avant de la ligne, transparence des autres).
- 🎨 UI : Correction du fil d'ariane des bulles (coordonnées natives).
- 🐛 Fix : Curseur "doigt" forcé sur le canvas au survol.

## v112
- 🎨 UI : Ajout d'un "fil" visuel reliant l'infobulle au point sur le graphique.
- ⏱️ Timer : Formatage strict `hh:mm` (ex: 01:05).
- 🐛 Fix : Amélioration de la détection du survol pour le curseur "doigt".

## v111
- 🐛 Fix : Correction du numéro de version affiché dans la sidebar (était resté bloqué sur v109).

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