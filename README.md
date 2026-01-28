# Cortex Loom : Exocortex & Veille Technologique

Visualisation interactive et agent de veille pour suivre l'avènement des singularités technologiques.

## 🚀 Installation Rapide

1.  **Cloner le dépôt :**
    ```bash
    git clone <votre-repo-url>
    cd Cortex_Loom
    ```

2.  **Installer les dépendances Python :**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurer l'environnement :**
    *   Créez un fichier `.env` à la racine.
    *   Ajoutez votre `CLOUD_URL` (URL du script Google Apps).

## 🛠️ Utilisation

*   **Lancer l'agent Sentinel (Veille) :**
    ```bash
    python sentinel.py
    ```
*   **Injecter les données initiales (Reset) :**
    ```bash
    python inject_data.py
    ```
*   **Visualisation :** Ouvrez `index.html` dans votre navigateur.

## 🐛 Troubleshooting (Dépannage)

### Erreurs Pylance / VS Code
Si vous voyez des erreurs comme `Unhandled Rejection in Pylance` ou `File or directory not found` :
1.  Assurez-vous d'avoir ouvert le **dossier racine** `Cortex_Loom` dans VS Code.
2.  Redémarrez le serveur de langage : `Ctrl+Shift+P` > `Python: Restart Language Server`.
3.  Vérifiez que votre interpréteur Python est bien sélectionné (en bas à droite de VS Code).

### Erreurs de Script
*   `ModuleNotFoundError` : Lancez `pip install -r requirements.txt`.
*   `CLOUD_URL missing` : Vérifiez votre fichier `.env`.