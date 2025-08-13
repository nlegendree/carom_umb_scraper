# 🎱 UMB Carom Scraper - Structure du Projet

## 📁 Organisation des fichiers

```
carom_umb_scraper/
├── main.py                     # Script principal d'orchestration
├── pyproject.toml              # Configuration du projet Python
├── CLAUDE.md                   # Instructions pour Claude
├── PROJECT_STRUCTURE.md        # Ce fichier
├── 
├── config/                     # 📋 Configurations
│   ├── player.json            # 👤 Données du joueur (À COMPLÉTER)
│   └── bot_config.json        # ⚙️ Configuration des bots
├── 
├── data/                      # 📊 Données scrapées
│   ├── umb_tournaments.json   # Base de données des tournois
│   ├── umb_tournaments.csv    # Export CSV
│   ├── umb_tournaments_future.json  # Tournois futurs uniquement
│   └── umb_tournaments_future.csv
├── 
├── logs/                      # 📝 Logs des bots
│   └── (logs générés automatiquement)
├── 
└── src/                       # 💻 Code source
    ├── scraper/               # Module principal de scraping
    │   ├── __init__.py
    │   ├── scraper.py         # Scraper principal
    │   └── config_manager.py  # Gestionnaire de configuration
    └── bots/                  # 🤖 Bots d'inscription
        ├── __init__.py
        ├── base_bot.py        # Classe de base pour bots
        ├── curl_bot.py               # Bot cURL (ultra-rapide)
        ├── selenium_bot.py           # Bot Selenium
        └── extension_bot.js   # Extension navigateur
```

## 🚀 Workflow complet

### 1. Configuration initiale
```bash
# Compléter vos données personnelles
nano config/player.json
```

### 2. Scraping des tournois
```bash
# Scraper tous les tournois (ou mise à jour sélective)
python main.py scrape
```

### 3. Identifier les World Cups
```bash
# Voir les World Cups futures avec dates d'inscription
python main.py world-cups
```

### 4. Configurer un bot pour un tournoi
```bash
# Générer la config pour le tournoi 362
python main.py setup-bot 362
```

### 5. Lancer l'inscription automatique
```bash
# Bot cURL (recommandé - plus rapide)
cd src/bots
python curl_bot.py --config ../../config/tournament_362.json

# Ou bot Selenium (backup)
python selenium_bot.py --config ../../config/tournament_362.json
```

## ⚙️ Configuration

### config/player.json
**❗ IMPORTANT: À compléter avec vos données**
```json
{
  "player_data": {
    "federation": "109",           // Fédération Française = 109
    "lastName": "VOTRE_NOM",
    "firstName": "VOTRE_PRENOM",
    "playerId": "VOTRE_ID",
    "nationality": "216",          // France = 216
    "dateOfBirth": "DD/MM/YYYY",
    "country": "216",              // France = 216
    "city": "VOTRE_VILLE",
    "address": "VOTRE_ADRESSE",
    "phone": "VOTRE_TELEPHONE",
    "email": "VOTRE_EMAIL",
    "contactFax": ""
  }
}
```

### config/bot_config.json
Configuration générale des bots (déjà configuré)

## 🎯 Cas d'usage typique

1. **Une fois par semaine** : `python main.py scrape` pour mettre à jour
2. **Quand nouvelle World Cup** : `python main.py world-cups` pour voir
3. **8 semaines avant** : `python main.py setup-bot <ID>` puis lancer le bot
4. **Le jour J** : Le bot surveille et s'inscrit automatiquement à 12h GMT Paris

## 🔧 Commandes disponibles

```bash
python main.py scrape              # Lance le scraping
python main.py world-cups          # Affiche World Cups futures  
python main.py setup-bot 362       # Configure bot pour tournoi 362
python main.py config              # Vérifie la configuration
```

## 📊 Types de fichiers de données

- **umb_tournaments.json** : Base complète (328+ tournois)
- **umb_tournaments_future.json** : Tournois futurs uniquement
- **tournament_362.json** : Config spécifique pour bot tournoi 362

## 🤖 Choix du bot

1. **curl_bot.py** - Recommandé
   - ⚡ Ultra-rapide (50ms checks)
   - 🎯 Gestion tokens ASP.NET
   - 📱 Léger, pas de navigateur

2. **selenium_bot.py** - Backup
   - 🖥️ Interface navigateur visible
   - 🐛 Meilleur pour debugging
   - 📸 Screenshots automatiques

3. **extension_bot.js** - Manuel
   - 🖱️ Tampermonkey/Greasemonkey
   - ✋ Inscription manuelle assistée

## 🏆 Avantages de la nouvelle structure

- ✅ Configuration centralisée
- ✅ Séparation claire des responsabilités  
- ✅ Réutilisabilité du code
- ✅ Logs organisés
- ✅ Données versionnées
- ✅ CLI convivial
- ✅ Workflow automatisé complet