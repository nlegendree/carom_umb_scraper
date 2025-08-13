#!/usr/bin/env python3
"""
Script principal pour le projet UMB Carom Scraper
Orchestration complète : Scraping → Identification World Cups → Bot d'inscription
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Ajouter le dossier src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.scraper.scraper import main as scraper_main
from src.scraper.config_manager import config_manager
from src.scraper.players_manager import players_manager

def show_world_cups():
    """Affiche les World Cups futures détectées"""
    print("🏆 WORLD CUPS 3-CUSHION FUTURES")
    print("=" * 60)
    
    world_cups = config_manager.get_world_cup_tournaments()
    
    if not world_cups:
        print("⚠️ Aucune World Cup future trouvée")
        print("💡 Lancez d'abord le scraping avec: python main.py scrape")
        return
    
    # Trier les World Cups par date starts_on
    from datetime import datetime
    
    def parse_date_for_sorting(date_str):
        """Parse une date pour le tri"""
        try:
            return datetime.strptime(date_str, "%d-%B-%Y")
        except ValueError:
            # En cas d'échec, retourner une date très future pour mettre à la fin
            return datetime(2099, 12, 31)
    
    world_cups_sorted = sorted(world_cups, key=lambda x: parse_date_for_sorting(x.get('starts_on', '')))
    
    for tournament in world_cups_sorted:
        print(f"ID {tournament['id']:3d}: {tournament['tournament']}")
        print(f"      📅 {tournament['starts_on']}")
        print(f"      📍 {tournament['place']}")
        
        if tournament.get('registration_start'):
            print(f"      📝 Inscriptions: {tournament['registration_start']}")
        
        print(f"      🔗 {tournament['url']}")
        print()
    
    print(f"📊 Total: {len(world_cups_sorted)} World Cups futures")

def setup_bot_unified(tournament_id: int, player: str = None, players: List[str] = None, bot_type: str = "curl"):
    """Configure un bot pour un tournoi (simple ou multi-joueurs)"""
    
    # Validation des paramètres
    if player and players:
        print("❌ Erreur: Utilisez soit --player soit --players, pas les deux")
        return
    
    if not player and not players:
        print("❌ Erreur: Spécifiez au moins --player ou --players")
        print("💡 Exemples:")
        print("   python main.py setup-bot 362 --player john")
        print("   python main.py setup-bot 362 --players john,marie")
        print("   python main.py setup-bot 362 --players john:curl,marie:selenium")
        return
    
    # Déterminer le mode et parser les joueurs
    is_multi = bool(players)
    
    if is_multi:
        # Parser les joueurs avec types de bot optionnels
        players_config = []
        has_custom_types = False
        
        for player_spec in players:
            if ':' in player_spec:
                # Format "joueur:type_bot"
                player_name, player_bot_type = player_spec.split(':', 1)
                if player_bot_type not in ['curl', 'selenium']:
                    print(f"❌ Erreur: Type de bot invalide '{player_bot_type}' pour {player_name}")
                    print("💡 Types supportés: curl, selenium")
                    return
                players_config.append((player_name.strip(), player_bot_type))
                has_custom_types = True
            else:
                # Format simple "joueur"
                players_config.append((player_spec.strip(), bot_type))
        
        players_list = [p[0] for p in players_config]
        
        # Affichage adapté selon le format
        if has_custom_types:
            bot_display = "Mix: " + ", ".join([f"{p[0]}({p[1]})" for p in players_config])
        else:
            bot_display = bot_type
    else:
        players_list = [player]
        players_config = [(player, bot_type)]
        bot_display = bot_type
    
    print(f"⚙️ CONFIGURATION BOT TOURNOI {tournament_id}")
    print("=" * 60)
    print(f"👥 Joueur(s): {', '.join(players_list)}")
    print(f"🤖 Type de bot: {bot_display}")
    print(f"📋 Mode: {'Multi-joueurs' if is_multi else 'Simple'}")
    print()
    
    # Récupérer les infos du tournoi
    tournaments_data = config_manager.get_tournaments_data()
    tournament = None
    
    for t in tournaments_data.get('tournaments', []):
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        print(f"❌ Tournoi ID {tournament_id} non trouvé")
        print("💡 Lancez d'abord: python main.py scrape")
        return
    
    print(f"🎯 Tournoi: {tournament['tournament']}")
    print(f"📅 Date: {tournament['starts_on']}")
    print(f"📍 Lieu: {tournament['place']}")
    
    if not tournament.get('registration_start'):
        print("⚠️ Date d'inscription non calculée (pas une World Cup 3-Cushion?)")
        return
    
    registration_date = tournament['registration_start'].split(' à ')[0]
    print(f"📝 Inscription: {tournament['registration_start']}")
    
    try:
        if is_multi:
            # Configuration multi-joueurs avec support mix de bots
            config_file = players_manager.create_multi_tournament_config_with_types(
                tournament_id, registration_date, players_config
            )
            print(f"✅ Configuration multi-joueurs sauvée: {config_file}")
            print("\n🚀 Pour lancer l'inscription multi-joueurs:")
            print(f"   python -m src.bots.multi_launcher --config {config_file}")
        else:
            # Configuration simple
            config_file = config_manager.save_tournament_config(tournament_id, registration_date)
            print(f"✅ Configuration sauvée: {config_file}")
            print(f"\n🤖 Pour lancer le bot avec {player}:")
            print(f"   python -m src.bots.curl_bot --config {config_file} --player config/players/{player}.json")
            print(f"   python -m src.bots.selenium_bot --config {config_file} --player config/players/{player}.json")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def list_players():
    """Liste tous les joueurs disponibles avec toutes les infos obligatoires"""
    print("👥 JOUEURS DISPONIBLES")
    print("=" * 80)
    
    players_summary = players_manager.get_players_summary()
    
    if not players_summary:
        print("⚠️ Aucun joueur configuré")
        print("💡 Créez un joueur avec: python main.py create-player <nom>")
        return
    
    for player in players_summary:
        status = "✅" if player['valid'] else "❌"
        print(f"{status} {player['name'].upper()}")
        print("-" * 40)
        
        try:
            # Récupérer toutes les données du joueur
            player_data = players_manager.get_player_info(player['name'])
            
            # Champs obligatoires à afficher
            essential_fields = [
                ('federation', '🏛️ Fédération'),
                ('lastName', '👤 Nom'),
                ('firstName', '👤 Prénom'),  
                ('playerId', '🆔 ID Joueur'),
                ('nationality', '🌍 Nationalité'),
                ('dateOfBirth', '📅 Date naissance'),
                ('country', '🇫🇷 Pays'),
                ('email', '📧 Email')
            ]
            
            for field_key, field_label in essential_fields:
                value = player_data.get(field_key, '')
                field_status = "✅" if value else "❌"
                print(f"   {field_status} {field_label:18}: {value}")
            
            # Champs optionnels (si remplis)
            optional_fields = [
                ('city', '🏙️  Ville'),
                ('address', '🏠 Adresse'),
                ('phone', '📞 Téléphone'),
                ('contactFax', '📠 Fax')
            ]
            
            optional_filled = []
            for field_key, field_label in optional_fields:
                value = player_data.get(field_key, '')
                if value:
                    optional_filled.append(f"{field_label}: {value}")
            
            if optional_filled:
                print("   📋 Infos optionnelles:")
                for info in optional_filled:
                    print(f"      • {info}")
            
        except Exception as e:
            print(f"   ❌ Erreur lecture données: {e}")
        
        if not player['valid']:
            print(f"   ⚠️  {player['errors_count']} erreur(s) - Utilisez 'validate-player {player['name']}'")
        
        print()

def create_player(player_name: str, from_player: str = None):
    """Crée un nouveau profil joueur"""
    print(f"👤 CRÉATION JOUEUR: {player_name}")
    print("=" * 40)
    
    try:
        if from_player:
            player_file = players_manager.create_player(player_name, from_template=False, from_player=from_player)
            print(f"✅ Joueur créé depuis {from_player}: {player_file}")
        else:
            player_file = players_manager.create_player(player_name, from_template=True)
            print(f"✅ Joueur créé depuis template: {player_file}")
        
        print("💡 Éditez le fichier pour compléter les données:")
        print(f"   nano {player_file}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def validate_player(player_name: str):
    """Valide la configuration d'un joueur"""
    errors = players_manager.validate_player(player_name)
    
    if not errors:
        print(f"✅ Configuration valide pour {player_name}")
    else:
        print(f"❌ Configuration invalide pour {player_name}")
        for error in errors:
            print(f"   • {error}")


def main():
    """Fonction principale avec CLI"""
    parser = argparse.ArgumentParser(
        description="UMB Carom Scraper - Automatisation complète d'inscription aux World Cups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'usage:
  python main.py scrape                          # Lance le scraping des tournois
  python main.py world-cups                      # Affiche les World Cups futures
  python main.py setup-bot 362 --player john     # Configure le bot pour john
  python main.py setup-bot 362 --players john,marie  # Multi-joueurs (tous cURL)
  python main.py setup-bot 362 --players john:curl,marie:selenium  # Mix cURL/Selenium
  python main.py list-players                    # Liste tous les joueurs
  python main.py create-player john              # Crée un nouveau joueur
  python main.py validate-player john            # Valide la config de john
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
    setup_parser.add_argument('--player', help='Joueur unique pour configuration simple')
    setup_parser.add_argument('--players', help='Liste des joueurs séparés par virgules pour configuration multi')
    setup_parser.add_argument('--bot-type', choices=['curl', 'selenium'], default='curl', help='Type de bot à utiliser')
    
    # Commande config
    config_parser = subparsers.add_parser('config', help='Affiche les informations de configuration')
    
    # === NOUVELLES COMMANDES MULTI-JOUEURS ===
    
    # Liste des joueurs
    list_parser = subparsers.add_parser('list-players', help='Liste tous les joueurs disponibles')
    
    # Création de joueur
    create_parser = subparsers.add_parser('create-player', help='Crée un nouveau profil joueur')
    create_parser.add_argument('player_name', help='Nom du joueur à créer')
    create_parser.add_argument('--from-player', help='Copier depuis un autre joueur existant')
    
    # Validation joueur
    validate_parser = subparsers.add_parser('validate-player', help='Valide la configuration d\'un joueur')
    validate_parser.add_argument('player_name', help='Nom du joueur à valider')
    
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        print("🎱 LANCEMENT DU SCRAPING")
        scraper_main()
        
    elif args.command == 'world-cups':
        show_world_cups()
        
    elif args.command == 'setup-bot':
        players_list = None
        if args.players:
            players_list = [p.strip() for p in args.players.split(',')]
        setup_bot_unified(args.tournament_id, args.player, players_list, args.bot_type)
        
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
            print()
            print("📋 DONNÉES JOUEUR CONFIGURÉES")
            print("-" * 40)
            
            # Champs indispensables avec leurs valeurs
            essential_fields = [
                ('federation', 'Fédération'),
                ('lastName', 'Nom'),
                ('firstName', 'Prénom'),  
                ('playerId', 'ID Joueur'),
                ('nationality', 'Nationalité'),
                ('dateOfBirth', 'Date naissance'),
                ('country', 'Pays'),
                ('email', 'Email')
            ]
            
            for field_key, field_label in essential_fields:
                value = player_data.get(field_key, '')
                status = "✅" if value else "❌"
                print(f"   {status} {field_label:15}: {value}")
                
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ Configuration joueur: {e}")
            print("💡 Éditez config/player.json avec vos données")
    
    elif args.command == 'list-players':
        list_players()
    
    elif args.command == 'create-player':
        create_player(args.player_name, args.from_player)
    
    elif args.command == 'validate-player':
        validate_player(args.player_name)
    
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()