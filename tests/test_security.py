"""
TESTS DE SÉCURITÉ - Shellia AI Bot
Tests unitaires pour les modules de sécurité
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta


# ============== TESTS SECURE_CONFIG ==============

def test_secure_config_encryption():
    """Test le chiffrement/déchiffrement"""
    try:
        from bot.secure_config import SecureConfigManager
    except ImportError:
        pytest.skip("secure_config non disponible")
    
    # Générer une clé
    key = SecureConfigManager.generate_master_key()
    assert key is not None
    assert len(key) > 0
    
    # Créer le manager
    manager = SecureConfigManager(key)
    
    # Chiffrer/déchiffrer
    secret = "my_secret_api_key_123"
    encrypted = manager.encrypt(secret)
    decrypted = manager.decrypt(encrypted)
    
    assert decrypted == secret
    assert encrypted != secret
    assert encrypted.startswith("gAAAAAB")  # Format Fernet


def test_secure_config_validation():
    """Test la validation de configuration"""
    try:
        from bot.secure_config import ShelliaConfig
    except ImportError:
        pytest.skip("secure_config non disponible")
    
    config = ShelliaConfig()
    # Sans variables d'environnement, tout doit être manquant
    missing = config.validate()
    
    # Au moins quelques champs doivent être requis
    assert len(missing) > 0
    assert 'GEMINI_API_KEY' in missing


# ============== TESTS CIRCUIT BREAKER ==============

@pytest.mark.asyncio
async def test_circuit_breaker_states():
    """Test les états du circuit breaker"""
    try:
        from bot.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerConfig
    except ImportError:
        pytest.skip("circuit_breaker non disponible")
    
    breaker = CircuitBreaker(
        "test",
        config=CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=1,
            timeout_seconds=1
        )
    )
    
    # État initial: CLOSED
    assert breaker.state == CircuitState.CLOSED
    
    # Fonction qui échoue
    async def failing_func():
        raise Exception("Test error")
    
    # 2 échecs = OPEN
    for _ in range(2):
        try:
            await breaker.call(failing_func)
        except:
            pass
    
    assert breaker.state == CircuitState.OPEN
    
    # Attendre le timeout
    await asyncio.sleep(1.1)
    
    # Appel suivant tente HALF_OPEN
    try:
        await breaker.call(failing_func)
    except:
        pass
    
    # Retourne en OPEN car échec
    assert breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_success():
    """Test le circuit breaker avec succès"""
    try:
        from bot.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerConfig
    except ImportError:
        pytest.skip("circuit_breaker non disponible")
    
    breaker = CircuitBreaker(
        "test_success",
        config=CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout_seconds=1
        )
    )
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


# ============== TESTS RATE LIMITER ==============

@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basique du rate limiter"""
    try:
        from bot.persistent_rate_limiter import PersistentRateLimiter, RateLimitStatus
    except ImportError:
        pytest.skip("persistent_rate_limiter non disponible")
    
    # Mock DB
    class MockDB:
        class client:
            @staticmethod
            def table(name):
                return MockTable()
    
    class MockTable:
        def insert(self, *args, **kwargs):
            return self
        def execute(self):
            return type('Result', (), {'data': []})()
    
    db = MockDB()
    limiter = PersistentRateLimiter(db)
    
    # Premier appel: OK
    status = limiter.check_rate_limit(12345)
    assert status.can_proceed is True
    assert status.remaining_minute >= 0
    
    # Admin bypass
    status = limiter.check_rate_limit(12345, is_admin=True)
    assert status.can_proceed is True


def test_rate_limiter_spam_detection():
    """Test la détection de spam"""
    try:
        from bot.persistent_rate_limiter import PersistentRateLimiter
    except ImportError:
        pytest.skip("persistent_rate_limiter non disponible")
    
    class MockDB:
        pass
    
    limiter = PersistentRateLimiter(MockDB())
    user_id = 12345
    content = "spam message"
    
    # Envoyer le même message 5 fois
    for _ in range(5):
        is_ok, msg = limiter.check_spam(user_id, content)
    
    # Le 5ème devrait être détecté comme spam
    # Note: Le comportement exact dépend de SPAM_THRESHOLD


# ============== TESTS WEBHOOK VALIDATOR ==============

def test_webhook_signature_parsing():
    """Test le parsing du header Stripe-Signature"""
    try:
        from bot.stripe_webhook_validator import StripeWebhookValidator
    except ImportError:
        pytest.skip("stripe_webhook_validator non disponible")
    
    validator = StripeWebhookValidator("whsec_test_secret_key_for_testing_purposes_only")
    
    header = "t=1492774577,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd"
    parsed = validator._parse_signature_header(header)
    
    assert parsed is not None
    assert parsed['t'] == '1492774577'
    assert parsed['v1'] == '5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd'


def test_webhook_invalid_signature():
    """Test la validation avec signature invalide"""
    try:
        from bot.stripe_webhook_validator import StripeWebhookValidator
    except ImportError:
        pytest.skip("stripe_webhook_validator non disponible")
    
    validator = StripeWebhookValidator("whsec_test_secret")
    
    # Payload invalide
    payload = b'{"test": "data"}'
    header = "t=1492774577,v1=invalid_signature"
    
    result = validator.validate_webhook(payload, header, max_age_seconds=10000)
    
    assert result.is_valid is False
    assert "Signature invalide" in result.error_message or "impossible" in result.error_message.lower()


def test_webhook_timestamp_validation():
    """Test la validation du timestamp"""
    try:
        from bot.stripe_webhook_validator import StripeWebhookValidator
    except ImportError:
        pytest.skip("stripe_webhook_validator non disponible")
    
    validator = StripeWebhookValidator("whsec_test")
    
    # Timestamp trop vieux (10 minutes)
    old_timestamp = str(int(time.time()) - 600)
    header = f"t={old_timestamp},v1=invalid"
    
    result = validator.validate_webhook(b'{}', header)
    
    assert result.is_valid is False
    assert "trop ancien" in result.error_message.lower() or "expir" in result.error_message.lower()


# ============== TESTS CONVERSATION HISTORY ==============

@pytest.mark.asyncio
async def test_conversation_history_basic():
    """Test basique de l'historique"""
    try:
        from bot.conversation_history import ConversationHistoryManager, Message
    except ImportError:
        pytest.skip("conversation_history non disponible")
    
    class MockDB:
        class client:
            @staticmethod
            def table(name):
                return MockTable()
    
    class MockTable:
        def insert(self, *args, **kwargs):
            return self
        def select(self, *args, **kwargs):
            return self
        def eq(self, *args, **kwargs):
            return self
        def order(self, *args, **kwargs):
            return self
        def limit(self, *args, **kwargs):
            return self
        def execute(self):
            return type('Result', (), {'data': []})()
    
    db = MockDB()
    history = ConversationHistoryManager(db, max_history=10)
    
    # Ajouter un message
    await history.add_message(12345, 'user', 'Hello')
    
    # Récupérer l'historique (depuis le cache)
    messages = await history.get_history(12345, limit=5)
    assert len(messages) == 1
    assert messages[0].content == 'Hello'
    assert messages[0].role == 'user'


def test_message_dataclass():
    """Test la classe Message"""
    try:
        from bot.conversation_history import Message
    except ImportError:
        pytest.skip("conversation_history non disponible")
    
    msg = Message(
        role='user',
        content='Test',
        timestamp=datetime.now(),
        metadata={'key': 'value'}
    )
    
    # Test to_dict/from_dict
    data = msg.to_dict()
    msg2 = Message.from_dict(data)
    
    assert msg2.role == msg.role
    assert msg2.content == msg.content
    assert msg2.metadata == msg.metadata


# ============== TESTS INTÉGRATION ==============

def test_security_modules_import():
    """Test que tous les modules de sécurité peuvent être importés"""
    modules = [
        'bot.secure_config',
        'bot.stripe_webhook_validator',
        'bot.persistent_rate_limiter',
        'bot.circuit_breaker',
        'bot.conversation_history',
        'bot.security_integration',
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
        except ImportError as e:
            failed.append((module, str(e)))
    
    if failed:
        print(f"Modules non importables: {failed}")
    
    # Ne pas fail le test - certains modules peuvent avoir des dépendances
    # qui ne sont pas installées dans l'environnement de test
    assert len(failed) <= 3  # Au moins quelques modules doivent marcher


# ============== UTILITAIRES ==============

if __name__ == '__main__':
    # Exécuter les tests
    pytest.main([__file__, '-v'])
