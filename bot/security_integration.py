"""
INTÉGRATION SÉCURITÉ - Shellia AI Bot
Intègre tous les modules de sécurité dans le bot existant
"""

import os
import asyncio
from typing import Optional

# Imports des nouveaux modules de sécurité
try:
    from secure_config import ShelliaConfig, SecureConfigManager
    SECURE_CONFIG_AVAILABLE = True
except ImportError:
    SECURE_CONFIG_AVAILABLE = False

try:
    from persistent_rate_limiter import PersistentRateLimiter, RateLimitStatus
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

try:
    from stripe_webhook_validator import StripeWebhookValidator, StripeEventHandler
    WEBHOOK_VALIDATOR_AVAILABLE = True
except ImportError:
    WEBHOOK_VALIDATOR_AVAILABLE = False

try:
    from circuit_breaker import CircuitBreakerRegistry, CircuitBreakerConfig, CircuitBreakerOpenError
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

try:
    from conversation_history import ConversationHistoryManager
    CONVERSATION_HISTORY_AVAILABLE = True
except ImportError:
    CONVERSATION_HISTORY_AVAILABLE = False


class SecurityIntegration:
    """
    Intègre tous les modules de sécurité dans une interface unifiée
    """
    
    def __init__(self, db):
        self.db = db
        self.config: Optional[ShelliaConfig] = None
        self.rate_limiter: Optional[PersistentRateLimiter] = None
        self.webhook_handler: Optional[StripeEventHandler] = None
        self.conversation_history: Optional[ConversationHistoryManager] = None
        self.gemini_breaker = None
        
        self._initialized = False
    
    async def initialize(self, redis_client=None):
        """
        Initialise tous les composants de sécurité
        """
        if self._initialized:
            return
        
        print("🔒 Initialisation des composants de sécurité...")
        
        # 1. Configuration sécurisée
        self._init_config()
        
        # 2. Rate limiter persistant
        self._init_rate_limiter(redis_client)
        
        # 3. Webhook handler
        self._init_webhook_handler()
        
        # 4. Circuit breaker pour Gemini
        self._init_circuit_breaker()
        
        # 5. Historique de conversation
        self._init_conversation_history()
        
        self._initialized = True
        print("✅ Tous les composants de sécurité sont initialisés")
    
    def _init_config(self):
        """Initialise la configuration sécurisée"""
        if SECURE_CONFIG_AVAILABLE:
            try:
                encrypted = os.getenv('SECURE_CONFIG_KEY') is not None
                self.config = ShelliaConfig.from_env(encrypted=encrypted)
                
                missing = self.config.validate()
                if missing:
                    print(f"⚠️  Secrets manquants: {', '.join(missing)}")
                else:
                    print("✅ Configuration sécurisée chargée")
            except Exception as e:
                print(f"⚠️  Erreur config sécurisée: {e}")
                self.config = None
        else:
            print("⚠️  Module secure_config non disponible")
    
    def _init_rate_limiter(self, redis_client):
        """Initialise le rate limiter"""
        if RATE_LIMITER_AVAILABLE:
            try:
                self.rate_limiter = PersistentRateLimiter(self.db, redis_client)
                backend = "Redis" if redis_client else "Supabase"
                print(f"✅ Rate limiter initialisé ({backend})")
            except Exception as e:
                print(f"⚠️  Erreur rate limiter: {e}")
        else:
            print("⚠️  Module persistent_rate_limiter non disponible")
    
    def _init_webhook_handler(self):
        """Initialise le gestionnaire de webhooks"""
        if WEBHOOK_VALIDATOR_AVAILABLE and self.config:
            try:
                secret = self.config.stripe_webhook_secret
                if secret:
                    validator = StripeWebhookValidator(secret)
                    self.webhook_handler = StripeEventHandler(self.db, validator)
                    print("✅ Webhook handler initialisé")
                else:
                    print("⚠️  STRIPE_WEBHOOK_SECRET non configuré")
            except Exception as e:
                print(f"⚠️  Erreur webhook handler: {e}")
        else:
            print("⚠️  Module webhook_validator non disponible ou config manquante")
    
    def _init_circuit_breaker(self):
        """Initialise le circuit breaker pour Gemini"""
        if CIRCUIT_BREAKER_AVAILABLE:
            try:
                self.gemini_breaker = CircuitBreakerRegistry.get_or_create(
                    "gemini_api",
                    config=CircuitBreakerConfig(
                        failure_threshold=3,
                        success_threshold=2,
                        timeout_seconds=60,
                        max_retries=2,
                        base_delay=2.0,
                        call_timeout=30.0
                    ),
                    on_state_change=self._on_circuit_state_change
                )
                print("✅ Circuit breaker Gemini initialisé")
            except Exception as e:
                print(f"⚠️  Erreur circuit breaker: {e}")
        else:
            print("⚠️  Module circuit_breaker non disponible")
    
    def _init_conversation_history(self):
        """Initialise l'historique de conversation"""
        if CONVERSATION_HISTORY_AVAILABLE:
            try:
                self.conversation_history = ConversationHistoryManager(
                    self.db,
                    max_history=50,
                    compression_threshold=10
                )
                print("✅ Gestionnaire d'historique initialisé")
            except Exception as e:
                print(f"⚠️  Erreur conversation history: {e}")
        else:
            print("⚠️  Module conversation_history non disponible")
    
    def _on_circuit_state_change(self, name, old_state, new_state):
        """Callback pour changement d'état du circuit"""
        print(f"🔄 Circuit '{name}': {old_state.value} -> {new_state.value}")
        
        # Logger dans la base
        if self.db:
            try:
                self.db.client.table('circuit_breaker_state').upsert({
                    'circuit_name': name,
                    'state': new_state.value,
                    'opened_at': 'NOW()' if new_state.name == 'OPEN' else None
                }).execute()
            except:
                pass
    
    # ============ MÉTHODES PUBLIQUES ============
    
    async def check_rate_limit(self, user_id: int, is_admin: bool = False) -> tuple:
        """
        Vérifie le rate limit pour un utilisateur
        
        Returns:
            (can_proceed: bool, message: str)
        """
        if not self.rate_limiter:
            # Fallback: pas de rate limiting
            return True, None
        
        status = self.rate_limiter.check_rate_limit(user_id, is_admin)
        
        if not status.can_proceed:
            if status.cooldown_remaining > 0:
                msg = f"⏱️ Attendez {status.cooldown_remaining:.1f}s entre chaque message"
            else:
                msg = f"🚫 {status.reason}"
            return False, msg
        
        return True, None
    
    async def check_spam(self, user_id: int, content: str) -> tuple:
        """
        Vérifie si le contenu est du spam
        
        Returns:
            (is_ok: bool, message: str)
        """
        if not self.rate_limiter:
            return True, None
        
        return self.rate_limiter.check_spam(user_id, content)
    
    async def process_stripe_webhook(self, payload: bytes, signature: str) -> tuple:
        """
        Traite un webhook Stripe
        
        Returns:
            (success: bool, message: str)
        """
        if not self.webhook_handler:
            return False, "Webhook handler non initialisé"
        
        return self.webhook_handler.process_webhook(payload, signature)
    
    async def call_with_circuit_breaker(self, func, *args, **kwargs):
        """
        Appelle une fonction protégée par circuit breaker
        """
        if not self.gemini_breaker:
            # Fallback: appel direct
            return await func(*args, **kwargs)
        
        try:
            return await self.gemini_breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            return None
    
    async def add_to_history(self, user_id: int, role: str, content: str):
        """Ajoute un message à l'historique"""
        if self.conversation_history:
            await self.conversation_history.add_message(user_id, role, content)
    
    async def get_conversation_context(self, user_id: int):
        """Récupère le contexte de conversation pour Gemini"""
        if self.conversation_history:
            return await self.conversation_history.get_conversation_context(user_id)
        return []
    
    def get_stats(self) -> dict:
        """Récupère les statistiques de sécurité"""
        stats = {
            'secure_config': self.config is not None,
            'rate_limiter': self.rate_limiter is not None,
            'webhook_handler': self.webhook_handler is not None,
            'circuit_breaker': self.gemini_breaker is not None,
            'conversation_history': self.conversation_history is not None,
        }
        
        if self.gemini_breaker:
            stats['circuit_stats'] = self.gemini_breaker.get_stats()
        
        return stats


# ============ INTÉGRATION AVEC BOT.PY ============
"""
Exemple d'intégration dans la classe ShelliaBot:

class ShelliaBot(commands.Bot):
    def __init__(self):
        super().__init__(...)
        self.db = SupabaseDB()
        self.security = SecurityIntegration(self.db)
        
    async def setup_hook(self):
        # Initialiser la sécurité
        await self.security.initialize()
        
        # Utiliser les méthodes de sécurité
        self.ai = AIManager(
            api_key=self.security.config.gemini_api_key if self.security.config else None,
            db=self.db,
            security=self.security
        )
    
    async def handle_ai_message(self, message):
        user_id = message.author.id
        
        # 1. Rate limiting
        can_proceed, error = await self.security.check_rate_limit(user_id)
        if not can_proceed:
            return await message.reply(error)
        
        # 2. Anti-spam
        is_ok, spam_msg = await self.security.check_spam(user_id, message.content)
        if not is_ok:
            return await message.reply(spam_msg)
        
        # 3. Générer réponse avec circuit breaker
        response = await self.security.call_with_circuit_breaker(
            self.ai.generate_response,
            message.content,
            user_id
        )
        
        if response is None:
            return await message.reply(
                "Le service IA est temporairement indisponible. Réessayez plus tard. 🔄"
            )
        
        # 4. Sauvegarder dans l'historique
        await self.security.add_to_history(user_id, 'user', message.content)
        await self.security.add_to_history(user_id, 'model', response)
        
        # Envoyer réponse
        await message.reply(response)
"""


# ============ UTILITAIRES DE MIGRATION ============

async def migrate_to_secure_config():
    """
    Migre les secrets non chiffrés vers le format chiffré
    """
    if not SECURE_CONFIG_AVAILABLE:
        print("❌ Module secure_config non disponible")
        return
    
    # Vérifier si déjà chiffré
    if os.getenv('GEMINI_API_KEY', '').startswith('ENC:'):
        print("✅ Les secrets semblent déjà chiffrés")
        return
    
    print("\n🔐 Migration vers configuration sécurisée")
    print("=" * 50)
    
    # Générer clé
    master_key = SecureConfigManager.generate_master_key()
    print(f"\n1. Clé maître générée: {master_key}")
    print("   ⚠️  CONSERVEZ CETTE CLÉ DANS UN ENDROIT SÛR!")
    
    # Créer manager
    os.environ['SECURE_CONFIG_KEY'] = master_key
    manager = SecureConfigManager()
    
    # Lister les secrets à chiffrer
    secrets_to_encrypt = [
        'GEMINI_API_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'DISCORD_TOKEN',
        'SUPABASE_SERVICE_KEY',
    ]
    
    print("\n2. Secrets à chiffrer:")
    for key in secrets_to_encrypt:
        value = os.getenv(key)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"   - {key}: {masked}")
    
    print("\n3. Commandes pour appliquer:")
    print(f"   export SECURE_CONFIG_KEY='{master_key}'")
    print("   python secure_config.py encrypt --env-file .env")
    print("   mv .env.encrypted .env")


async def run_security_check():
    """Exécute une vérification de sécurité"""
    print("\n🔍 Vérification de sécurité")
    print("=" * 50)
    
    checks = []
    
    # 1. Vérifier chiffrement
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    if gemini_key.startswith('ENC:'):
        checks.append(("✅", "Clés API chiffrées"))
    else:
        checks.append(("❌", "Clés API en CLAIR - URGENT!"))
    
    # 2. Vérifier webhook secret
    if os.getenv('STRIPE_WEBHOOK_SECRET'):
        checks.append(("✅", "Webhook Stripe configuré"))
    else:
        checks.append(("❌", "Webhook Stripe NON configuré"))
    
    # 3. Vérifier modules
    if RATE_LIMITER_AVAILABLE:
        checks.append(("✅", "Rate limiter disponible"))
    else:
        checks.append(("⚠️ ", "Rate limiter non disponible"))
    
    if CIRCUIT_BREAKER_AVAILABLE:
        checks.append(("✅", "Circuit breaker disponible"))
    else:
        checks.append(("⚠️ ", "Circuit breaker non disponible"))
    
    if CONVERSATION_HISTORY_AVAILABLE:
        checks.append(("✅", "Historique persistant disponible"))
    else:
        checks.append(("⚠️ ", "Historique persistant non disponible"))
    
    for status, msg in checks:
        print(f"   {status} {msg}")
    
    # Résumé
    critical = sum(1 for s, _ in checks if s == "❌")
    if critical > 0:
        print(f"\n❌ {critical} problèmes CRITIQUES détectés!")
    else:
        print("\n✅ Aucun problème critique détecté")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'migrate':
            asyncio.run(migrate_to_secure_config())
        elif command == 'check':
            asyncio.run(run_security_check())
        else:
            print(f"Commande inconnue: {command}")
            print("Usage: python security_integration.py [migrate|check]")
    else:
        print("Security Integration Module")
        print("Usage: python security_integration.py [migrate|check]")
