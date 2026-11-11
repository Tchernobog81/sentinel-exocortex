# DIRECTIVES AGENT LOCAL — Sentinel Exocortex / Cortex Loom (v162)

Ce fichier est la référence unique pour toute évolution du projet. Toute modification doit le respecter.

## 0. Règle d'or : TESTER AVANT DE PROPOSER
Avant chaque version proposée/poussée, exécuter la **suite d'interactions complète en navigateur virtuel**
(headless Chromium via playwright-core + chrome-headless-shell, voir /tmp/pwtest/) :
chargement sans erreur, 8 courbes, 8 chips, isolement par clic (1er clic = isole, re-clic = tout réaffiche),
clic item flux → zoom + popup, clic point → popup fondu, Échap ferme, recherche filtre, wheel zoom, drag pan,
double-clic reset, nav ⇄ prédit/réalisé, viewport mobile 390px (burger, pas de débordement), 0 pageerror.
Ne jamais pousser une version non testée en navigateur.

## 1. Versioning (à chaque correction/évolution)
Incrémenter le numéro de version et mettre à jour systématiquement :
`CHANGELOG.md` (entrée en tête), `index.html` (title, SYSTEM BOOT, Init, brand-version),
`sentinel/sentinel.py` (`VERSION = "vXXX"` + logs), `.github/workflows/static.yml` (`run-name: The Loom vXXX 🚀`).
Commit + push sur `main` (remote SSH `git@github.com:Tchernobog81/sentinel-exocortex.git`, identité Tchernobog81).

## 2. Données
- **Tout événement doit être enrichi** : `description` factuelle (≥30 caractères), `whoWhat` (source/acteur),
  analyse Pharmakon (s_curve_phase, remède/poison, convergences, grand_filter, final_note). Jamais de "N/A"/"?".
  - À l'ingestion (sentinel) : tout nouvel événement passe par `enrich_event_if_needed` + LLM si description vide.
  - En masse : `scripts/enrich_events.py` (LLM local par lots de 8, fallback par catégorie) après chaque gros seed.
- **FACT-CHECK systématique** : toute info entrante est corroborée par recherche web
  (`factcheck()` dans sentinel : ≥2 sources ou mot-clé retrouvé, sinon l'événement est ignoré et logué ;
  champ `verified` ; le flux n'affiche que `verified != false`). Côté données : `scripts/factcheck.py`
  supprime les claims non sourcés (futur + sans description, ou sans aucune info).
- **Faits avérés uniquement** dans le flux 12h : RSS multi-requêtes + filtre anti-hype (mots-clés factuels :
  benchmark/record/prouvé/résolu/découvert/conjecture…), dédoublonné par titre, pas de dates futures,
  tri chrono décroissant, fiction exclue du flux. Simulateur OFF par défaut (`SIMULATOR=1` pour l'activer).
- **Fictions toujours liées ⇄ au réel** : `realYear` côté fiction, `predictedBy` côté réel (popups ⇄ cliquables).
- Seeds verrouillés (fcntl), idempotents (upsert par id stable sha1), écriture tmp+os.replace.
- Le miroir local du sentinel ne s'écrit QUE si l'API est down, et n'upsert que les NOUVEAUX événements
  (ne jamais écraser un snapshot périmé sur des champs enrichis realYear/predictedBy).
- HTML interdit dans les champs texte : nettoyé à l'ingestion (sentinel `clean_text`) et à l'API (backend `_clean_text`).
- Catégories d'origine conservées dans les données ; le regroupement en 8 courbes se fait AU RENDU (GROUP_OF).

## 3. Backend FastAPI (port 8000)
- Upsert idempotent par `id` stable ; écriture atomique + verrou fichier (flock) ; backups auto (10) + restore ;
  `GET /api/data?since=` ; réponses aplaties avec alias legacy (`pharmakon_*`).
- Champs préservés de bout en bout : `id, year, value, label, category, whoWhat, description, url, timestamp,
  tipping, realYear, predictedBy, img, analysis*`.

## 4. Front (index.html)
- 8 courbes regroupées : ⚙️ INDUSTRIE & ROBOTS, 🚀 ESPACE, 🧠 IA & COGNITION, 🌍 NOOSPHÈRE & RÉSEAUX,
  🧬 VIVANT & SANTÉ, 🏛️ POLITIQUE, ☢️ ENTROPIE & CYBER, 🎬 FICTION. Clic chip = isolement réversible.
- Popups : au CLIC uniquement (jamais au survol), ouverture en fondu 250 ms, Échap/clic dehors ferme.
- Flux cliquable (saut zoom + popup), hauteur = pleine hauteur navigateur, refresh auto 60 s.
- Auto-zoom vers les nouveautés UNIQUEMENT si l'utilisateur n'a pas navigué (userNavigated).
- Zoom molette/pinch + pan glisser en xy (double-clic = reset) ; décimation adaptative des étiquettes selon densité ;
  axe X en jour/mois/année selon le zoom ; ligne « MAINTENANT » ; recherche textuelle ; widget Horloge de l'Apocalypse.
- Responsive : ≤760px burger ☰, sidebar off-canvas, popup plein écran.

## 5. Sentinel (agent de veille, boucle ~60 s)
- Analyse Pharmakon v117 par LLM local Ollama outillé (`web_search`/`fetch_url`), focus AI2027,
  modèle `hermes3:8b`, fallback `qwen3:8b` (config `.env` : OLLAMA_URL/OLLAMA_MODEL/ANALYSIS_MODE).
- Horloge de l'Apocalypse scrapée à chaque cycle depuis thebulletin.org (label stable par année → upsert).
- Boucle : `scripts/run_push_agent.sh` — cycle sentinel → commit+push `loom_data.json` sur main UNIQUEMENT si changé.
- Ne jamais push de version non testée en navigateur virtuel (règle 0).

## 6. Pipeline CI/CD
- GitHub Pages se déploie sur push main via `static.yml` (concurrency group "pages" = déploiements sérialisés).
- Les commits faits avec le GITHUB_TOKEN (bot) ne redéclenchent pas les workflows `on: push` → ne pas compter dessus.
- Recommandé : workflow de validation JSON (jq + schéma) en amont du deploy. Secrets jamais en clair.
- Scraping sur le Mac (push SSH), PAS de self-hosted runner GitHub (déconseillé sur repo public, bientôt payant).
