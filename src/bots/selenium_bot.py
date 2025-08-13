#!/usr/bin/env python3
"""
Bot UMB avec Selenium
Utilise la configuration centralisée BaseBotConfig
"""

import sys
import argparse
from pathlib import Path
import time
import threading
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import logging
from concurrent.futures import ThreadPoolExecutor

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from bots.base_bot import BaseBotConfig

class SeleniumBot:
    def __init__(self, config_file: str = None, player_file: str = None):
        # Configuration centralisée
        self.config = BaseBotConfig(config_file, player_file)
        
        # Validation de la configuration
        errors = self.config.validate_config()
        if errors:
            raise ValueError(f"Configuration invalide: {errors}")
        
        # Configuration bot
        self.bot_settings = self.config.get_bot_settings()
        self.tournament_id = self.config.get_tournament_id()
        self.registration_datetime = self.config.get_registration_datetime()
        self.check_start_datetime = self.config.get_check_start_datetime()
        self.player_data = self.config.get_player_data_for_selenium()
        
        # Setup logging
        self.logger = self.setup_logging()
        
        # Selenium et HTTP
        self.driver = None
        self.session = requests.Session()
        self.registration_url = self.config.get_registration_url()
        self.details_url = f"https://files.umb-carom.org/public/TournametDetails.aspx?id={self.tournament_id}"
        
        # États de surveillance
        self.is_monitoring = False
        self.registration_opened = False
        self.registration_completed = False
        
        # Performance tracking
        self.check_count = 0
        self.last_check_time = None
        
    def setup_logging(self):
        """Configure le logging haute performance"""
        log_path = self.config.get_log_path('selenium_bot')
        
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
    
    def setup_ultra_fast_browser(self):
        """Configure un navigateur ultra-optimisé"""
        chrome_options = Options()
        
        # Performance maximale
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-images')
        # chrome_options.add_argument('--disable-javascript')  # Garde JS pour ASP.NET
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--memory-pressure-off')
        
        # Cache et réseau
        chrome_options.add_argument('--disk-cache-size=0')
        chrome_options.add_argument('--media-cache-size=0')
        
        # Taille de fenêtre fixe
        chrome_options.add_argument('--window-size=1200,800')
        
        # Prefs pour désactiver images et autres
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(2)  # Timeout court
            self.logger.info("🚀 Navigateur ultra-rapide configuré")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration navigateur: {e}")
            return False
    
    def quick_url_check(self):
        """Vérification ultra-rapide de l'URL via requests"""
        try:
            start_time = time.time()
            response = self.session.get(self.registration_url, timeout=3)
            check_time = (time.time() - start_time) * 1000  # en ms
            
            self.check_count += 1
            self.last_check_time = check_time
            
            # Analyse rapide du contenu
            if response.status_code == 200:
                content = response.text
                
                # Vérifier si c'est le formulaire (pas la redirection)
                if 'txtLName' in content and 'btnSave' in content and 'No Data to display' not in content:
                    self.logger.info(f"🎯 FORMULAIRE DÉTECTÉ! (check #{self.check_count}, {check_time:.1f}ms)")
                    return True, "FORM_AVAILABLE"
                elif 'No Data to display' in content or 'Tournament Details' in content:
                    return False, "REDIRECT_OR_CLOSED"
                else:
                    return False, "UNKNOWN_STATE"
            else:
                return False, f"HTTP_{response.status_code}"
                
        except Exception as e:
            return False, f"ERROR_{str(e)[:20]}"
    
    def ultra_fast_fill_and_submit(self):
        """Remplissage et soumission ultra-rapides"""
        try:
            start_time = time.time()
            
            # Navigation immédiate
            self.driver.get(self.registration_url)
            nav_time = time.time()
            
            # Vérifier qu'on est bien sur le bon formulaire
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.NAME, "txtLName"))
            )
            
            # Vérifier qu'il n'y a pas de redirection
            if "PlayerModify.aspx" not in self.driver.current_url:
                self.logger.warning(f"⚠️ Redirection détectée: {self.driver.current_url}")
                return False
                
            form_ready_time = time.time()
            
            # Remplissage ultra-rapide (seulement les champs obligatoires)
            mandatory_fields = [
                ('ddlFedration', self.player_data['federation'], 'select'),
                ('txtLName', self.player_data['lastName'], 'input'),
                ('txtFName', self.player_data['firstName'], 'input'),
                ('txtRankID', self.player_data['playerId'], 'input'),
                ('ddlNationality', self.player_data['nationality'], 'select'),
                ('txtDOB', self.player_data['dateOfBirth'], 'input'),
                ('ddlCountry', self.player_data['country'], 'select'),
                ('txtEmail', self.player_data['email'], 'input')
            ]
            
            for field_name, value, field_type in mandatory_fields:
                if value:
                    if field_type == 'select':
                        select_element = Select(self.driver.find_element(By.NAME, field_name))
                        select_element.select_by_value(value)
                    else:
                        field = self.driver.find_element(By.NAME, field_name)
                        field.clear()
                        field.send_keys(value)
            
            fill_time = time.time()
            
            # Soumission immédiate
            submit_button = self.driver.find_element(By.NAME, "btnSave")
            submit_button.click()
            submit_time = time.time()
            
            # Calculs de performance
            total_time = submit_time - start_time
            nav_duration = nav_time - start_time
            form_duration = form_ready_time - nav_time
            fill_duration = fill_time - form_ready_time
            submit_duration = submit_time - fill_time
            
            self.logger.info(f"⚡ INSCRIPTION SOUMISE!")
            self.logger.info(f"   📊 Navigation: {nav_duration:.2f}s")
            self.logger.info(f"   📊 Formulaire ready: {form_duration:.2f}s")
            self.logger.info(f"   📊 Remplissage: {fill_duration:.2f}s")
            self.logger.info(f"   📊 Soumission: {submit_duration:.2f}s")
            self.logger.info(f"   📊 TOTAL: {total_time:.2f}s")
            
            self.registration_completed = True
            
            # Vérifier le résultat
            time.sleep(3)  # Attendre la réponse serveur
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # Indicateurs de succès
            success_indicators = ['success', 'confirm', 'registered', 'inscrit', 'thank']
            error_indicators = ['error', 'erreur', 'failed', 'échec']
            
            if any(indicator in current_url or indicator in page_source for indicator in success_indicators):
                self.logger.info("🎉 INSCRIPTION CONFIRMÉE!")
                return True
            elif any(indicator in current_url or indicator in page_source for indicator in error_indicators):
                self.logger.error("❌ ERREUR D'INSCRIPTION DÉTECTÉE")
                self.driver.save_screenshot(f"registration_error_{datetime.now().strftime('%H%M%S')}.png")
                return False
            else:
                self.logger.warning("⚠️ Statut incertain - sauvegarde pour analyse")
                self.driver.save_screenshot(f"registration_unknown_{datetime.now().strftime('%H%M%S')}.png")
                # Sauvegarder le code source pour analyse
                with open(f"page_source_{datetime.now().strftime('%H%M%S')}.html", 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                return True  # Supposer succès si pas d'erreur explicite
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'inscription: {e}")
            self.driver.save_screenshot(f"registration_error_{datetime.now().strftime('%H%M%S')}.png")
            return False
    
    def calculate_wait_time(self):
        """Calcule le temps d'attente jusqu'au début de surveillance"""
        now = datetime.now()
        wait_seconds = (self.check_start_datetime - now).total_seconds()
        return max(0, wait_seconds)
    
    def intensive_monitoring(self):
        """Surveillance intensive pendant la période critique"""
        self.logger.info(f"🔥 SURVEILLANCE INTENSIVE DÉMARRÉE")
        
        while not self.registration_completed:
            now = datetime.now()
            
            # Calculer l'intervalle de vérification basé sur la proximité de l'heure cible
            time_to_target = (self.registration_datetime - now).total_seconds()
            
            critical_window = self.bot_settings.get('critical_window', 10)
            if time_to_target <= critical_window:
                check_interval = self.bot_settings.get('check_interval_critical', 0.1)  # 100ms pendant les dernières secondes
                if time_to_target <= 0:
                    self.logger.info(f"🚨 HEURE CIBLE ATTEINTE! Check #{self.check_count}")
            else:
                check_interval = self.bot_settings.get('check_interval_normal', 1.0)
            
            # Vérification rapide
            is_available, status = self.quick_url_check()
            
            if is_available:
                self.logger.info(f"🎯 FORMULAIRE DISPONIBLE! Lancement inscription...")
                self.registration_opened = True
                
                # Lancer l'inscription en parallèle pour ne pas perdre de temps
                if self.ultra_fast_fill_and_submit():
                    break
                else:
                    self.logger.warning("⚠️ Première tentative échouée, retry...")
                    continue
            
            # Log périodique pour montrer que ça fonctionne
            if self.check_count % 50 == 0:  # Toutes les 50 vérifications
                self.logger.info(f"⏰ Check #{self.check_count} - {status} - Dernier: {self.last_check_time:.1f}ms")
            
            time.sleep(check_interval)
    
    def run(self):
        """Lance le bot complet"""
        self.logger.info("🎱 UMB SELENIUM BOT")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 Tournoi: {self.tournament_id}")
        self.logger.info(f"📅 Inscription: {self.registration_datetime.strftime('%Y-%m-%d à %H:%M:%S')}")
        self.logger.info(f"🔍 Début surveillance: {self.check_start_datetime.strftime('%H:%M:%S')}")
        self.logger.info(f"👤 Joueur: {self.player_data['firstName']} {self.player_data['lastName']}")
        self.logger.info("=" * 60)
        
        try:
            # Calculer le temps d'attente
            wait_time = self.calculate_wait_time()
            
            if wait_time > 0:
                self.logger.info(f"⏳ Attente de {wait_time:.1f} secondes avant surveillance...")
                time.sleep(wait_time)
            
            # Configurer le navigateur juste avant la surveillance
            if not self.setup_ultra_fast_browser():
                self.logger.error("❌ Impossible de configurer le navigateur")
                return
            
            # Lancer la surveillance intensive
            self.intensive_monitoring()
            
        except KeyboardInterrupt:
            self.logger.info("👋 Bot arrêté par l'utilisateur")
        except Exception as e:
            self.logger.error(f"❌ Erreur critique: {e}")
        finally:
            if self.driver:
                if not self.registration_completed:
                    input("⏸️ Appuyez sur Entrée pour fermer le navigateur...")
                self.driver.quit()
            
            # Statistiques finales
            self.logger.info(f"📊 Statistiques: {self.check_count} vérifications effectuées")
            if self.registration_completed:
                self.logger.info("🎉 MISSION ACCOMPLIE!")
            else:
                self.logger.info("⚠️ Mission incomplète")

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Bot Selenium UMB")
    parser.add_argument('--config', help='Fichier de configuration du tournoi')
    parser.add_argument('--player', help='Fichier de configuration du joueur')
    parser.add_argument('--delay', type=int, help='Délai en millisecondes avant démarrage')
    args = parser.parse_args()
    
    try:
        # Appliquer le délai si spécifié
        if args.delay:
            time.sleep(args.delay / 1000.0)
        
        bot = SeleniumBot(args.config, args.player)
        bot.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
