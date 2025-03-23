# Projet simplon

Ce projet implémente une solution d'analyse de données de ventes pour une PME, utilisant une architecture à deux services Docker pour le traitement et le stockage des données.

## 🏗 Architecture

Le projet utilise une architecture à deux services avec une configuration réseau et un flux de données complet :

### Configuration des Services

1. **Service Python (Analyse_des_resultats)**
    - Port: 5000 (réservé pour futures extensions API)
    - Port: 7860 (interface web Gradio)
    - Accès: Web interface accessible depuis l'extérieur
    - Communication: Bidirectionnelle avec SQLite via volumes Docker

2. **Service SQLite (sqlite_service)**
   - Port: Non exposé
   - Accès: Interne uniquement
   - Communication: Via volumes Docker partagés

### Flux de Données

```mermaid
flowchart TD
    SCHED[Scheduler 12h/00h] -->|Déclenche| FETCH[Data Fetcher]
    CSV1[Ventes CSV] -->|Import| FETCH
    CSV2[Produits CSV] -->|Import| FETCH
    CSV3[Magasins CSV] -->|Import| FETCH
    
    FETCH -->|Import données| PS[Python Service]
    PS -->|Import données| DB[(SQLite DB)]
    PS <-->|Requêtes| DB
    
    DB -->|Analyses| AN[Analyses]
    AN -->|Résultats| LOG[Logs]
    AN -->|Données| DASH[Dashboard]
    
    subgraph Interface Web
        DASH -->|Ventes| VIZ1[Visualisation Ventes]
        DASH -->|RH| VIZ2[Visualisation RH]
        DASH -->|Produits| VIZ3[Visualisation Produits]
    end
```

Le système est composé de :
- **Service Python** : Conteneur exécutant les scripts d'import et d'analyse
- **Service SQLite** : Base de données stockant et servant les données
- **Flux de Données** : Pipeline automatisé depuis Google Sheets jusqu'aux analyses

## 📁 Structure du projet

```
.
├── docker-compose.yml
├── src/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── web_app.py
│   ├── viz-config-ventes.json
│   ├── viz-config-magasins.json
│   ├── viz-config-produits.json
│   ├── data_fetcher.log
├── data/
│   ├── analysis.db
└── README.md
```

Les fichiers de configuration viz-config-*.json contiennent les paramètres de visualisation pour chaque tableau de bord.

## 🗃 Structure des données

Le modèle de données suit une structure relationnelle avec trois tables principales :

```mermaid
erDiagram
    MAGASINS ||--o{ VENTES : "réalise"
    PRODUITS ||--o{ VENTES : "concerne"
    
    MAGASINS {
        integer ID_Magasin PK "Primary Key"
        string Ville
        integer Nombre_de_salaries
    }
    
    PRODUITS {
        string ID_Reference_produit PK "Primary Key"
        string Nom
        decimal Prix
        integer Stock
    }
    
    VENTES {
        date Date PK "Part of composite PK"
        string ID_Reference_produit FK "FK & Part of composite PK"
        integer ID_Magasin FK "FK & Part of composite PK"
        integer Quantite
    }
```

Caractéristiques principales :
- Table **VENTES** avec clé primaire composite sur trois champs (Date, ID_Reference_produit, ID_Magasin)
- Relations one-to-many entre MAGASINS/PRODUITS et VENTES
- Table **PRODUITS** gérant le catalogue (prix, stocks)
- Table **MAGASINS** stockant les informations géographiques et RH
- Intégrité référentielle assurée par les clés étrangères

## 🚀 Installation

1. Construire et démarrer les services :
```bash
docker-compose up --build
```

2. Interagir avec le docker SQlite
```bash
docker exec -it sqlite_service sqlite3 /db/analysis.db
```

## 📊 Fonctionnalités

### Import des données
- Import automatique et régulier des liens Google Sheets (12h et 00h heure de Paris)
- Gestion des doublons
- Validation des données
- Logging détaillé des opérations d'import

### Analyses disponibles
1. **Analyses temporelles**
   - Évolution des ventes quotidiennes
   - Tendances par période
   - Jours de forte/faible activité

2. **Analyses spatiales**
   - Performance par magasin
   - Distribution géographique des ventes
   - Corrélation taille équipe/performance

3. **Analyses produits**
   - Top des produits vendus
   - Rotation des stocks
   - Chiffre d'affaires par produit

## 🛠 Technologies utilisées

- Python 3.11
- SQLite3
- Docker & Docker Compose
- Pandas pour le traitement des données
- Schedule pour la planification des tâches
- Pytz pour la gestion des fuseaux horaires
- Gradio pour l'interface web interactive
- PyGWalker pour les visualisations de données

## 📊 Dashboard Web

Le projet inclut une interface web interactive accessible via Gradio qui propose trois sections principales :

### 1. Analyse des ventes 📈
- Visualisations détaillées des performances de vente
- Graphiques temporels et tendances
- Filtres interactifs pour l'analyse

### 2. RH & Magasins 👥
- Performances par magasin
- Analyse des effectifs
- Comparaisons et métriques clés

### 3. Catalogue produits 📦
- Vue d'ensemble du catalogue
- Statistiques de vente par produit
- Analyse des stocks

### Accès au dashboard
```bash
# Le dashboard est accessible sur le port 7860
http://localhost:7860
```

Caractéristiques :
- Interface intuitive avec onglets
- Visualisations interactives
- Filtres dynamiques
- Mise à jour automatique avec les dernières données

##  Utilisation

1. **Importer les données**
```bash
docker-compose exec scripts python import_data.py
```

2. **Lancer les analyses**
```bash
docker-compose exec scripts python analyze_data.py
```

## 🔍 Monitoring et maintenance

- Les logs sont disponibles via Docker
- Logs détaillés des imports programmés dans `data_fetcher.log`
  * Imports automatiques à 12h et 00h (heure de Paris)
  * Statut des opérations d'import
  * Résultats des analyses
- Les résultats d'analyses sont stockés dans la table `analyses_resultats`
- Backups automatiques de la base de données
- Surveillance des tâches programmées via les logs Docker
  ```bash
  docker logs -f Analyseur
  ```
