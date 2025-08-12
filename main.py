#!/usr/bin/env python3
"""
Script principal pour le projet UMB Carom Scraper
Orchestration complète : Scraping → Identification World Cups → Bot d'inscription
"""

import sys
import argparse
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.carom_scraper.scraper import main as scraper_main
from src.carom_scraper.config_manager import config_manager

def show_world_cups():
    """Affiche les World Cups futures détectées"""
    print("🏆 WORLD CUPS 3-CUSHION FUTURES")
    print("=" * 60)
    
    world_cups = config_manager.get_world_cup_tournaments()
    
    if not world_cups:
        print("⚠️ Aucune World Cup future trouvée")
        print("💡 Lancez d'abord le scraping avec: python main.py scrape")
        return
    
    for tournament in world_cups:
        print(f"ID {tournament['id']:3d}: {tournament['tournament']}")
        print(f"      📅 {tournament['starts_on']}")
        print(f"      📍 {tournament['place']}")
        
        if tournament.get('registration_start'):
            print(f"      📝 Inscriptions: {tournament['registration_start']}")
        
        print(f"      🔗 {tournament['url']}")
        print()
    
    print(f"📊 Total: {len(world_cups)} World Cups futures")

def setup_bot_config(tournament_id: int):
    """Configure un bot pour un tournoi spécifique"""
    print(f"⚙️ CONFIGURATION BOT POUR TOURNOI {tournament_id}")
    print("=" * 50)
    
    # Récupérer les infos du tournoi
    tournaments_data = config_manager.get_tournaments_data()
    tournament = None
    
    for t in tournaments_data.get('tournaments', []):
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        print(f"❌ Tournoi ID {tournament_id} non trouvé")
        print("💡 Lancez d'abord: python main.py world-cups")
        return
    
    print(f"🎯 Tournoi: {tournament['tournament']}")
    print(f"📅 Date: {tournament['starts_on']}")
    print(f"📍 Lieu: {tournament['place']}")
    
    if tournament.get('registration_start'):
        registration_date = tournament['registration_start'].split(' à ')[0]
        print(f"📝 Inscription: {tournament['registration_start']}")
        
        # Sauvegarder la config
        config_file = config_manager.save_tournament_config(tournament_id, registration_date)
        print(f"✅ Configuration sauvée: {config_file}")
        
        print("\n🤖 Pour lancer le bot:")
        print(f"   python -m src.bots.curl_bot --config {config_file}")
        print(f"   python -m src.bots.selenium_bot --config {config_file}")
    else:
        print("⚠️ Date d'inscription non calculée (pas une World Cup 3-Cushion?)")

def main():
    """Fonction principale avec CLI"""
    parser = argparse.ArgumentParser(
        description="UMB Carom Scraper - Automatisation complète d'inscription aux World Cups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'usage:
  python main.py scrape              # Lance le scraping des tournois
  python main.py world-cups          # Affiche les World Cups futures
  python main.py setup-bot 362       # Configure le bot pour le tournoi 362
  python main.py config              # Affiche les chemins de configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Commande scrape
    scrape_parser = subparsers.add_parser('scrape', help='Lance le scraping des tournois')
    
    # Commande world-cups
    worldcups_parser = subparsers.add_parser('world-cups', help='Affiche les World Cups futures')
    
    # Commande setup-bot
    setup_parser = subparsers.add_parser('setup-bot', help='Configure un bot pour un tournoi')
    setup_parser.add_argument('tournament_id', type=int, help='ID du tournoi')
    
    # Commande config
    config_parser = subparsers.add_parser('config', help='Affiche les informations de configuration')
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        print("🎱 LANCEMENT DU SCRAPING")
        scraper_main()
        
    elif args.command == 'world-cups':
        show_world_cups()
        
    elif args.command == 'setup-bot':
        setup_bot_config(args.tournament_id)
        
    elif args.command == 'config':
        print("📁 CONFIGURATION DU PROJET")
        print("=" * 40)
        print(f"Racine projet: {config_manager.project_root}")
        print(f"Dossier config: {config_manager.config_dir}")
        print(f"Dossier data: {config_manager.data_dir}")
        print(f"Dossier logs: {config_manager.logs_dir}")
        print()
        
        # Vérifier la config joueur
        try:
            player_data = config_manager.load_player_data()
            print("✅ Configuration joueur: OK")
            print(f"   Joueur: {player_data.get('firstName', '')} {player_data.get('lastName', '')}")
            print(f"   Email: {player_data.get('email', '')}")
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ Configuration joueur: {e}")
            print("💡 Éditez config/player.json avec vos données")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()