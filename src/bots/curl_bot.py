#!/usr/bin/env python3
"""
Bot UMB avec cURL/requests pur
Utilise la configuration centralisée BaseBotConfig
"""

import sys
import argparse
from pathlib import Path
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import threading

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from bots.base_bot import BaseBotConfig

class CurlBot:
    def __init__(self, config_file: str = None):
        # Configuration centralisée
        self.config = BaseBotConfig(config_file)
        
        # Validation de la configuration
        errors = self.config.validate_config()
        if errors:
            raise ValueError(f"Configuration invalide: {errors}")
        
        # Configuration bot
        self.bot_settings = self.config.get_bot_settings()
        self.tournament_id = self.config.get_tournament_id()
        self.registration_datetime = self.config.get_registration_datetime()
        self.check_start_datetime = self.config.get_check_start_datetime()
        self.player_data = self.config.get_player_data_for_curl()
        
        # Setup logging
        self.logger = self.setup_logging()
        
        # Session HTTP
        self.session = requests.Session()
        self.setup_session()
        
        self.registration_url = self.config.get_registration_url()
        
        # État du bot
        self.form_available = False
        self.registration_completed = False
        self.check_count = 0
        
        # Cache pour tokens ASP.NET
        self.cached_viewstate = None
        self.cached_eventvalidation = None
        self.cached_viewstategenerator = None
        
    def setup_logging(self):
        """Configure logging ultra-précis"""
        log_path = self.config.get_log_path('curl_bot')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s.%(msecs)03d - %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def setup_session(self):
        """Configure session HTTP optimisée"""
        # Headers pour imiter un vrai navigateur
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0'
        })
        
        # Configuration de performance
        self.session.mount('https://', requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0  # Pas de retry pour la vitesse
        ))
        
        self.logger.info("🚀 Session HTTP optimisée configurée")
    
    def extract_asp_net_tokens(self, html_content):
        """Extrait les tokens ASP.NET cachés"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
        viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        
        tokens = {
            '__VIEWSTATE': viewstate['value'] if viewstate else '',
            '__EVENTVALIDATION': eventvalidation['value'] if eventvalidation else '',
            '__VIEWSTATEGENERATOR': viewstategenerator['value'] if viewstategenerator else ''
        }
        
        return tokens
    
    def quick_availability_check(self):
        """Vérification ultra-rapide de disponibilité"""
        try:
            start_time = time.time()
            
            response = self.session.get(
                self.registration_url, 
                timeout=2,
                allow_redirects=True
            )
            
            check_time = (time.time() - start_time) * 1000
            self.check_count += 1
            
            if response.status_code == 200:
                content = response.text
                
                # Vérifier si c'est le formulaire d'inscription
                if ('txtLName' in content and 
                    'btnSave' in content and 
                    'No Data to display' not in content and
                    'PlayerModify.aspx' in response.url):
                    
                    # Extraire les tokens pour le submit
                    tokens = self.extract_asp_net_tokens(content)
                    if tokens['__VIEWSTATE'] and tokens['__EVENTVALIDATION']:
                        self.cached_viewstate = tokens['__VIEWSTATE']
                        self.cached_eventvalidation = tokens['__EVENTVALIDATION'] 
                        self.cached_viewstategenerator = tokens['__VIEWSTATEGENERATOR']
                        
                        self.logger.info(f"🎯 FORMULAIRE PRÊT! (#{self.check_count}, {check_time:.1f}ms)")
                        return True, "FORM_READY"
                    else:
                        self.logger.warning("⚠️ Tokens ASP.NET manquants")
                        return False, "MISSING_TOKENS"
                
                elif 'No Data to display' in content or 'TournamentDetails.aspx' in response.url:
                    return False, "REDIRECT_OR_CLOSED"
                else:
                    return False, "UNKNOWN_CONTENT"
            else:
                return False, f"HTTP_{response.status_code}"
                
        except Exception as e:
            return False, f"ERROR_{str(e)[:20]}"
    
    def ultra_fast_submit(self):
        """Soumission ultra-rapide avec cURL"""
        try:
            start_time = time.time()
            
            # Préparer les données POST
            post_data = {
                # Tokens ASP.NET obligatoires
                '__VIEWSTATE': self.cached_viewstate,
                '__EVENTVALIDATION': self.cached_eventvalidation,
                '__VIEWSTATEGENERATOR': self.cached_viewstategenerator,
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                
                # Données du joueur
                **self.player_data,
                
                # Bouton de soumission
                'btnSave': 'Submit'
            }
            
            # Headers spécifiques pour POST
            post_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://files.umb-carom.org',
                'Referer': self.registration_url
            }
            
            # Soumission POST ultra-rapide
            response = self.session.post(
                self.registration_url,
                data=post_data,
                headers=post_headers,
                timeout=5,
                allow_redirects=True
            )
            
            submit_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"⚡ SOUMISSION TERMINÉE en {submit_time:.1f}ms")
            self.logger.info(f"📊 Status: {response.status_code}")
            self.logger.info(f"📊 URL finale: {response.url}")
            
            # Analyser la réponse
            if response.status_code == 200:
                content = response.text.lower()
                
                # Indicateurs de succès
                success_indicators = ['success', 'confirm', 'registered', 'inscrit', 'thank', 'merci']
                error_indicators = ['error', 'erreur', 'failed', 'échec', 'invalid', 'required']
                
                if any(indicator in content for indicator in success_indicators):
                    self.logger.info("🎉 INSCRIPTION CONFIRMÉE!")
                    self.registration_completed = True
                    return True
                elif any(indicator in content for indicator in error_indicators):
                    self.logger.error("❌ ERREUR DÉTECTÉE dans la réponse")
                    # Sauvegarder pour débug
                    with open(f'error_response_{datetime.now().strftime("%H%M%S")}.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    return False
                else:
                    self.logger.warning("⚠️ Statut incertain - analyse manuelle requise")
                    # Sauvegarder la réponse pour analyse
                    with open(f'response_{datetime.now().strftime("%H%M%S")}.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    # Vérifier si on est retourné sur le formulaire (=échec)
                    if 'playermodify.aspx' in response.url.lower() and 'txtlname' in content:
                        self.logger.error("❌ Retour sur formulaire = échec inscription")
                        return False
                    
                    return True  # Supposer succès si redirection
            else:
                self.logger.error(f"❌ Status HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erreur soumission: {e}")
            return False
    
    def intensive_monitoring(self):
        """Surveillance intensive ultra-rapide"""
        self.logger.info("🔥 SURVEILLANCE INTENSIVE cURL")
        
        while not self.registration_completed:
            now = datetime.now()
            time_to_target = (self.registration_datetime - now).total_seconds()
            
            # Intervalle adaptatif
            if time_to_target <= 5:  # 5 dernières secondes
                interval = self.bot_settings.get('check_interval_critical', 0.05)  # 50ms
                if time_to_target <= 0:
                    self.logger.info(f"🚨 HEURE CIBLE! Check #{self.check_count}")
            else:
                interval = self.bot_settings.get('check_interval_normal', 0.5)  # 500ms
            
            # Vérification
            is_available, status = self.quick_availability_check()
            
            if is_available:
                self.logger.info("🎯 LANCEMENT INSCRIPTION cURL...")
                self.form_available = True
                
                success = self.ultra_fast_submit()
                if success:
                    break
                else:
                    self.logger.warning("⚠️ Tentative échouée, retry avec nouveaux tokens...")
                    # Invalider le cache des tokens pour re-fetch
                    self.cached_viewstate = None
                    self.cached_eventvalidation = None
                    self.cached_viewstategenerator = None
                    time.sleep(0.1)
                    continue
            
            # Log périodique
            if self.check_count % 100 == 0:
                self.logger.info(f"⏰ Check #{self.check_count} - {status}")
            
            time.sleep(interval)
    
    def run(self):
        """Lance le bot cURL"""
        self.logger.info("🚀 CURL BOT")
        self.logger.info("=" * 50)
        self.logger.info(f"🎯 Tournoi: {self.tournament_id}")
        self.logger.info(f"📅 {self.registration_datetime.strftime('%Y-%m-%d à %H:%M:%S')}")
        self.logger.info(f"👤 {self.player_data['txtFName']} {self.player_data['txtLName']}")
        self.logger.info("=" * 50)
        
        try:
            # Calculer attente
            wait_time = (self.check_start_datetime - datetime.now()).total_seconds()
            
            if wait_time > 0:
                self.logger.info(f"⏳ Attente {wait_time:.1f}s...")
                time.sleep(wait_time)
            
            # Surveillance
            self.intensive_monitoring()
            
        except KeyboardInterrupt:
            self.logger.info("👋 Arrêt utilisateur")
        except Exception as e:
            self.logger.error(f"❌ Erreur: {e}")
        finally:
            self.logger.info(f"📊 {self.check_count} vérifications total")
            if self.registration_completed:
                self.logger.info("🎉 MISSION RÉUSSIE!")

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Bot cURL UMB")
    parser.add_argument('--config', help='Fichier de configuration du tournoi')
    args = parser.parse_args()
    
    try:
        bot = CurlBot(args.config)
        bot.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
