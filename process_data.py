import json
from collections import defaultdict

# --- CONFIGURATION ---
INPUT_FILE = "loom_consolidated_v102.json"
OUTPUT_FILE = "loom_data.json"

# Palette de couleurs pour les catégories (strands)
CATEGORY_COLORS = {
    "🔴 RÉSEAU": "#ef4444",
    "🟡 HARDWARE": "#f59e0b",
    "🔵 COGNITION": "#3b82f6",
    "🟢 BIOTECH": "#22c55e",
    "🟣 ESPACE": "#8b5cf6",
    "🔮 IMAGINAIRE": "#a855f7",
    "☢️ ENTROPIE": "#f43f5e",
    "⚪ SINGULARITÉ": "#ffffff",
    "☠️ RISQUE": "#9ca3af" # Nouvelle catégorie
}

def get_color(category):
    """Retourne la couleur pour une catégorie donnée, avec une couleur par défaut."""
    return CATEGORY_COLORS.get(category, "#6b7280") # Gris par défaut

def process_and_restructure_data():
    """
    Charge les données plates, les restructure en 'strands' par catégorie,
    ajoute la nouvelle ligne "Risque" et sauvegarde le résultat.
    """
    # 1. Charger les données existantes
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            flat_data = json.load(f)
        print(f"-> Fichier '{INPUT_FILE}' chargé ({len(flat_data)} événements).")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERREUR: Impossible de charger ou parser '{INPUT_FILE}': {e}")
        return

    # 2. Grouper les événements par catégorie
    strands_map = defaultdict(list)
    for event in flat_data:
        category = event.get("category", "INCONNUE")
        strands_map[category].append(event)
    print(f"-> {len(strands_map)} catégories trouvées.")

    # 3. Créer la nouvelle ligne "Risque" avec les données de l'Horloge de l'Apocalypse
    # Source: recherche web précédente. 'value' est arbitraire pour le positionnement Y.
    doomsday_clock_events = [
        {"year": 1947, "value": 100, "label": "Horloge créée (7 min)", "how": "Début de l'âge nucléaire."},
        {"year": 1953, "value": 100, "label": "2 min avant minuit", "how": "Essais de la bombe H (USA/URSS)."},
        {"year": 1991, "value": 100, "label": "Recul à 17 min", "how": "Fin de la Guerre Froide, signature du traité START I."},
        {"year": 2007, "value": 100, "label": "Le climat inclus (5 min)", "how": "Le changement climatique devient un facteur clé."},
        {"year": 2020, "value": 100, "label": "100 secondes", "how": "Guerre nucléaire, climat et désinformation."},
        {"year": 2023, "value": 100, "label": "90 secondes", "how": "Guerre en Ukraine, menaces nucléaires accrues."},
        {"year": 2026, "value": 100, "label": "85 secondes", "how": "Risques nucléaires, climatiques et IA incontrôlée."}
    ]
    
    # Ajoute chaque événement au format attendu par le graphique
    for event in doomsday_clock_events:
        event["category"] = "☠️ RISQUE"
        strands_map["☠️ RISQUE"].append(event)
    print(f"-> Nouvelle catégorie '☠️ RISQUE' ajoutée avec {len(doomsday_clock_events)} événements.")

    # 4. Construire la structure finale de 'strands'
    final_strands = []
    for category_name, events in strands_map.items():
        # Trie les événements par année pour cette catégorie
        sorted_events = sorted(events, key=lambda x: x.get('year', 0))
        
        final_strands.append({
            "name": category_name,
            "color": get_color(category_name),
            "events": sorted_events
        })
    
    # Trier les strands par nom pour un ordre cohérent
    final_strands = sorted(final_strands, key=lambda x: x['name'])
    
    output_data = {"strands": final_strands}

    # 5. Sauvegarder le nouveau fichier JSON
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"-> Données restructurées et sauvegardées dans '{OUTPUT_FILE}'.")
    except IOError as e:
        print(f"ERREUR: Impossible d'écrire dans '{OUTPUT_FILE}': {e}")

if __name__ == "__main__":
    print("--- Début du script de transformation des données du Loom ---")
    process_and_restructure_data()
    print("--- Script terminé. ---")
