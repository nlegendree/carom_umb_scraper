#!/usr/bin/env python3
"""
Multi-Launcher pour inscription simultanée de plusieurs joueurs
Orchestration de plusieurs instances de bots (cURL/Selenium)
"""

import sys
import json
import time
import argparse
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.config_manager import config_manager

class MultiPlayerLauncher:
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config = self.load_multi_config()
        self.processes = []
        self.results = {}
        self.logger = self.setup_logging()
        
        # Validation de la configuration
        self.validate_config()
        
        # Paramètres
        self.tournament_id = self.config['tournament_id']
        self.registration_datetime = self.parse_registration_datetime()
        self.players = self.config['players']
        self.launch_settings = self.config.get('launch_settings', {})
        
    def load_multi_config(self) -> Dict[str, Any]:
        """Charge la configuration multi-joueurs"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Fichier de configuration non trouvé: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_config(self):
        """Valide la configuration multi-joueurs"""
        required_fields = ['tournament_id', 'registration_date', 'players']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Champ obligatoire manquant: {field}")
        
        if not self.config['players']:
            raise ValueError("Aucun joueur configuré")
        
        # Vérifier que tous les fichiers joueurs existent
        for player in self.config['players']:
            player_file = Path(player['config_file'])
            if not player_file.exists():
                raise FileNotFoundError(f"Fichier joueur non trouvé: {player_file}")
    
    def parse_registration_datetime(self) -> datetime:
        """Parse la date/heure d'inscription"""
        date_str = self.config['registration_date']
        time_str = self.config.get('registration_time', '12:00:00')
        return datetime.strptime(f"{date_str} {time_str}", "%d-%B-%Y %H:%M:%S")
    
    def setup_logging(self) -> logging.Logger:
        """Configure le logging pour multi-launcher"""
        log_path = config_manager.get_log_path('multi_launcher')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def get_bot_command(self, player_config: Dict[str, Any], delay_ms: int = 0) -> List[str]:
        """Génère la commande pour lancer un bot"""
        bot_type = player_config.get('bot_type', 'curl')
        
        if bot_type == 'curl':
            cmd = [sys.executable, '-m', 'src.bots.curl_bot']
        elif bot_type == 'selenium':
            cmd = [sys.executable, '-m', 'src.bots.selenium_bot']
        else:
            raise ValueError(f"Type de bot non supporté: {bot_type}")
        
        # Créer config tournoi temporaire pour ce joueur
        tournament_config = self.create_tournament_config_for_player(player_config)
        
        cmd.extend(['--config', tournament_config])
        cmd.extend(['--player', player_config['config_file']])
        
        if delay_ms > 0:
            cmd.extend(['--delay', str(delay_ms)])
        
        return cmd
    
    def create_tournament_config_for_player(self, player_config: Dict[str, Any]) -> str:
        """Crée une config tournoi temporaire pour un joueur"""
        temp_config = {
            'tournament_id': self.tournament_id,
            'registration_date': self.config['registration_date'],
            'registration_time': self.config.get('registration_time', '12:00:00'),
            'check_start_offset': 5
        }
        
        # Fichier temporaire
        temp_file = config_manager.config_dir / f"temp_tournament_{self.tournament_id}_{player_config['name']}.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(temp_config, f, indent=2, ensure_ascii=False)
        
        return str(temp_file)
    
    def calculate_wait_time(self) -> float:
        """Calcule le temps d'attente avant démarrage"""
        now = datetime.now()
        check_start_offset = self.launch_settings.get('max_sync_wait_seconds', 30)
        start_time = self.registration_datetime - timedelta(seconds=check_start_offset)
        
        wait_seconds = (start_time - now).total_seconds()
        return max(0, wait_seconds)
    
    def launch_all_bots(self):
        """Lance tous les bots de manière coordonnée"""
        self.logger.info("🚀 MULTI-LAUNCHER DÉMARRAGE")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 Tournoi: {self.tournament_id}")
        self.logger.info(f"📅 Inscription: {self.registration_datetime.strftime('%d-%B-%Y à %H:%M:%S')}")
        self.logger.info(f"👥 Joueurs: {len(self.players)}")
        self.logger.info("=" * 60)
        
        # Afficher tous les joueurs
        for i, player in enumerate(self.players):
            player_name = player['name']
            bot_type = player.get('bot_type', 'curl')
            self.logger.info(f"👤 {i+1}. {player_name} ({bot_type})")
        
        self.logger.info("=" * 60)
        
        # Calculer attente
        wait_time = self.calculate_wait_time()
        if wait_time > 0:
            self.logger.info(f"⏳ Attente {wait_time:.1f}s avant synchronisation...")
            time.sleep(wait_time)
        
        # Phase de lancement échelonné
        self.logger.info("🔄 LANCEMENT COORDONNÉ")
        delay_between_bots = self.launch_settings.get('delay_between_bots_ms', 50)
        
        for i, player in enumerate(self.players):
            delay_ms = i * delay_between_bots
            cmd = self.get_bot_command(player, delay_ms)
            
            self.logger.info(f"⚡ Lancement {player['name']} ({player.get('bot_type', 'curl')}) avec délai {delay_ms}ms")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append({
                'process': process,
                'player': player,
                'start_time': time.time() + (delay_ms / 1000)
            })
            
            # Petit délai pour éviter la surcharge
            time.sleep(0.05)
        
        # Monitoring temps réel
        self.monitor_all_bots()
    
    def monitor_all_bots(self):
        """Surveille tous les bots en temps réel"""
        self.logger.info("📊 MONITORING EN TEMPS RÉEL")
        self.logger.info("-" * 60)
        
        running_count = len(self.processes)
        
        while running_count > 0:
            running_count = 0
            
            for i, bot_info in enumerate(self.processes):
                process = bot_info['process']
                player_name = bot_info['player']['name']
                
                if process.poll() is None:
                    running_count += 1
                    elapsed = time.time() - bot_info['start_time']
                    self.logger.info(f"👤 {player_name}: ⏳ En cours ({elapsed:.1f}s)")
                else:
                    # Processus terminé
                    if player_name not in self.results:
                        return_code = process.returncode
                        elapsed = time.time() - bot_info['start_time']
                        
                        if return_code == 0:
                            self.results[player_name] = {'status': 'success', 'time': elapsed}
                            self.logger.info(f"✅ {player_name}: SUCCESS en {elapsed:.1f}s")
                        else:
                            self.results[player_name] = {'status': 'error', 'time': elapsed, 'code': return_code}
                            self.logger.info(f"❌ {player_name}: ERREUR (code {return_code}) en {elapsed:.1f}s")
            
            if running_count > 0:
                time.sleep(0.5)
        
        self.show_final_results()
    
    def show_final_results(self):
        """Affiche les résultats finaux"""
        self.logger.info("\\n" + "=" * 60)
        self.logger.info("🎉 RÉSULTATS FINAUX")
        self.logger.info("=" * 60)
        
        success_count = 0
        total_time = 0
        fastest_time = float('inf')
        
        for player_name, result in self.results.items():
            status = result['status']
            time_taken = result['time']
            
            if status == 'success':
                success_count += 1
                total_time += time_taken
                fastest_time = min(fastest_time, time_taken)
                self.logger.info(f"✅ {player_name}: Success en {time_taken:.1f}s")
            else:
                self.logger.info(f"❌ {player_name}: Échec en {time_taken:.1f}s")
        
        total_players = len(self.results)
        success_rate = (success_count / total_players * 100) if total_players > 0 else 0
        
        self.logger.info("-" * 60)
        self.logger.info(f"📊 Succès: {success_count}/{total_players} ({success_rate:.1f}%)")
        
        if success_count > 0:
            avg_time = total_time / success_count
            self.logger.info(f"⚡ Temps le plus rapide: {fastest_time:.1f}s")
            self.logger.info(f"📊 Temps moyen: {avg_time:.1f}s")
        
        if success_count == total_players:
            self.logger.info("🏆 MISSION PARFAITE: Tous les joueurs inscrits!")
        elif success_count > 0:
            self.logger.info("🎯 MISSION PARTIELLE: Certains joueurs inscrits")
        else:
            self.logger.info("💥 MISSION ÉCHOUÉE: Aucun joueur inscrit")
    
    def cleanup(self):
        """Nettoyage des ressources"""
        # Arrêter tous les processus encore en cours
        for bot_info in self.processes:
            process = bot_info['process']
            if process.poll() is None:
                process.terminate()
                
        # Supprimer les fichiers de config temporaires
        temp_files = config_manager.config_dir.glob(f"temp_tournament_{self.tournament_id}_*.json")
        for temp_file in temp_files:
            try:
                temp_file.unlink()
            except Exception:
                pass
    
    def run(self):
        """Lance le processus complet"""
        try:
            self.launch_all_bots()
        except KeyboardInterrupt:
            self.logger.info("\\n👋 Arrêt utilisateur - Nettoyage en cours...")
            self.cleanup()
        except Exception as e:
            self.logger.error(f"❌ Erreur critique: {e}")
        finally:
            self.cleanup()

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Multi-Launcher UMB - Inscription multiple simultanée")
    parser.add_argument('--config', required=True, help='Fichier de configuration multi-joueurs')
    parser.add_argument('--monitor', action='store_true', help='Mode monitoring seulement')
    
    args = parser.parse_args()
    
    try:
        launcher = MultiPlayerLauncher(args.config)
        launcher.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()