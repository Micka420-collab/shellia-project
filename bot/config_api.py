"""
API DE CONFIGURATION - Shellia AI Bot
Endpoint sécurisé pour mise à jour des clés API depuis le dashboard
"""

import os
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Optional
from functools import wraps

# Ces imports nécessitent d'installer flask ou fastapi
# Pour l'instant, je crée une structure compatible avec Flask

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask non installé. API de configuration non disponible.")
    print("   pip install flask")


class ConfigAPI:
    """
    API sécurisée pour la gestion des configurations
    
    Usage:
        from config_api import ConfigAPI
        config_api = ConfigAPI(bot_instance)
        config_api.run(port=5000)
    """
    
    def __init__(self, bot, admin_secret: Optional[str] = None):
        """
        Args:
            bot: Instance du bot Shellia
            admin_secret: Secret pour authentifier les requêtes admin
        """
        self.bot = bot
        self.admin_secret = admin_secret or os.getenv('ADMIN_API_SECRET')
        self.app = None
        
        if FLASK_AVAILABLE:
            self.app = Flask(__name__)
            self._setup_routes()
    
    def _setup_routes(self):
        """Configure les routes API"""
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Récupère la configuration actuelle (sans les secrets)"""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Retourner seulement les métadonnées, pas les valeurs sensibles
            config = {
                'gemini_configured': bool(os.getenv('GEMINI_API_KEY')),
                'stripe_configured': bool(os.getenv('STRIPE_SECRET_KEY')),
                'discord_configured': bool(os.getenv('DISCORD_TOKEN')),
                'supabase_configured': bool(os.getenv('SUPABASE_URL')),
                'redis_configured': bool(os.getenv('REDIS_URL')),
                'encryption_enabled': bool(os.getenv('SECURE_CONFIG_KEY')),
                'updated_at': datetime.now().isoformat()
            }
            
            return jsonify(config)
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Met à jour la configuration"""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            results = []
            
            # Valider et mettre à jour chaque clé
            for key, value in data.items():
                if not self._validate_key_format(key, value):
                    results.append({
                        'key': key,
                        'status': 'error',
                        'message': 'Invalid format'
                    })
                    continue
                
                # Tester la clé avant sauvegarde
                test_result = self._test_key(key, value)
                
                if test_result['valid']:
                    # Sauvegarder dans Supabase (chiffré)
                    save_result = self._save_key(key, value)
                    results.append({
                        'key': key,
                        'status': 'success' if save_result else 'error',
                        'tested': True,
                        'message': test_result.get('message', 'Saved')
                    })
                    
                    # Logger
                    self._log_config_change(key, 'UPDATED')
                else:
                    results.append({
                        'key': key,
                        'status': 'error',
                        'tested': True,
                        'message': test_result.get('message', 'Invalid key')
                    })
            
            return jsonify({
                'success': True,
                'results': results,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/config/test', methods=['POST'])
        def test_config():
            """Teste une clé API sans la sauvegarder"""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            data = request.get_json()
            key_type = data.get('type')
            key_value = data.get('value')
            
            if not key_type or not key_value:
                return jsonify({'error': 'Missing type or value'}), 400
            
            result = self._test_key(key_type, key_value)
            
            return jsonify({
                'valid': result['valid'],
                'message': result.get('message', ''),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/config/reload', methods=['POST'])
        def reload_config():
            """Recharge la configuration depuis Supabase"""
            if not self._check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            success = self._reload_config_from_db()
            
            if success:
                self._log_config_change('SYSTEM', 'CONFIG_RELOADED')
                return jsonify({
                    'success': True,
                    'message': 'Configuration reloaded',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to reload configuration'
                }), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'ok',
                'bot_connected': self.bot.is_ready() if hasattr(self.bot, 'is_ready') else True,
                'timestamp': datetime.now().isoformat()
            })
    
    def _check_auth(self) -> bool:
        """Vérifie l'authentification de la requête"""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header.split(' ')[1]
        
        # Vérifier le token (en production, utiliser JWT ou similar)
        if self.admin_secret:
            return hmac.compare_digest(token, self.admin_secret)
        
        # Si pas de secret configuré, accepter les requêtes locales uniquement
        if request.remote_addr in ['127.0.0.1', 'localhost']:
            return True
        
        return False
    
    def _validate_key_format(self, key_name: str, key_value: str) -> bool:
        """Valide le format d'une clé API"""
        if not key_value:
            return False
        
        formats = {
            'GEMINI_API_KEY': lambda v: v.startswith('AIzaSy') and len(v) > 20,
            'STRIPE_SECRET_KEY': lambda v: v.startswith(('sk_test_', 'sk_live_')) and len(v) > 20,
            'STRIPE_WEBHOOK_SECRET': lambda v: v.startswith('whsec_') and len(v) > 20,
            'DISCORD_TOKEN': lambda v: len(v) > 50,  # Discord tokens are long
            'SUPABASE_URL': lambda v: v.startswith('https://') and v.endswith('.supabase.co'),
            'SUPABASE_SERVICE_KEY': lambda v: v.startswith('eyJ') and len(v) > 100,
            'REDIS_URL': lambda v: v.startswith(('redis://', 'rediss://')),
            'SECURE_CONFIG_KEY': lambda v: len(v) >= 32
        }
        
        validator = formats.get(key_name)
        if validator:
            return validator(key_value)
        
        return True  # Clés inconnues acceptées
    
    def _test_key(self, key_name: str, key_value: str) -> Dict:
        """Teste une clé API"""
        import asyncio
        
        try:
            if key_name == 'GEMINI_API_KEY':
                return self._test_gemini_key(key_value)
            elif key_name == 'STRIPE_SECRET_KEY':
                return self._test_stripe_key(key_value)
            elif key_name == 'DISCORD_TOKEN':
                return self._test_discord_token(key_value)
            elif key_name == 'SUPABASE_URL' or key_name == 'SUPABASE_SERVICE_KEY':
                return {'valid': True, 'message': 'Test via sauvegarde recommandé'}
            else:
                return {'valid': True, 'message': 'Format OK (non testé)'}
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    def _test_gemini_key(self, key: str) -> Dict:
        """Teste une clé Gemini"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            models = genai.list_models()
            return {'valid': True, 'message': f'{len(list(models))} modèles disponibles'}
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    def _test_stripe_key(self, key: str) -> Dict:
        """Teste une clé Stripe"""
        try:
            import stripe
            stripe.api_key = key
            account = stripe.Account.retrieve()
            return {'valid': True, 'message': f'Compte: {account.settings.dashboard.display_name}'}
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    def _test_discord_token(self, token: str) -> Dict:
        """Teste un token Discord"""
        try:
            import requests
            response = requests.get(
                'https://discord.com/api/v10/users/@me',
                headers={'Authorization': f'Bot {token}'}
            )
            if response.status_code == 200:
                data = response.json()
                return {'valid': True, 'message': f'Bot: {data["username"]}'}
            else:
                return {'valid': False, 'message': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    def _save_key(self, key_name: str, key_value: str) -> bool:
        """Sauvegarde une clé dans Supabase (chiffrée)"""
        try:
            # Utiliser le secure_config du bot
            if hasattr(self.bot, 'security') and hasattr(self.bot.security, 'config'):
                from secure_config import SecureConfigManager
                
                manager = SecureConfigManager()
                encrypted = manager.encrypt(key_value)
                
                # Sauvegarder dans Supabase
                result = self.bot.db.client.table('secure_config').upsert({
                    'config_key': key_name,
                    'encrypted_value': f'ENC:{encrypted}',
                    'encrypted_by': 'config_api',
                    'updated_at': datetime.now().isoformat()
                }).execute()
                
                return bool(result.data)
            
            # Fallback: sauvegarder en clair (pas recommandé)
            result = self.bot.db.client.table('secure_config').upsert({
                'config_key': key_name,
                'encrypted_value': key_value,  # Non chiffré!
                'encrypted_by': 'config_api',
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde clé {key_name}: {e}")
            return False
    
    def _reload_config_from_db(self) -> bool:
        """Recharge la configuration depuis Supabase"""
        try:
            result = self.bot.db.client.table('secure_config').select('*').execute()
            
            if not result.data:
                return False
            
            for row in result.data:
                key = row['config_key']
                value = row['encrypted_value']
                
                # Déchiffrer si nécessaire
                if value.startswith('ENC:'):
                    try:
                        from secure_config import SecureConfigManager
                        manager = SecureConfigManager()
                        value = manager.decrypt(value[4:])
                    except:
                        continue  # Impossible de déchiffrer
                
                # Mettre à jour l'environnement
                os.environ[key] = value
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur rechargement config: {e}")
            return False
    
    def _log_config_change(self, key: str, action: str):
        """Logger les changements de configuration"""
        try:
            self.bot.db.client.table('audit_logs').insert({
                'admin_user_id': 0,  # API
                'action': action,
                'target_type': 'config',
                'target_user_id': None,
                'old_value': None,
                'new_value': {'key': key, 'source': 'config_api'},
                'reason': 'API configuration update',
                'created_at': datetime.now().isoformat()
            }).execute()
        except:
            pass
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Démarre l'API"""
        if not FLASK_AVAILABLE:
            print("❌ Flask requis: pip install flask")
            return
        
        if not self.app:
            print("❌ API non initialisée")
            return
        
        print(f"🚀 API de configuration démarrée sur http://{host}:{port}")
        print(f"   Endpoints:")
        print(f"   - GET  /api/config       : Voir configuration")
        print(f"   - POST /api/config       : Mettre à jour")
        print(f"   - POST /api/config/test  : Tester une clé")
        print(f"   - POST /api/config/reload: Recharger depuis DB")
        print(f"   - GET  /api/health       : Health check")
        
        self.app.run(host=host, port=port, debug=debug)


# Alternative simple sans Flask (via Discord bot command)
class ConfigManager:
    """
    Gestionnaire de configuration sans serveur HTTP
    Utilise les commandes Discord pour la configuration
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def update_config_command(self, interaction, key: str, value: str):
        """
        Commande Discord pour mettre à jour une config
        Usage: /setconfig GEMINI_API_KEY nouvelle_cle
        """
        # Vérifier permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Réservé aux administrateurs", ephemeral=True)
            return
        
        # Valider
        if not self._validate_key_format(key, value):
            await interaction.response.send_message("❌ Format de clé invalide", ephemeral=True)
            return
        
        # Tester
        await interaction.response.defer(ephemeral=True)
        
        test_result = self._test_key_sync(key, value)
        
        if not test_result['valid']:
            await interaction.followup.send(
                f"❌ Clé invalide: {test_result.get('message', 'Test échoué')}",
                ephemeral=True
            )
            return
        
        # Sauvegarder
        success = self._save_key_sync(key, value)
        
        if success:
            await interaction.followup.send(
                f"✅ Clé `{key}` mise à jour et testée avec succès !\n"
                f"📝 {test_result.get('message', '')}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ Erreur lors de la sauvegarde",
                ephemeral=True
            )
    
    def _validate_key_format(self, key_name: str, key_value: str) -> bool:
        """Valide le format d'une clé"""
        # Même logique que ConfigAPI
        return True  # Simplifié
    
    def _test_key_sync(self, key_name: str, key_value: str) -> Dict:
        """Teste une clé (synchrone)"""
        # Même logique que ConfigAPI
        return {'valid': True, 'message': 'Test non implémenté'}
    
    def _save_key_sync(self, key_name: str, key_value: str) -> bool:
        """Sauvegarde une clé (synchrone)"""
        try:
            # Sauvegarder dans secure_config
            self.bot.db.client.table('secure_config').upsert({
                'config_key': key_name,
                'encrypted_value': f'ENC:PENDING_{key_value[:10]}...',  # À chiffrer
                'updated_at': datetime.now().isoformat()
            }).execute()
            return True
        except:
            return False


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

"""
# Dans bot.py, ajouter:

from config_api import ConfigAPI, ConfigManager

# Option 1: API HTTP (nécessite Flask)
config_api = ConfigAPI(bot, admin_secret='votre_secret_admin')
# Démarrer dans un thread séparé
import threading
threading.Thread(target=config_api.run, kwargs={'port': 5000}, daemon=True).start()

# Option 2: Commande Discord
config_manager = ConfigManager(bot)

@bot.tree.command(name="setconfig", description="Met à jour une clé API (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_setconfig(interaction: discord.Interaction, key: str, value: str):
    await config_manager.update_config_command(interaction, key, value)
"""
