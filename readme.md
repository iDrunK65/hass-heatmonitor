# Fichier : `custom_components/heat_monitor/README.md`

# Temperature Monitor (heat_monitor)
Petite integration Home Assistant pour surveiller la température et exposer des binary_sensors.

## Description
L'intégration `heat_monitor` fournit des capteurs de température et des binary_sensors pour détecter des seuils de température. Conçue pour être ajoutée comme custom component dans Home Assistant. Configuration via l'interface (config flow).

## Caractéristiques
- Domaine : `heat_monitor`
- Nom : Temperature Monitor
- Version : 0.0.1
- Type IOT : local_push
- Configuration : interface (config flow) — pas de YAML nécessaire

## Installation (utilisateur Home Assistant)
1. Copier le dossier `heat_monitor` dans `custom_components/` de votre configuration Home Assistant :
   - `config/custom_components/heat_monitor/`
2. Redémarrer Home Assistant.
3. Aller dans Configuration → Intégrations → Ajouter une intégration → chercher "Temperature Monitor" et suivre l'assistant.

## Configuration
- Aucun YAML requis. Utiliser l'assistant d'ajout dans l'interface.
- Paramètres disponibles (selon implémentation) : seuils de température, options de notification, etc.

## Fichiers importants
- `__init__.py` — initialisation de l'intégration
- `binary_sensor.py` — définition des binary sensors
- `config_flow.py` — flux d'ajout via l'interface
- `const.py` — constantes
- `manifest.json` — métadonnées de l'intégration

## Développement & Débogage
- Vérifier les logs Home Assistant pour les erreurs au démarrage.
- Travailler depuis un environnement virtuel Python sur macOS (IntelliJ IDEA est utilisable).
- Auteur / Mainteneur : `@iDrunK65`
- Documentation : https://example.com/temp_monitor

---

# Fichier : `README.md` (racine du dépôt)

# HA-Tempalert — Temperature Monitor (custom component)
Composant personnalisé Home Assistant pour la surveillance de température (nom interne `heat_monitor`).

## Objectif
Fournir des capteurs et alertes simples basés sur la température pour Home Assistant, facilement installables via `custom_components`.

## Structure du dépôt
- `custom_components/heat_monitor/` — code de l'intégration
  - `__init__.py`
  - `binary_sensor.py`
  - `config_flow.py`
  - `const.py`
  - `manifest.json`

## Installation
1. Copier le dossier `custom_components/heat_monitor` dans le répertoire `custom_components` de votre instance Home Assistant :
   - `config/custom_components/heat_monitor/`
2. Redémarrer Home Assistant.
3. Ajouter l'intégration via l'interface (Configuration → Intégrations).

## Développement (rapide)
1. Sur macOS, créer un environnement virtuel :
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Ouvrir le projet dans IntelliJ IDEA 2025.2.
3. Modifier le code dans `custom_components/heat_monitor/`.
4. Tester en rechargeant Home Assistant et en surveillant les logs.

## Contributeurs
- Mainteneur principal : `@iDrunK65`

## Licence
Ajouter la licence souhaitée (ex : MIT) dans un fichier `LICENSE` à la racine si nécessaire.

## Documentation
Documentation utilisateur : https://example.com/temp_monitor