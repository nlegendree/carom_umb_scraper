#!/usr/bin/env python3
"""
Configuration Manager pour le projet UMB Carom Scraper
Centralise la gestion des configurations et des données joueur
"""

import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self, project_root: str = None):
        if project_root is None:
            # Détecter automatiquement la racine du projet
            current_file = Path(__file__).resolve()
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        
        # Créer les dossiers si nécessaire
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def load_player_data(self) -> Dict[str, Any]:
        """Charge les données du joueur depuis player.json"""
        player_file = self.config_dir / "player.json"
        
        if not player_file.exists():
            raise FileNotFoundError(
                f"Fichier de configuration joueur non trouvé: {player_file}\n"
                "Veuillez créer config/player.json avec vos données"
            )
        
        with open(player_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        player_data = config.get('player_data', {})
        
        # Vérifier que les champs obligatoires sont remplis
        required_fields = ['lastName', 'firstName', 'email']
        missing_fields = [field for field in required_fields if not player_data.get(field)]
        
        if missing_fields:
            raise ValueError(
                f"Champs obligatoires manquants dans player.json: {missing_fields}"
            )
        
        return player_data
    
    def load_bot_config(self) -> Dict[str, Any]:
        """Charge la configuration des bots"""
        config_file = self.config_dir / "bot_config.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration bot non trouvée: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_data_path(self, filename: str) -> Path:
        """Retourne le chemin complet vers un fichier de données"""
        return self.data_dir / filename
    
    def get_log_path(self, filename: str) -> Path:
        """Retourne le chemin complet vers un fichier de log"""
        return self.logs_dir / f"{filename}.log"
    
    def get_tournaments_data(self) -> Dict[str, Any]:
        """Charge les données des tournois depuis umb_tournaments.json"""
        tournaments_file = self.get_data_path("umb_tournaments.json")
        
        if not tournaments_file.exists():
            return {"metadata": {}, "tournaments": []}
        
        with open(tournaments_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_world_cup_tournaments(self) -> list:
        """Retourne uniquement les tournois World Cup 3-Cushion futurs"""
        from datetime import datetime
        
        data = self.get_tournaments_data()
        tournaments = data.get('tournaments', [])
        current_date = datetime.now()
        
        world_cups = []
        for tournament in tournaments:
            if tournament.get('tournament') == 'World Cup 3-Cushion':
                # Vérifier si c'est un tournoi futur
                starts_on = tournament.get('starts_on', '')
                if starts_on:
                    try:
                        # Parser la date (format: DD-Month-YYYY)
                        start_date = datetime.strptime(starts_on, "%d-%B-%Y")
                        if start_date > current_date:
                            world_cups.append(tournament)
                    except ValueError:
                        continue
        
        return world_cups
    
    def save_tournament_config(self, tournament_id: int, registration_date: str) -> str:
        """Sauvegarde une configuration de tournoi pour le bot"""
        # Créer le dossier tournaments s'il n'existe pas
        tournaments_dir = self.config_dir / "tournaments"
        tournaments_dir.mkdir(exist_ok=True)
        
        config_data = {
            "tournament_id": tournament_id,
            "registration_date": registration_date,
            "registration_time": "12:00:00",
            "check_start_offset": 5
        }
        
        config_file = tournaments_dir / f"tournament_{tournament_id}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        return str(config_file)

# Instance globale pour faciliter l'import
config_manager = ConfigManager()