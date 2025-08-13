#!/usr/bin/env python3
"""
Classe de base pour les bots d'inscription UMB
Centralise la configuration et les fonctionnalités communes
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Ajouter le dossier parent au PYTHONPATH pour l'import
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.config_manager import config_manager

class BaseBotConfig:
    """Gestionnaire de configuration pour les bots"""
    
    def __init__(self, tournament_config_file: str = None, player_config_file: str = None):
        self.config_manager = config_manager
        
        # Charger config bot générale
        self.bot_config = self.config_manager.load_bot_config()
        
        # Charger données joueur (depuis fichier spécifique ou défaut)
        if player_config_file:
            self.player_data = self.load_player_from_file(player_config_file)
        else:
            self.player_data = self.config_manager.load_player_data()
        
        # Charger config tournoi spécifique si fournie
        self.tournament_config = None
        if tournament_config_file:
            self.load_tournament_config(tournament_config_file)
    
    def load_player_from_file(self, player_file: str) -> Dict[str, Any]:
        """Charge les données joueur depuis un fichier spécifique"""
        player_path = Path(player_file)
        if not player_path.is_absolute():
            player_path = self.config_manager.project_root / player_file
        
        if not player_path.exists():
            raise FileNotFoundError(f"Fichier joueur non trouvé: {player_path}")
        
        with open(player_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        player_data = config.get('player_data', {})
        
        # Vérifier que les champs obligatoires sont remplis
        required_fields = ['lastName', 'firstName', 'email']
        missing_fields = [field for field in required_fields if not player_data.get(field)]
        
        if missing_fields:
            raise ValueError(
                f"Champs obligatoires manquants dans {player_path}: {missing_fields}"
            )
        
        return player_data
    
    def load_tournament_config(self, config_file: str):
        """Charge la configuration d'un tournoi spécifique"""
        config_path = Path(config_file)
        if not config_path.is_absolute():
            config_path = self.config_manager.config_dir / config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration tournoi non trouvée: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.tournament_config = json.load(f)
    
    def get_tournament_id(self) -> int:
        """Retourne l'ID du tournoi configuré"""
        if self.tournament_config:
            return self.tournament_config['tournament_id']
        
        # Fallback: demander à l'utilisateur
        try:
            return int(input("ID du tournoi: "))
        except ValueError:
            raise ValueError("ID de tournoi invalide")
    
    def get_registration_datetime(self) -> datetime:
        """Retourne la date/heure d'inscription"""
        if self.tournament_config:
            date_str = self.tournament_config['registration_date']
            time_str = self.tournament_config.get('registration_time', '12:00:00')
            return datetime.strptime(f"{date_str} {time_str}", "%d-%B-%Y %H:%M:%S")
        
        # Fallback: demander à l'utilisateur
        date_input = input("Date d'inscription (DD-Month-YYYY): ")
        time_input = input("Heure d'inscription (HH:MM:SS) [12:00:00]: ") or "12:00:00"
        return datetime.strptime(f"{date_input} {time_input}", "%d-%B-%Y %H:%M:%S")
    
    def get_check_start_datetime(self) -> datetime:
        """Retourne la date/heure de début de surveillance"""
        registration_dt = self.get_registration_datetime()
        offset_seconds = self.bot_config['bot'].get('check_start_offset_seconds', 5)
        return registration_dt - timedelta(seconds=offset_seconds)
    
    def get_registration_url(self) -> str:
        """Retourne l'URL d'inscription"""
        tournament_id = self.get_tournament_id()
        return f"https://files.umb-carom.org/public/PlayerModify.aspx?tourID={tournament_id}"
    
    def get_player_data_for_curl(self) -> dict:
        """Retourne les données joueur formatées pour cURL"""
        return {
            'ddlFedration': self.player_data.get('federation', ''),
            'txtLName': self.player_data.get('lastName', ''),
            'txtFName': self.player_data.get('firstName', ''),
            'txtRankID': self.player_data.get('playerId', ''),
            'ddlNationality': self.player_data.get('nationality', ''),
            'txtDOB': self.player_data.get('dateOfBirth', ''),
            'ddlCountry': self.player_data.get('country', ''),
            'txtCity': self.player_data.get('city', ''),
            'txtAddress': self.player_data.get('address', ''),
            'txtPhone': self.player_data.get('phone', ''),
            'txtEmail': self.player_data.get('email', ''),
            'txtFax': self.player_data.get('contactFax', '')
        }
    
    def get_player_data_for_selenium(self) -> dict:
        """Retourne les données joueur formatées pour Selenium"""
        return self.player_data
    
    def get_bot_settings(self) -> dict:
        """Retourne les paramètres de performance du bot"""
        return self.bot_config['bot']
    
    def get_log_path(self, bot_name: str) -> Path:
        """Retourne le chemin de log pour un bot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{bot_name}_{timestamp}.log"
        return self.config_manager.get_log_path(log_filename)
    
    def validate_config(self) -> list:
        """Valide la configuration et retourne les erreurs éventuelles"""
        errors = []
        
        # Vérifier données joueur essentielles
        required_fields = ['lastName', 'firstName', 'email']
        for field in required_fields:
            if not self.player_data.get(field):
                errors.append(f"Champ joueur requis manquant: {field}")
        
        # Vérifier configuration tournoi si chargée
        if self.tournament_config:
            if not self.tournament_config.get('tournament_id'):
                errors.append("ID de tournoi manquant dans la configuration")
            if not self.tournament_config.get('registration_date'):
                errors.append("Date d'inscription manquante dans la configuration")
        
        return errors