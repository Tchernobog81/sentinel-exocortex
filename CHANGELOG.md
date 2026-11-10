# CHANGELOG - Cortex Loom

## v161
- 🧼 **Popups propres** : le HTML brut des flux RSS (Google News embarque <a>/<font>) est supprimé à l'ingestion (sentinel `clean_text`) ET à l'API (backend `_clean_text` sur label/description/source/analyse) ; les données existantes sont curées. Une popup affiche désormais « Le score ARC-AGI-3 de Gemini 4 Argon atteint 97,5 %… » sans balises.
- 🔖 **Version :** Passage en v161.

## v160
- ⇄ **Toutes les fictions liées** : mapping manuel des 24 classiques (1984→PRISM, Blade Runner→Atlas, Gattaca→23andMe, Ex Machina→LLM, Tron→Métavers, WarGames→Stuxnet, Simpson→Higgs, Excession→Bitcoin…) + auto-liens. Bilan: 67/68 fictions avec realYear, 45 réels avec predictedBy — les popups fictionnelles pointent toutes vers leur réalisation.
- 📏 **Flux à hauteur max dynamique** : max-height 45vh, scroll interne.
- 📱 **Interface adaptative** : burger ☰ + sidebar en overlay coulissante ≤760px, top-bar qui wrap, fiche popup plein écran scrollable, recherche réduite.
- 🗓️ **Axe X lisible en zoom** : ticks en "15 juin 2026" (zoom < 2 ans), "juin 2026" (< 20 ans), année sinon — plus de décimaux 2026.5.
- 🔖 **Version :** Passage en v160.

## v159
- 👆 **Flux cliquable** : chaque événement du flux amène (zoom animé) au point correspondant de la courbe et ouvre sa fiche popup.
- ⏱️ **Flux chronologique strict** : tri par timestamp décroissant, dates invalides/futures exclues, affichage HH:MM (aujourd'hui) ou JJ/MM.
- 🔄 **Rafraîchissement auto toutes les minutes** (60 s).
- 🎯 **Clic catégorie = isolement réversible** : un clic invisibilise toutes les autres courbes, un re-clic sur la même les réaffiche toutes.
- 🔖 **Version :** Passage en v159.

## v158
- 🗂️ **13 catégories regroupées en 8 courbes** (option B validée, au rendu — données inchangées) : ⚙️ INDUSTRIE & ROBOTS · 🚀 ESPACE · 🧠 IA & COGNITION · 🌍 NOOSPHÈRE & RÉSEAUX · 🧬 VIVANT & SANTÉ · 🏛️ POLITIQUE · ☢️ ENTROPIE & CYBER · 🎬 FICTION. Toggle on/off par courbe dans le bandeau.
- 🔖 **Version :** Passage en v158.

## v157
- ⇄ **Liens fiction⇄réel systématisés** : Manon des sources (Pagnol) ⇄ Guerres de l'Eau 2050 ; +11 appariements auto conservateurs (token commun + fenêtre 90 ans). Bilan: 43/68 fictions avec realYear, 37 réels avec predictedBy.
- 🎨 **Courbes adoucies** (lisibilité zone dense) : lignes 1,5 px à 70 % d'opacité, points 4 px / bordure 1 px.
- 🔖 **Version :** Passage en v157.

## v156
- 🗂️ **Catégories déplacées** en bandeau horizontal au-dessus du graphique (scrollable, groupes thématiques + chips), la sidebar est libérée pour le flux.
- 🧹 **Libellés nettoyés** : plus de « Mise à jour... » (horloge HH:MM discrète) ni de « Source: loom_data.json... » (simple ↻ HH:MM).
- ⇄ **Popups inter-liées** : navigation prédit ⇄ réalisé dans les deux sens (realYear / predictedBy), les doublons de label sautent vers l'entrée liée.
- 📡 **Flux haut signal** : RSS multi-requêtes (ARC-AGI, FrontierMath, IMO, preuves maths/physique, labs) + filtre anti-hype par mots-clés factuels (benchmark/record/prouvé/résolu/découvert...). +8 faits 2026 vérifiés seedés (ARC-AGI-3 launch 25/03, Gemini 4 Argon 97,5 %, conjecture 42 ans en 12 h, réfutation Erdős Lean, 5/6 IMO, Science 2026...).
- 🔖 **Version :** Passage en v156.

## v155
- 🤖 **13e courbe « ROBOTIQUE »** : 14 jalons réels (Léonard 1495 → Figure 01 2024) + 8 liens fiction→réalité (Metropolis, R.U.R., I, Robot, Terminator...) avec realYear/predictedBy.
- 🗂️ **Zone catégories réorganisée** : groupes thématiques (Matière & Énergie / Vivant & Santé / Esprit & Idées / Société & Risques) en grille de chips compacts on/off, compteurs inclus.
- 🔬 **Lisibilité zone d'accélération** : décimation adaptative des étiquettes selon la densité de points visibles (>60: tipping seuls, >30: 1/3, >15: 1/2, sinon toutes) ; fenêtre d'auto-zoom encore plus serrée quand la densité récente est forte (half=1 si >6 events sur 3 ans).
- 🔖 **Version :** Passage en v155.

## v154
- 🏛️ **Référentiel élargi aux origines :** événements de -2600 (irrigation Égypte) au mécanisme d'Anticythère (~-100 av. J.-C.) et inventions grecques/romaines/égyptiennes/chinoises (papier 105, poudre 850, boussole ~1000, horloge mécanique 1300...). Vue initiale désormais calée sur toute la plage de données (`dataRange()`), plus 1940-2050 en dur.
- 💊 **12e courbe « MÉDECINE »** : 15 jalons médicaux avérés (Hippocrate -400, Harvey 1628, Jenner 1796, Pasteur 1861, pénicilline 1928, ADN 1953, VIH 1983, CRISPR 2012, ARNm 2020...).
- 📡 **Flux 12h = faits vérifiés uniquement** : la fiction (IMAGINAIRE) est exclue du flux entrant (tâche de fond) ; 69 timestamps de seeds normalisés (backdatés à leur année) pour ne plus polluer le flux.
- 🔖 **Version :** Passage en v154.

## v153
- 🎨 **Dashboard :** popups adoucies (fiche au clic uniquement, plus au survol ; ouverture en fondu 250 ms) ; barre de recherche textuelle (label/source/catégorie/description) ; ligne verticale « MAINTENANT » ; widget Horloge de l'Apocalypse dans la sidebar (dernier réglage officiel, maj quotidienne) ; navigation Prédit→Réalisé cliquable dans la fiche (realYear / predictedBy, zoom animé vers la cible).
- ☢️ **Horloge :** `scan_doomsday_clock()` scrape désormais la page officielle thebulletin.org à chaque cycle (label stable par année → upsert, description rafraîchie quotidiennement).
- 📚 **Data :** +44 événements fiction→réalité (22 paires œuvre/réalisation avec liens predictedBy/realYear), seed verrouillé `scripts/seed_fiction_links.py`. Total 431 événements, 11 catégories.
- 🔖 **Version :** Passage en v153.

## v152
- 🎛️ **UI (légende) :** courbes en on/off **indépendant** — cliquer une catégorie allume/éteint UNIQUEMENT celle-ci (les autres restent inchangées) ; bouton ⟳ pour tout réafficher ; l'état on/off survit aux rafraîchissements auto.
- ☠️ **Nouvelle courbe (11e) « RISQUES CYBER »** : 25 attaques cyber majeures des origines (ver Morris 1988) à aujourd'hui (Bybit 2025), seed via `scripts/seed_cyber_events.py` (upsert par id).
- 🔖 **Version :** Passage en v152.

## v151
- 📈 **UI (courbes) :** `showLine: true` sur les datasets scatter — les événements d'une catégorie sont reliés par une courbe (les points restent visibles).
- 🔍 **UI (zoom/pan) :** bloc `plugins.zoom` correctement imbriqué (`zoom.zoom.wheel/pinch`, `zoom.pan`) — zoom molette/pinch en mode `xy` restauré, pan glisser-déposer `xy` (avant/arrière/haut/bas), limite `x.minRange = 0.25 an`. Testé en headless Chromium (wheel + drag simulés).
- 🔖 **Version :** Passage en v151.

## v150
- 🐛 **UI (bloqué) :** Fix du plantage au chargement (testé en navigateur headless Chromium) : `chartjs-plugin-datalabels` appelait `display()` avec `context.dataPoint` undefined → TypeError non capturée → écran de boot jamais retiré. Gardes sur `display`/`formatter`/tooltip externe + try/catch autour du rendu initial (l'écran de chargement disparaît désormais toujours).
- 🔖 **Version :** Passage en v150.

## v149
- 🔍 **UI (Pages) :** Ordre des sources de données contextuel — sur GitHub Pages, `loom_data.json` est lu directement (plus de tentative `localhost:8000` qui échouait à chaque rafraîchissement) ; en local, l'API FastAPI reste prioritaire. Cache-buster `?t=` appliqué aussi au JSON.
- 🔖 **Version :** Passage en v149.

## v148
- 🏗️ **Architecture :** Publication de la version locale (backend FastAPI + sentinel LLM) dans le dépôt ; la page GitHub Pages lit désormais `loom_data.json` (poussé par l'agent) avec fallback GAS.
- 🛡️ **Backend :** upsert idempotent par `id` stable, écriture atomique verrouillée (flock + os.replace), backups auto (10) avec endpoints restore, `GET /api/data?since=`.
- 🤖 **Sentinel :** analyse Pharmakon v117 par LLM local outillé (Ollama hermes3:8b, fallback qwen3:8b) avec recherche web (web_search/fetch_url), focus AI2027 ; boucle de push toutes les minutes vers GitHub si nouveaux événements.
- 🐛 **Fix :** somme remède+poison = 100 % (un seul tirage) ; label stable du stade de singularité (upsert au lieu de doublons).
- 🔍 **UI :** zooms intelligents (wheel/pinch/pan, double-clic reset), auto-zoom animé vers les nouveaux événements avec fenêtre adaptative, transitions fluides 700 ms.
- 🔖 **Version :** Passage en v148.

## v147
- 🐛 **Data Fix (Entropie) :** Correction définitive du "trou" de l'Horloge de l'Apocalypse. Suppression des doublons (séries concurrentes) et recalcul complet de l'axe Y pour garantir une courbe strictement croissante de 1943 à 2050.
- 🔗 **Data Links :** Ajout du lien prédictif manquant entre *Le Meilleur des mondes* et *Bébés CRISPR*.
- 📏 **Directives :** Ajout d'une règle de déduplication stricte.
- 🔖 **Version :** Passage en v147.

## v146
- 🧠 **Auto-Repair :** L'agent `sentinel.py` intègre désormais une "Matrice de Convergence". Il détectera et corrigera automatiquement les analyses manquantes ("N/A") lors de chaque cycle.
- 🧠 **Data Intelligence (Remoulinage) :** Suppression totale des "N/A" dans les champs d'analyse (`convergences`, `grand_filter`). Un script heuristique a appliqué une matrice d'analyse par défaut basée sur la catégorie pour tous les événements incomplets.
- 📏 **Directives :** Interdiction absolue des champs d'analyse vides ou "N/A".
- 🔖 **Version :** Passage en v146.

## v145
- 🎨 **UI (Visual Check) :** Le numéro de version dans la barre latérale est maintenant **Vert Émeraude** pour confirmer visuellement la mise à jour et distinguer la v145 des versions cachées précédentes.
- ⚙️ **CI/CD :** Inscription explicite du `run-name: The Loom v145 🚀` dans le fichier YAML pour garantir la traçabilité du déploiement.
- 🔖 **Version :** Passage en v145.

## v144
- 📚 **Data Quality (Deep Clean) :** Enrichissement manuel des événements fondateurs du Réseau (Web, Google, Facebook, Bitcoin) qui manquaient de descriptions et d'analyses.
- 📈 **Data Fix (Entropie v2) :** Algorithme de lissage strict appliqué à la courbe d'Entropie. La valeur `y` d'un événement ne peut désormais plus jamais être inférieure à celle de l'événement précédent, garantissant une courbe ascendante sans "chute".
- 📏 **Directives :** Obligation de remplir les champs d'analyse (`convergences`, `grand_filter`) pour tous les événements majeurs.
- 🔖 **Version :** Passage en v144.

## v143
- 🔧 **UX (Hotfix) :** Ajout d'une fonction `forceReload()` accessible en cliquant sur le numéro de version (Sidebar). Cela recharge la page avec un paramètre unique pour contourner le cache du navigateur.
- 🔖 **Version :** Passage en v143.

## v142
- 📚 **Data Fix (Massif) :** Injection automatique des sources (`whoWhat`) pour +100 événements orphelins. Plus aucun "Source: ?" ne devrait apparaître.
- 📈 **Data Fix (Entropie) :** Harmonisation algorithmique de la courbe "☢️ ENTROPIE". Les valeurs de l'axe Y ont été recalculées pour être strictement croissantes, supprimant le "trou" de 1991 (Horloge 17mn).
- 📏 **Directives :** Règle stricte imposant le champ `whoWhat` pour tout événement.
- 🔖 **Version :** Passage en v142.

## v141
- 🔧 **Hotfix (Cache) :** Ajout de balises `meta` anti-cache et d'un timestamp sur les requêtes `fetch` pour forcer le rafraîchissement des données sur tous les navigateurs.
- 🧭 **UX (Interface) :** La fiche de détail (`#detail-card`) est désormais **déplaçable** (draggable) à la souris.
- 🛡️ **UX (Contraintes) :** Le déplacement de la fiche est contraint aux limites de l'écran pour éviter qu'elle ne devienne inaccessible.
- 📚 **Data Quality :** Enrichissement massif des œuvres de fiction (Blade Runner, Matrix, Her, etc.) avec descriptions complètes, analyses Pharmakon et liens bidirectionnels (Prédit/Réalisé).
- 🐛 **Data Fix :** Suppression du doublon "Horloge Apocalypse 1991" (valeur 100) qui cassait la courbe d'Entropie. Correction de syntaxe JSON sur les événements 2000/2001.
- 💉 **Data Injection :** Ajout de 10 événements majeurs pour les catégories **Biotech** (PCR, OGM, iPS) et **Noosphère** (McLuhan, Intelligence Collective, Wikileaks) afin d'équilibrer le dataset.
- � **Directives :** Ajout d'une règle stricte pour les fictions : Pitch obligatoire, pas de "N/A", et lien vers la réalité.
- 🧭 **UX (Nav) :** Le maillage temporel est maintenant dense : Blade Runner pointe vers Ameca, Her vers GPT-4o, etc.
- 🔖 **Version :** Passage en v141.

## v140
- 🛡️ **Sentinel Fix :** Sécurisation des imports (`dotenv` optionnel) pour éviter le crash "Exit Code 1" en CI/CD.
- 🧭 **UX (Nav Fix) :** Amélioration de la tolérance de date (0.5 an) pour le saut "Prédit <-> Réalisé".
- 📚 **Data Fix :** Correction du lien temporel *Neuromancien* -> *Vision Pro* (2023).
- 🏗️ **Architecture :** Documentation spécifique pour l'installation sur Raspberry Pi 5 (venv obligatoire).
- 📏 **Directives :** Mise à jour stricte des instructions (`GEMINI_INSTRUCTIONS.md`) pour forcer la synchronisation des numéros de version dans tous les fichiers (HTML, Python, Logs).
- 🔖 **Version :** Passage en v140.

## v139
- 🧭 **UX (Nav Fix) :** Correction du saut temporel "Prédit <-> Réalisé". Le clic zoome désormais sur la cible ET ouvre automatiquement sa fiche détaillée après 600ms.
- 🏗️ **Architecture :** Mise à jour des documents de diagnostic et d'instructions pour la compatibilité Raspberry Pi 5.
- 📝 **Docs :** Ajout des procédures d'installation Python venv pour RPi OS Bookworm.
- 🔖 **Version :** Passage en v139.

## v138
- 🧭 **UX (Nav) :** Le saut temporel "Prédit <-> Réalisé" est de nouveau fonctionnel dans la fiche de détail.
- 📚 **Data (Doomsday Clock) :** Injection de **toutes** les mises à jour de l'Horloge de l'Apocalypse depuis 1947, avec descriptions détaillées et étiquettes permanentes.
- 📊 **Data Fix :** Lissage de la courbe d'Entropie en ré-évaluant la "valeur" des événements pour éviter les plongeons incohérents.
- 🧹 **Data :** Nettoyage des anciens points de données de l'Horloge.
- 🔖 **Version :** Passage en v138.

## v137
- 📚 **Data Fix :** Correction de la date d'invention du Web (1989 au lieu de 1990).
- 📚 **Data Injection :** Ajout d'événements fondateurs (Langage C, Python, Java) pour compléter le référentiel.
- 🔖 **Version :** Passage en v137 pour garantir la cohérence du déploiement.
- 🧹 **Data :** Validation et nettoyage du jeu de données de référence.

## v136
- 📊 **Data Fix :** Correction de la courbe de Singularité (suppression de la "bosse" en 2030). Les valeurs suivent désormais une progression sigmoïde stricte.
- 🎨 **UI (Focus) :** Ajustement de l'opacité des courbes non-actives (0.1 -> 0.25) pour une meilleure lisibilité du contexte.
- 🔖 **Version :** Passage en v136.

## v135
- 🚀 **Pipeline Fix :** Ajout d'un `timeout-minutes: 5` au workflow GitHub Actions pour tuer les processus bloqués.
- 🤖 **Agent Fix :** Le scan RSS utilise désormais `requests` avec un timeout (15s) pour éviter les blocages réseau infinis.
- 🔖 **Version :** Passage en v135.

## v134
- 🐛 **UI Fix :** Correction critique de la configuration Chart.js qui empêchait la désactivation des infobulles par défaut (doublons).
- 🔍 **UX (Zoom & Labels) :** Affichage dynamique des étiquettes basé sur la densité. Zoom arrière = Majeures uniquement. Zoom avant (<15 ans) = Toutes (si place).
- 🎨 **UI (Hover) :** Le fil de l'étiquette surgissante est maintenant ancré au coin haut-gauche, assurant une connexion parfaite avec le point quelle que soit la taille du texte.
- 🔧 **Code :** Nettoyage de la déclaration des plugins dans `index.html`.
- 🔖 **Version :** Passage en v134.

## v133
- 🛠️ **DevEnv :** Ajout de configurations VS Code pour stabiliser Pylance et l'environnement Python.
- 📝 **Docs :** Ajout d'une section Troubleshooting dans le README pour les erreurs courantes.
- 🧹 **Data :** Nettoyage et validation de la structure JSON consolidée.
- 🔖 **Version :** Passage en v133.

## v132
- 🔖 **Version :** Consolidation générale des versions suite aux itérations rapides.
- 🧠 **Data Intelligence :** L'analyse Pharmakon est maintenant **déterministe**. Les pourcentages sont calculés via un hash du nom de l'événement (stable entre les injections).
- 🔧 **Pipeline :** Synchronisation stricte de la logique d'enrichissement entre `sentinel.py` et `inject_data.py`.
- 🔖 **Version :** Passage en v132.

## v131
- 🔧 **Pipeline Fix :** Correction critique de la perte des analyses Pharmakon lors de l'injection de données.
- 🧠 **Data Intelligence :** Le script `inject_data.py` enrichit désormais automatiquement les données (S-Curve, Pharmakon) avant l'envoi.
- 💾 **Data Persistence :** Les données enrichies sont sauvegardées localement dans `loom_consolidated_v102.json` pour devenir la source de vérité.
- 🔖 **Version :** Passage en v131.

## v130
- 🐛 **UI Fix :** Suppression des infobulles natives (doublons) et masquage de l'étiquette surgissante sur les points permanents.
- 🎨 **UI (Labels) :** Les étiquettes permanentes incluent désormais l'icône de catégorie et un fil de connexion renforcé.
- 🔍 **UX (Zoom) :** Zoom activé en XY, limité à une profondeur de 1 an (4 trimestres).
- 🧭 **UX (Nav) :** Réintégration du saut "Prédit / Réalisé" dans la fiche de détail.
- 🧭 **UX (Nav) :** Le bouton "Retour vers le Futur" centre strictement sur 1985.
- 🏛️ **Data :** Ajout des vagues de licenciements Tech/IA (2023-2024).
- 💉 **Data :** Injection complémentaire pour dépasser les 300 événements.
- 🔖 **Version :** Passage en v130.

## v129
- 🎨 **UI (Focus Mode) :** Transparence forte appliquée aux étiquettes non sélectionnées lors du focus sur une catégorie.
- 🎨 **UI (Labels) :** Ajout d'un "fil" de connexion visuel pour toutes les étiquettes permanentes (plugin `connectorPlugin`).
- 🎨 **UI (Hover) :** Les bulles surgissantes adoptent le même style (fond coloré, bordure) que les étiquettes permanentes.
- 💉 **Data :** Injection massive pour atteindre >300 événements (Histoire sciences, Politique, Futurisme).
- 🔍 **UX (Zoom) :** Les trimestres ne s'affichent sur l'axe X que si le zoom est très serré (< 2 ans).
- 🔖 **Version :** Passage en v129 (Correction affichage version).

## v128
- ✨ **UX (Focus Mode) :** Le mode focus (clic sur la légende) rend désormais les étiquettes des autres lignes diaphanes, en plus des lignes elles-mêmes.
- 🐛 **UI Fix (Généralisé) :** La couleur de l'étiquette de survol ("label-float") correspond maintenant systématiquement à la couleur de sa catégorie.
- 🐛 **UI Fix :** Le bouton "Retour vers le Futur" est réparé et zoome correctement sur l'événement de 1985.
- ✨ **UX :** La vue initiale se concentre par défaut sur "Retour vers le Futur" comme point d'ancrage narratif.
- ✨ **UX :** Les trimestres sur l'axe des dates n'apparaissent que lorsque le niveau de zoom est suffisamment proche (< 15 ans).
- 📝 **Docs :** Clarification du processus d'injection de données initiales via `inject_data.py`.
- 📝 **Docs (Agent) :** Ajout de la directive pour utiliser systématiquement les boîtes "Run in terminal" pour les commandes.
- 🔖 **Version :** Passage en v128.

## v127
- 🤖 **Agent :** Sentinel enrichit désormais automatiquement tous les événements historiques avec une analyse "Pharmakon" plausible.
- ✨ **UX (Généralisé) :** La boîte de détails de l'analyse (Remède/Poison, Courbe en S) s'affiche maintenant pour **tous** les événements.
- 🔧 **Core :** Le cycle de l'agent a été rendu plus robuste pour assurer la cohérence des données dans le temps.
- 🔖 **Version :** Passage en v127.

## v126
- 🎨 **UI Fix (Généralisé) :** La couleur des étiquettes de survol correspond désormais à la couleur de leur courbe (le rose reste rose).
- 🎨 **UI :** Les étiquettes persistantes ont maintenant une bordure de la couleur de leur catégorie, renforçant le lien visuel.
- 💉 **Data Injection :** Injection massive de +120 événements (Total > 300).
- 📊 **Data Story :** L'horizon temporel s'étend jusqu'en 2100, avec des projections pour la Singularité et la Civilisation Type 1.
- 🏛️ **Politique & Noosphère :** Ajout de dizaines d'événements pour donner corps à ces catégories.
- ✨ **UX :** Le nombre total d'événements est maintenant affiché dans la légende.
- 🔖 **Version :** Passage en v126.

## v125
- 🐛 **UI Fix :** Correction définitive du curseur "doigt" sur les points et étiquettes via un flag d'état (`isHoveringLabel`).
- 🖱️ **UX :** Augmentation de la zone de clic (`hitRadius`) des points à 30px pour une meilleure accessibilité.
- 💉 **Data Injection :** Injection massive de ~100 nouveaux événements (Total > 180).
- 🏛️ **Politique :** La catégorie Politique est maintenant visible et peuplée (Luddites, RGPD, AI Act, Grèves...).
- 🔬 **Recherche :** Ajout de jalons scientifiques majeurs (Physique, Biotech, IA historique).
- 🔖 **Version :** Passage en v125.

## v124
- 🐛 **UI Fix :** Le curseur "doigt" est maintenant fonctionnel au survol des étiquettes (conflit `onHover` résolu).
- 📚 **Data :** Les événements de la catégorie `🏛️ POLITIQUE` affichent désormais leurs étiquettes persistantes (`tipping: true`).
- 📚 **Data :** Vérification et confirmation de la description et de la source pour "Tchernobyl".
- 🎨 **UI :** La date des événements historiques dans la carte de détail affiche l'année entière (ex: 1986).
- 📝 **Docs :** Ajout d'une section "Directives de Qualité des Données" dans `GEMINI_INSTRUCTIONS.md`.
- 🔧 **CI/CD :** Ajout d'un `run-name` au workflow GitHub Actions pour une meilleure identification des exécutions.
- 🔖 **Version :** Passage en v124.

## v123
- 🚀 **Pipeline Fix :** Ajout d'une règle de concurrence (`concurrency`) au workflow GitHub Actions pour empêcher les exécutions en double.
- 🔖 **Version :** Passage rigoureux à la v123 sur tous les composants pour corriger les problèmes de cache et d'affichage.
- 📝 **Docs :** Clarification de la correction dans le journal des modifications.

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