#!/usr/bin/env python3
"""
Players Manager pour le projet UMB Carom Scraper
Gestion des profils de joueurs multiples
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from .config_manager import config_manager

class PlayersManager:
    def __init__(self):
        self.config_manager = config_manager
        self.players_dir = self.config_manager.config_dir / "players"
        self.players_dir.mkdir(exist_ok=True)
    
    def list_players(self) -> List[str]:
        """Liste tous les joueurs disponibles"""
        players = []
        for player_file in self.players_dir.glob("*.json"):
            if player_file.name != "template.json":
                players.append(player_file.stem)
        return sorted(players)
    
    def get_player_info(self, player_name: str) -> Dict[str, Any]:
        """Récupère les informations d'un joueur"""
        player_file = self.players_dir / f"{player_name}.json"
        
        if not player_file.exists():
            raise FileNotFoundError(f"Joueur '{player_name}' non trouvé")
        
        with open(player_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('player_data', {})
    
    def validate_player(self, player_name: str) -> List[str]:
        """Valide la configuration d'un joueur et retourne les erreurs"""
        try:
            player_data = self.get_player_info(player_name)
        except FileNotFoundError as e:
            return [str(e)]
        
        errors = []
        
        # Champs obligatoires
        required_fields = ['lastName', 'firstName', 'email', 'federation', 'nationality', 'country']
        for field in required_fields:
            if not player_data.get(field):
                errors.append(f"Champ obligatoire manquant: {field}")
        
        # Validation email basique
        email = player_data.get('email', '')
        if email and '@' not in email:
            errors.append("Format email invalide")
        
        # Validation date de naissance
        dob = player_data.get('dateOfBirth', '')
        if dob:
            import re
            if not re.match(r'\d{2}/\d{2}/\d{4}', dob):
                errors.append("Format date de naissance invalide (attendu: DD/MM/YYYY)")
        
        return errors
    
    def create_player(self, player_name: str, from_template: bool = True, from_player: str = None) -> str:
        """Crée un nouveau profil joueur"""
        player_file = self.players_dir / f"{player_name}.json"
        
        if player_file.exists():
            raise ValueError(f"Le joueur '{player_name}' existe déjà")
        
        if from_player:
            # Copier depuis un autre joueur
            source_file = self.players_dir / f"{from_player}.json"
            if not source_file.exists():
                raise FileNotFoundError(f"Joueur source '{from_player}' non trouvé")
            shutil.copy2(source_file, player_file)
        else:
            # Copier depuis le template
            template_file = self.players_dir / "template.json"
            if not template_file.exists():
                raise FileNotFoundError("Fichier template.json manquant")
            shutil.copy2(template_file, player_file)
        
        return str(player_file)
    
    def get_player_file_path(self, player_name: str) -> Path:
        """Retourne le chemin vers le fichier d'un joueur"""
        return self.players_dir / f"{player_name}.json"
    
    def validate_all_players(self, player_names: List[str]) -> Dict[str, List[str]]:
        """Valide plusieurs joueurs à la fois"""
        validation_results = {}
        
        for player_name in player_names:
            validation_results[player_name] = self.validate_player(player_name)
        
        return validation_results
    
    def get_players_summary(self) -> List[Dict[str, str]]:
        """Récupère un résumé de tous les joueurs"""
        players_summary = []
        
        for player_name in self.list_players():
            try:
                player_data = self.get_player_info(player_name)
                errors = self.validate_player(player_name)
                
                summary = {
                    'name': player_name,
                    'full_name': f"{player_data.get('firstName', '')} {player_data.get('lastName', '')}".strip(),
                    'email': player_data.get('email', ''),
                    'federation': player_data.get('federation', ''),
                    'valid': len(errors) == 0,
                    'errors_count': len(errors)
                }
                players_summary.append(summary)
            except Exception:
                players_summary.append({
                    'name': player_name,
                    'full_name': 'Erreur lecture',
                    'email': '',
                    'federation': '',
                    'valid': False,
                    'errors_count': 999
                })
        
        return players_summary
    
    def create_multi_tournament_config(self, tournament_id: int, registration_date: str, 
                                     player_names: List[str], bot_type: str = "curl") -> str:
        """Crée une configuration de tournoi multi-joueurs"""
        
        # Valider tous les joueurs
        validation_results = self.validate_all_players(player_names)
        invalid_players = [name for name, errors in validation_results.items() if errors]
        
        if invalid_players:
            error_details = []
            for player in invalid_players:
                errors = validation_results[player]
                error_details.append(f"{player}: {', '.join(errors)}")
            raise ValueError(f"Joueurs invalides: {'; '.join(error_details)}")
        
        # Configuration multi-joueurs
        players_config = []
        for player_name in player_names:
            player_config = {
                "name": player_name,
                "config_file": str(self.get_player_file_path(player_name)),
                "bot_type": bot_type
            }
            players_config.append(player_config)
        
        multi_config = {
            "tournament_id": tournament_id,
            "registration_date": registration_date,
            "registration_time": "12:00:00",
            "mode": "multi",
            "players": players_config,
            "launch_settings": {
                "delay_between_bots_ms": 50,
                "max_sync_wait_seconds": 30
            }
        }
        
        # Créer le dossier tournaments s'il n'existe pas
        tournaments_dir = self.config_manager.config_dir / "tournaments"
        tournaments_dir.mkdir(exist_ok=True)
        
        # Sauvegarder dans le dossier tournaments
        config_file = tournaments_dir / f"tournament_{tournament_id}_multi.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(multi_config, f, indent=2, ensure_ascii=False)
        
        return str(config_file)

    def create_multi_tournament_config_with_types(self, tournament_id: int, registration_date: str, 
                                                 players_config: List[Tuple[str, str]]) -> str:
        """Crée une configuration de tournoi multi-joueurs avec types de bot par joueur"""
        
        # Valider tous les joueurs
        player_names = [p[0] for p in players_config]
        validation_results = self.validate_all_players(player_names)
        invalid_players = [name for name, errors in validation_results.items() if errors]
        
        if invalid_players:
            error_details = []
            for player in invalid_players:
                errors = validation_results[player]
                error_details.append(f"{player}: {', '.join(errors)}")
            raise ValueError(f"Joueurs invalides: {'; '.join(error_details)}")
        
        # Configuration multi-joueurs avec types spécifiques
        players_config_list = []
        for player_name, bot_type in players_config:
            player_config = {
                "name": player_name,
                "config_file": str(self.get_player_file_path(player_name)),
                "bot_type": bot_type
            }
            players_config_list.append(player_config)
        
        multi_config = {
            "tournament_id": tournament_id,
            "registration_date": registration_date,
            "registration_time": "12:00:00",
            "mode": "multi",
            "players": players_config_list,
            "launch_settings": {
                "delay_between_bots_ms": 50,
                "max_sync_wait_seconds": 30
            }
        }
        
        # Créer le dossier tournaments s'il n'existe pas
        tournaments_dir = self.config_manager.config_dir / "tournaments"
        tournaments_dir.mkdir(exist_ok=True)
        
        # Sauvegarder dans le dossier tournaments
        config_file = tournaments_dir / f"tournament_{tournament_id}_multi.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(multi_config, f, indent=2, ensure_ascii=False)
        
        return str(config_file)

# Instance globale
players_manager = PlayersManager()