# Heat Monitor

Intégration personnalisée Home Assistant pour la surveillance de température avec alertes configurables.

## 🎯 Intention

**Heat Monitor** permet de surveiller la température d'un capteur et de recevoir des alertes lorsque celle-ci sort d'une plage définie. L'intégration crée un appareil complet avec :

- Un **binary_sensor** qui indique si la température est hors plage
- Deux entités **number** pour ajuster dynamiquement les seuils min/max depuis l'interface
- Des **événements** sur le bus Home Assistant pour déclencher des automatisations

Idéal pour surveiller des températures critiques (serveurs, caves à vin, serres, etc.) et déclencher des actions automatiques.

## ✨ Fonctionnalités

- ✅ Configuration via l'interface (config flow) — pas de YAML requis
- ✅ Surveillance en temps réel de la température
- ✅ Binary sensor qui passe à `on` lorsque la température sort de la plage
- ✅ Ajustement dynamique des seuils min/max via des entités number
- ✅ Persistance des seuils (conservés après redémarrage)
- ✅ Événements sur le bus pour les automatisations
- ✅ Regroupement des entités dans un seul appareil

## 📦 Installation

### Méthode 1 : Installation manuelle

1. Copier le dossier `custom_components/heat_monitor` dans votre configuration Home Assistant :
   ```
   config/custom_components/heat_monitor/
   ```

2. Redémarrer Home Assistant

3. Aller dans **Paramètres** → **Appareils & Services** → **Ajouter une intégration**

4. Rechercher **"Heat Monitor"** et suivre l'assistant de configuration

### Méthode 2 : Via HACS (si disponible)

1. Ajouter ce dépôt dans HACS
2. Installer depuis l'interface HACS
3. Redémarrer Home Assistant

## ⚙️ Configuration

Lors de l'ajout de l'intégration, vous devrez fournir :

- **Nom** : Nom de votre moniteur (optionnel, généré automatiquement si vide)
- **Capteur de température** : Sélection d'un capteur avec `device_class: temperature`
- **Température minimale** : Seuil bas (par défaut : 5.0 °C)
- **Température maximale** : Seuil haut (par défaut : 30.0 °C)

### Exemple de configuration

```
Nom : "Cave à vin"
Capteur : sensor.cave_temperature
Min : 10.0 °C
Max : 15.0 °C
```

## 📊 Entités créées

Pour chaque configuration, l'intégration crée un appareil avec 3 entités :

### 1. Binary Sensor (`binary_sensor.[nom]_alert`)

- **Device class** : `problem`
- **État** :
  - `off` : Température dans la plage [min, max]
  - `on` : Température hors plage
- **Attributs** :
  - `sensor` : Entity ID du capteur surveillé
  - `min_temp` : Seuil minimal actuel
  - `max_temp` : Seuil maximal actuel
  - `current_temp` : Température actuelle
  - `in_range` : Booléen indiquant si la température est dans la plage

### 2. Number - Température minimale (`number.[nom]_min_temp`)

- Permet d'ajuster le seuil minimal depuis l'interface
- Plage : -50.0 à 80.0 °C
- Pas : 0.5 °C
- La valeur est persistée dans la configuration

### 3. Number - Température maximale (`number.[nom]_max_temp`)

- Permet d'ajuster le seuil maximal depuis l'interface
- Plage : -50.0 à 80.0 °C
- Pas : 0.5 °C
- La valeur est persistée dans la configuration

## 🔔 Événements

L'intégration émet deux types d'événements sur le bus Home Assistant :

### `heat_monitor_out_of_range`

Émis lorsque la température sort de la plage définie.

**Données de l'événement** :
```yaml
monitor_entity_id: binary_sensor.cave_alert
sensor_entity_id: sensor.cave_temperature
current_temp: 8.5
min_temp: 10.0
max_temp: 15.0
reason: "below_min"  # ou "above_max"
entry_id: "abc123..."
```

### `heat_monitor_back_in_range`

Émis lorsque la température revient dans la plage.

**Données de l'événement** :
```yaml
monitor_entity_id: binary_sensor.cave_alert
sensor_entity_id: sensor.cave_temperature
current_temp: 12.0
min_temp: 10.0
max_temp: 15.0
entry_id: "abc123..."
```

## 🤖 Automatisations

### Exemple 1 : Notification lors d'alerte

```yaml
automation:
  - alias: "Alerte température cave"
    trigger:
      platform: event
      event_type: heat_monitor_out_of_range
      event_data:
        monitor_entity_id: binary_sensor.cave_alert
    action:
      - service: notify.mobile_app
        data:
          message: >
            Température hors plage !
            Actuelle: {{ trigger.event.data.current_temp }}°C
            Plage: {{ trigger.event.data.min_temp }}-{{ trigger.event.data.max_temp }}°C
            Raison: {{ trigger.event.data.reason }}
```

### Exemple 2 : Activer un chauffage si trop froid

```yaml
automation:
  - alias: "Chauffage si température trop basse"
    trigger:
      platform: event
      event_type: heat_monitor_out_of_range
      event_data:
        reason: "below_min"
    condition:
      condition: template
      value_template: "{{ trigger.event.data.monitor_entity_id == 'binary_sensor.cave_alert' }}"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.chauffage_cave
```

### Exemple 3 : Désactiver le chauffage quand retour à la normale

```yaml
automation:
  - alias: "Arrêt chauffage si température OK"
    trigger:
      platform: event
      event_type: heat_monitor_back_in_range
      event_data:
        monitor_entity_id: binary_sensor.cave_alert
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.chauffage_cave
```

## 🏗️ Structure technique

```
custom_components/heat_monitor/
├── __init__.py          # Initialisation et gestion des config entries
├── manifest.json        # Métadonnées de l'intégration
├── const.py             # Constantes (domaine, événements, etc.)
├── config_flow.py       # Assistant de configuration UI
├── binary_sensor.py      # Entité binary_sensor d'alerte
└── number.py            # Entités number pour min/max
```

### Architecture

- **Domaine** : `heat_monitor`
- **Plateformes** : `binary_sensor`, `number`
- **Type IOT** : `local_push` (pas de connexion externe)
- **Persistance** : Les seuils min/max sont sauvegardés dans la config entry

## 🔧 Développement

### Prérequis

- Python 3.9+
- Home Assistant 2025.1.0+

### Structure du projet

```bash
HA-Tempalert/
├── custom_components/
│   └── heat_monitor/     # Code de l'intégration
├── readme.md             # Ce fichier
└── hacs.json             # Configuration HACS (si applicable)
```

### Tests locaux

1. Copier `custom_components/heat_monitor` dans votre instance Home Assistant
2. Redémarrer Home Assistant
3. Vérifier les logs pour d'éventuelles erreurs :
   ```bash
   tail -f home-assistant.log | grep heat_monitor
   ```

### Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Faire vos modifications
4. Tester localement
5. Soumettre une pull request

## 📝 Notes

- Les valeurs min/max sont persistées dans la configuration et conservées après redémarrage
- Les événements ne sont émis que lors des **transitions** (pas au démarrage)
- Le binary_sensor se met à jour automatiquement lorsque les seuils sont modifiés via les entités number
- Un seul moniteur par capteur (détection de doublons via unique_id)

## 👤 Auteur

**@iDrunK65**


## 🔗 Liens

- Documentation : [GitHub](https://github.com/iDrunK65/hass-heatmonitor)
- Issues : [GitHub Issues](https://github.com/iDrunK65/hass-heatmonitor/issues)

