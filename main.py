#!/usr/bin/env python3
"""
UMB Tournament Scraper
Récupère les informations des tournois de billard français depuis umb-carom.org
"""

import requests
import json
import csv
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os

# ================== CONFIGURATION ==================
# Modifiez ces variables selon vos besoins
START_ID = 1  # ID de début (inclus)
END_ID = 400  # ID de fin (inclus)
DELAY_BETWEEN_REQUESTS = 1.0  # Délai en secondes entre chaque requête
OUTPUT_PREFIX = "umb_tournaments"  # Préfixe des fichiers de sortie
TIMEOUT = 10  # Timeout en secondes pour chaque requête


# ===================================================

class UMBScraper:
    def __init__(self):
        self.base_url = "https://files.umb-carom.org/public/TournametDetails.aspx?id="
        self.session = requests.Session()

        # Headers pour imiter un navigateur
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Statistiques
        self.stats = {
            'total_tested': 0,
            'successful': 0,
            'errors': 0,
            'no_tournament': 0
        }

    def extract_tournament_info(self, html_content: str) -> dict:
        """Extrait les informations du tournoi à partir du HTML"""
        # Vérifications d'erreur
        error_indicators = [
            "Server Error in '/' Application",
            "Runtime Error",
            "Exception Details",
            "404"
        ]

        for indicator in error_indicators:
            if indicator in html_content:
                return None

        # Vérifier la présence de contenu de tournoi
        if "Tournament Details" not in html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()

        # Nettoyer le texte
        lines = text.split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]

        # Extraction des informations
        tournament_info = {}

        for i, line in enumerate(clean_lines):
            if line == "Tournament:":
                tournament_info['tournament'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""
            elif line == "Starts on:":
                tournament_info['starts_on'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""
            elif line == "Ends on:":
                tournament_info['ends_on'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""
            elif line == "Organized by:":
                tournament_info['organized_by'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""
            elif line == "Place:":
                tournament_info['place'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""
            elif line == "Material:":
                tournament_info['material'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""
            elif line == "Delegate UMB:":
                tournament_info['delegate_umb'] = clean_lines[i + 1] if i + 1 < len(clean_lines) else ""

        # Valider qu'on a au moins un nom de tournoi
        if not tournament_info.get('tournament'):
            return None

        return tournament_info

    def get_tournament_details(self, tournament_id: int) -> dict:
        """Récupère les détails d'un tournoi spécifique"""
        url = f"{self.base_url}{tournament_id}"

        try:
            response = self.session.get(url, timeout=TIMEOUT)

            if response.status_code != 200:
                return None

            tournament_info = self.extract_tournament_info(response.text)

            if tournament_info:
                tournament_info['id'] = tournament_id
                tournament_info['url'] = url
                tournament_info['scraped_at'] = datetime.now().isoformat()
                
                # Ajouter la date de début des inscriptions pour World Cup 3-Cushion
                registration_start = self.calculate_registration_start(
                    tournament_info.get('tournament', ''),
                    tournament_info.get('starts_on', '')
                )
                if registration_start:
                    tournament_info['registration_start'] = registration_start
                
                return tournament_info

        except Exception as e:
            print(f"Erreur lors de la récupération de l'ID {tournament_id}: {e}")

        return None

    def calculate_registration_start(self, tournament_name: str, starts_on: str) -> str:
        """Calcule la date de début des inscriptions pour les tournois World Cup 3-Cushion"""
        if tournament_name != "World Cup 3-Cushion":
            return None
        
        start_date = self.parse_date(starts_on)
        if not start_date:
            return None
        
        # 8 semaines avant = 56 jours
        registration_start = start_date - timedelta(days=56)
        
        # Format: "DD-Month-YYYY à 12:00 GMT Paris"
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        return f"{registration_start.day:02d}-{months[registration_start.month-1]}-{registration_start.year} à 12:00 GMT Paris"

    def scrape_tournaments(self, start_id: int, end_id: int) -> list:
        """Scrape tous les tournois dans la plage donnée"""
        tournaments = []

        print(f"🚀 Début du scraping des tournois de {start_id} à {end_id}")
        print(f"⏱️  Délai entre requêtes: {DELAY_BETWEEN_REQUESTS}s")
        print(f"📁 Fichiers de sortie: {OUTPUT_PREFIX}.json et {OUTPUT_PREFIX}.csv")
        print("-" * 60)

        for tournament_id in range(start_id, end_id + 1):
            self.stats['total_tested'] += 1

            # Affichage du progress
            progress = (tournament_id - start_id + 1) / (end_id - start_id + 1) * 100
            print(f"[{progress:5.1f}%] Testing ID {tournament_id:3d}...", end=' ')

            tournament_info = self.get_tournament_details(tournament_id)

            if tournament_info:
                tournaments.append(tournament_info)
                self.stats['successful'] += 1
                print(f"✅ {tournament_info['tournament'][:50]}...")
            else:
                # Distinguer les erreurs des pages sans tournoi
                try:
                    response = self.session.get(f"{self.base_url}{tournament_id}", timeout=TIMEOUT)
                    if response.status_code == 200 and "Server Error" in response.text:
                        self.stats['errors'] += 1
                        print("❌ Erreur serveur")
                    else:
                        self.stats['no_tournament'] += 1
                        print("⚪ Pas de tournoi")
                except:
                    self.stats['errors'] += 1
                    print("❌ Erreur réseau")

            # Délai entre les requêtes
            if tournament_id < end_id:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        self.print_stats()
        return tournaments

    def print_stats(self):
        """Affiche les statistiques du scraping"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES DU SCRAPING")
        print("=" * 60)
        print(f"Total d'IDs testés:     {self.stats['total_tested']:4d}")
        print(f"Tournois trouvés:       {self.stats['successful']:4d}")
        print(f"Erreurs serveur:        {self.stats['errors']:4d}")
        print(f"Pas de tournoi:         {self.stats['no_tournament']:4d}")
        print(f"Taux de succès:         {(self.stats['successful'] / self.stats['total_tested'] * 100):5.1f}%")
        print("=" * 60)

    def save_to_json(self, tournaments: list, filename: str):
        """Sauvegarde les données en JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'scraped_at': datetime.now().isoformat(),
                        'total_tournaments': len(tournaments),
                        'stats': self.stats
                    },
                    'tournaments': tournaments
                }, f, ensure_ascii=False, indent=2)

            print(f"✅ Données JSON sauvegardées dans {filename}")

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde JSON: {e}")

    def save_to_csv(self, tournaments: list, filename: str):
        """Sauvegarde les données en CSV"""
        if not tournaments:
            print("⚠️  Aucun tournoi à sauvegarder en CSV")
            return

        try:
            fieldnames = [
                'id', 'tournament', 'starts_on', 'ends_on',
                'organized_by', 'place', 'material', 'delegate_umb',
                'registration_start', 'url', 'scraped_at'
            ]

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tournaments)

            print(f"✅ Données CSV sauvegardées dans {filename}")

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde CSV: {e}")

    def filter_future_tournaments(self, tournaments: list) -> list:
        """Filtre les tournois futurs"""
        future_tournaments = []
        current_date = datetime.now()

        for tournament in tournaments:
            try:
                start_date_str = tournament.get('starts_on', '')
                if start_date_str:
                    # Essayer plusieurs formats de date
                    date_formats = [
                        "%d-%B-%Y",  # 03-December-2023
                        "%d/%m/%Y",  # 03/12/2023
                        "%Y-%m-%d",  # 2023-12-03
                        "%d.%m.%Y"  # 03.12.2023
                    ]

                    for date_format in date_formats:
                        try:
                            start_date = datetime.strptime(start_date_str, date_format)
                            if start_date > current_date:
                                future_tournaments.append(tournament)
                            break
                        except ValueError:
                            continue

            except Exception:
                # Si on ne peut pas parser la date, on garde le tournoi par sécurité
                future_tournaments.append(tournament)

        return future_tournaments

    def load_existing_data(self, filename: str) -> dict:
        """Charge les données existantes depuis le fichier JSON"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de {filename}: {e}")
        
        return {'metadata': {}, 'tournaments': []}

    def parse_date(self, date_str: str) -> datetime:
        """Parse une date string en datetime"""
        if not date_str:
            return None
        
        date_formats = [
            "%d-%B-%Y",  # 03-December-2023
            "%d/%m/%Y",  # 03/12/2023
            "%Y-%m-%d",  # 2023-12-03
            "%d.%m.%Y"  # 03.12.2023
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        return None

    def identify_ids_to_rescrape(self, existing_data: dict, max_id: int = 400) -> list:
        """Identifie les IDs qui ont besoin d'être re-scrappés"""
        existing_tournaments = existing_data.get('tournaments', [])
        existing_ids = {t['id'] for t in existing_tournaments}
        current_date = datetime.now()
        
        ids_to_rescrape = set()
        
        # 1. IDs manquants dans la plage
        all_ids = set(range(1, max_id + 1))
        missing_ids = all_ids - existing_ids
        ids_to_rescrape.update(missing_ids)
        print(f"📋 IDs manquants: {len(missing_ids)}")
        
        # 2. Tournois "Reserved for UMB"
        reserved_ids = []
        for tournament in existing_tournaments:
            if tournament.get('tournament') == 'Reserved for UMB':
                reserved_ids.append(tournament['id'])
                ids_to_rescrape.add(tournament['id'])
        print(f"🔒 Tournois 'Reserved for UMB': {len(reserved_ids)}")
        
        # 3. Tournois futurs (starts_on > aujourd'hui)
        future_ids = []
        for tournament in existing_tournaments:
            start_date = self.parse_date(tournament.get('starts_on', ''))
            if start_date and start_date > current_date:
                future_ids.append(tournament['id'])
                ids_to_rescrape.add(tournament['id'])
        print(f"🔮 Tournois futurs: {len(future_ids)}")
        
        return sorted(list(ids_to_rescrape))

    def update_existing_data(self, existing_data: dict, new_tournaments: list) -> dict:
        """Met à jour les données existantes avec les nouvelles données"""
        existing_tournaments = existing_data.get('tournaments', [])
        existing_by_id = {t['id']: t for t in existing_tournaments}
        
        # Mettre à jour ou ajouter les nouveaux tournois
        for tournament in new_tournaments:
            existing_by_id[tournament['id']] = tournament
        
        # Reconstruire la liste
        updated_tournaments = list(existing_by_id.values())
        updated_tournaments.sort(key=lambda x: x['id'])
        
        # Mettre à jour les métadonnées
        updated_data = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_tournaments': len(updated_tournaments),
                'stats': self.stats,
                'last_update_type': 'selective_rescrape'
            },
            'tournaments': updated_tournaments
        }
        
        return updated_data

    def selective_scrape(self, json_filename: str = "umb_tournaments.json", max_id: int = 400):
        """Effectue un scraping sélectif basé sur les données existantes"""
        print("🔄 SCRAPING SÉLECTIF OPTIMISÉ")
        print("=" * 60)
        
        # Charger les données existantes
        existing_data = self.load_existing_data(json_filename)
        existing_count = len(existing_data.get('tournaments', []))
        print(f"📊 Tournois existants: {existing_count}")
        
        # Identifier les IDs à re-scrapper
        ids_to_rescrape = self.identify_ids_to_rescrape(existing_data, max_id)
        
        if not ids_to_rescrape:
            print("✅ Aucun ID à re-scrapper, les données sont à jour!")
            return existing_data.get('tournaments', [])
        
        print(f"🎯 Total IDs à re-scrapper: {len(ids_to_rescrape)}")
        print(f"📝 IDs: {ids_to_rescrape[:10]}{'...' if len(ids_to_rescrape) > 10 else ''}")
        print("-" * 60)
        
        # Effectuer le scraping sélectif
        new_tournaments = []
        for i, tournament_id in enumerate(ids_to_rescrape):
            progress = (i + 1) / len(ids_to_rescrape) * 100
            print(f"[{progress:5.1f}%] Re-scraping ID {tournament_id:3d}...", end=' ')
            
            tournament_info = self.get_tournament_details(tournament_id)
            
            if tournament_info:
                new_tournaments.append(tournament_info)
                self.stats['successful'] += 1
                print(f"✅ {tournament_info['tournament'][:50]}...")
            else:
                self.stats['no_tournament'] += 1
                print("⚪ Pas de tournoi")
            
            self.stats['total_tested'] += 1
            
            # Délai entre les requêtes
            if i < len(ids_to_rescrape) - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        print(f"\n📈 Nouveaux/Mis à jour: {len(new_tournaments)}")
        
        # Mettre à jour les données existantes
        updated_data = self.update_existing_data(existing_data, new_tournaments)
        updated_tournaments = updated_data.get('tournaments', [])
        
        # Sauvegarder immédiatement les données mises à jour
        self.save_to_json(updated_tournaments, json_filename)
        
        # Marquer que le mode sélectif a été utilisé
        self._selective_mode_used = True
        
        return updated_tournaments

    def display_results(self, tournaments: list):
        """Affiche les résultats trouvés"""
        if not tournaments:
            print("⚠️  Aucun tournoi trouvé")
            return

        print(f"\n🏆 TOURNOIS TROUVÉS ({len(tournaments)})")
        print("=" * 80)

        for tournament in tournaments:
            print(f"ID {tournament['id']:3d}: {tournament['tournament']}")
            print(f"      📅 {tournament['starts_on']} - {tournament['ends_on']}")
            print(f"      📍 {tournament['place']}")
            
            # Afficher la date de début des inscriptions si disponible
            if tournament.get('registration_start'):
                print(f"      📝 Inscriptions: {tournament['registration_start']}")
            
            print(f"      🔗 {tournament['url']}")
            print()

        # Tournois futurs
        future_tournaments = self.filter_future_tournaments(tournaments)
        if future_tournaments:
            print(f"🔮 TOURNOIS FUTURS ({len(future_tournaments)})")
            print("=" * 80)
            for tournament in future_tournaments:
                print(f"ID {tournament['id']:3d}: {tournament['tournament']}")
                print(f"      📅 {tournament['starts_on']}")
                print(f"      📍 {tournament['place']}")
                
                # Afficher la date de début des inscriptions si disponible
                if tournament.get('registration_start'):
                    print(f"      📝 Inscriptions: {tournament['registration_start']}")
                
                print()


def main():
    """Fonction principale"""
    print("🎱 UMB TOURNAMENT SCRAPER")
    print("=" * 60)
    
    # Créer le scraper
    scraper = UMBScraper()
    
    # Vérifier si le fichier JSON existe pour le scraping sélectif
    json_file = f"{OUTPUT_PREFIX}.json"
    
    if os.path.exists(json_file):
        print("📁 Fichier JSON existant détecté")
        print("🔄 Mode: SCRAPING SÉLECTIF (optimisé)")
        print(f"  - Fichier de base: {json_file}")
        print(f"  - Plage d'IDs: 1 à {END_ID}")
        print(f"  - Délai: {DELAY_BETWEEN_REQUESTS}s")
        print(f"  - Timeout: {TIMEOUT}s")
        print("=" * 60)
        
        # Lancer le scraping sélectif
        tournaments = scraper.selective_scrape(json_file, END_ID)
        scraper.print_stats()
        
    else:
        print("📝 Aucun fichier JSON existant")
        print("🔄 Mode: SCRAPING COMPLET")
        print(f"  - Plage d'IDs: {START_ID} à {END_ID}")
        print(f"  - Délai: {DELAY_BETWEEN_REQUESTS}s")
        print(f"  - Timeout: {TIMEOUT}s")
        print(f"  - Fichiers de sortie: {OUTPUT_PREFIX}.json/csv")
        print("=" * 60)
        
        # Lancer le scraping complet
        tournaments = scraper.scrape_tournaments(START_ID, END_ID)

    # Sauvegarder les résultats
    if tournaments:
        # En mode sélectif, le JSON est déjà sauvegardé dans selective_scrape()
        if not os.path.exists(json_file) or not hasattr(scraper, '_selective_mode_used'):
            scraper.save_to_json(tournaments, f"{OUTPUT_PREFIX}.json")
        scraper.save_to_csv(tournaments, f"{OUTPUT_PREFIX}.csv")

        # Sauvegarder séparément les tournois futurs
        future_tournaments = scraper.filter_future_tournaments(tournaments)
        if future_tournaments:
            scraper.save_to_json(future_tournaments, f"{OUTPUT_PREFIX}_future.json")
            scraper.save_to_csv(future_tournaments, f"{OUTPUT_PREFIX}_future.csv")

        # Afficher les résultats
        scraper.display_results(tournaments)
    else:
        print("⚠️  Aucun tournoi trouvé dans la plage spécifiée")

    print(f"\n✅ Scraping terminé!")


if __name__ == "__main__":
    main()
