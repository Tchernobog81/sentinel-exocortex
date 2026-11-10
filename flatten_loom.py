import os
from pathlib import Path

# --- CONFIGURATION (Ajuste selon ton projet) ---
# Dossiers à ignorer absolument (pour ne pas saturer l'IA avec du bruit)
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules', '.vscode', 'build', 'dist', 'public'}
# Fichiers spécifiques à ignorer
EXCLUDE_FILES = {'flatten_loom.py', 'loom_context.md', 'package-lock.json', 'yarn.lock'}
# Extensions de fichiers à inclure (ajoute .tsx ou .jsx si tu utilises React)
EXTENSIONS = {'.py', '.json', '.js', '.jsx', '.ts', '.tsx', '.md', '.txt', '.yaml', '.yml', '.html', '.css'}
OUTPUT_FILE = "loom_context.md"

def flatten_repo(root_path):
    root = Path(root_path)
    output = []
    
    # 1. GÉNÉRATION DE L'ARBORESCENCE (Vue globale pour l'IA)
    output.append("# 🧵 ARCHITECTURE GLOBALE : THE LOOM\n")
    output.append("Voici l'arborescence complète du projet pour comprendre comment les fichiers interagissent :\n")
    output.append("```text")
    for path in sorted(root.rglob('*')):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        depth = len(path.relative_to(root).parts) - 1
        spacer = '  ' * depth
        icon = '📂 ' if path.is_dir() else '📄 '
        output.append(f"{spacer}{icon}{path.name}")
    output.append("```\n\n---\n")
    output.append("# 💾 CODE SOURCE COMPLET\n\n")

    # 2. EXTRACTION DU CONTENU DES FICHIERS
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.suffix in EXTENSIONS:
            # Vérification des exclusions
            if any(part in EXCLUDE_DIRS for part in path.parts) or path.name in EXCLUDE_FILES:
                continue
            
            relative_path = path.relative_to(root)
            print(f"Ingestion de : {relative_path}")
            
            output.append(f"## FICHIER : `{relative_path}`")
            
            # Détermination du langage pour le formatage Markdown
            lang = path.suffix[1:] if path.suffix else "text"
            if lang in ['jsx', 'tsx']: lang = 'javascript' # Alias pour le rendu
                
            output.append(f"```{lang}")
            try:
                # Lecture en UTF-8 (ignore les erreurs d'encodage bizarres)
                content = path.read_text(encoding='utf-8', errors='replace')
                output.append(content)
            except Exception as e:
                output.append(f"// Erreur lors de la lecture du fichier : {e}")
            output.append("```\n\n---\n")

    # 3. ÉCRITURE DU FICHIER FINAL
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output))
        print(f"\n✅ Terminé ! Le condensé complet est dans : {OUTPUT_FILE}")
        print(f"📊 Taille approximative : {os.path.getsize(OUTPUT_FILE) / 1024:.2f} KB")
    except Exception as e:
         print(f"\n❌ Erreur lors de l'écriture du fichier final : {e}")

if __name__ == "__main__":
    print("Début de l'aplatissement du dépôt...")
    flatten_repo(".")
