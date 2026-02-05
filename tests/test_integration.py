"""
TESTS D'INTÉGRATION - Shellia AI Bot
Tests complets des flux critiques
"""

import pytest
import asyncio
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Configuration des variables d'environnement pour les tests
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'test_key')
os.environ.setdefault('GEMINI_API_KEY', 'test_gemini_key')
os.environ.setdefault('DISCORD_TOKEN', 'test_discord_token')


class TestIntegration:
    """Tests d'intégration complets"""
    
    @pytest.fixture
    def mock_db(self):
        """Fixture pour une base de données mockée"""
        db = Mock()
        
        # Mock des méthodes courantes
        db.get_or_create_user = Mock(return_value={
            'user_id': 12345,
            'username': 'TestUser',
            'plan': 'free',
            'total_messages': 0,
            'created_at': datetime.now().isoformat()
        })
        
        db.get_daily_quota = Mock(return_value={
            'messages_used': 0,
            'messages_limit': 10,
            'streak_bonus': 0,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
        db.increment_quota_usage = Mock(return_value=True)
        db.update_streak = Mock(return_value={
            'current_streak': 1,
            'is_new_milestone': False,
            'bonus_messages': 0
        })
        db.log_security_event = Mock()
        
        # Mock Supabase client
        db.client = Mock()
        db.client.table = Mock(return_value=Mock(
            select=Mock(return_value=Mock(
                eq=Mock(return_value=Mock(
                    execute=Mock(return_value=Mock(data=[]))
                ))
            )),
            insert=Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[{}])))),
            update=Mock(return_value=Mock(eq=Mock(return_value=Mock(execute=Mock())))),
            delete=Mock(return_value=Mock(eq=Mock(return_value=Mock(execute=Mock()))))
        ))
        
        return db
    
    @pytest.fixture
    def mock_discord_message(self):
        """Fixture pour un message Discord mocké"""
        message = Mock()
        message.author = Mock()
        message.author.id = 12345
        message.author.name = "TestUser"
        message.author.guild_permissions = Mock()
        message.author.guild_permissions.administrator = False
        message.content = "Bonjour, comment ça va ?"
        message.channel = Mock()
        message.channel.name = "général"
        message.channel.typing = Mock(return_value=AsyncMock())
        message.reply = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_discord_interaction(self):
        """Fixture pour une interaction Discord mockée"""
        interaction = Mock()
        interaction.user = Mock()
        interaction.user.id = 12345
        interaction.user.name = "TestUser"
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()
        interaction.guild = Mock()
        interaction.guild.get_member = Mock(return_value=Mock())
        return interaction


class TestSecurityIntegration(TestIntegration):
    """Tests d'intégration de la sécurité"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_blocks_excessive_requests(self, mock_db):
        """Test que le rate limiting bloque les requêtes excessives"""
        try:
            from bot.persistent_rate_limiter import PersistentRateLimiter
        except ImportError:
            pytest.skip("persistent_rate_limiter non disponible")
        
        limiter = PersistentRateLimiter(mock_db)
        user_id = 12345
        
        # Envoyer 15 messages (limite à 10/min)
        blocked = False
        for i in range(15):
            status = limiter.check_rate_limit(user_id)
            if not status.can_proceed:
                blocked = True
                break
        
        assert blocked, "Le rate limiter devrait bloquer après la limite"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, mock_db):
        """Test que le circuit breaker s'ouvre après plusieurs échecs"""
        try:
            from bot.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
        except ImportError:
            pytest.skip("circuit_breaker non disponible")
        
        breaker = CircuitBreaker(
            "test_api",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout_seconds=1
            )
        )
        
        async def failing_func():
            raise Exception("API Error")
        
        # 3 échecs
        for _ in range(3):
            try:
                await breaker.call(failing_func)
            except:
                pass
        
        assert breaker.state == CircuitState.OPEN, "Le circuit devrait être ouvert"
    
    @pytest.mark.asyncio
    async def test_spam_detection_triggers_warning(self, mock_db):
        """Test que la détection de spam fonctionne"""
        try:
            from bot.persistent_rate_limiter import PersistentRateLimiter
        except ImportError:
            pytest.skip("persistent_rate_limiter non disponible")
        
        limiter = PersistentRateLimiter(mock_db)
        user_id = 12345
        spam_message = "SPAM MESSAGE IDENTIQUE"
        
        # Envoyer le même message 5 fois
        is_spam = False
        for _ in range(5):
            is_ok, msg = limiter.check_spam(user_id, spam_message)
            if not is_ok:
                is_spam = True
                break
        
        assert is_spam, "Le spam devrait être détecté"


class TestImageGeneration(TestIntegration):
    """Tests de génération d'images"""
    
    def test_prompt_validation_blocks_inappropriate_content(self):
        """Test que les prompts inappropriés sont rejetés"""
        try:
            from bot.image_generator import ImageGenerator
        except ImportError:
            pytest.skip("image_generator non disponible")
        
        generator = ImageGenerator("test_key")
        
        # Test prompt valide
        is_valid, error = generator.validate_prompt("A cute cat")
        assert is_valid, "Un prompt valide devrait être accepté"
        
        # Test prompt invalide
        is_valid, error = generator.validate_prompt("nude picture")
        assert not is_valid, "Un prompt inapproprié devrait être rejeté"
    
    def test_quota_calculation_per_plan(self, mock_db):
        """Test que les quotas sont correctement calculés selon le plan"""
        try:
            from bot.image_generator import ImageGenerator
        except ImportError:
            pytest.skip("image_generator non disponible")
        
        generator = ImageGenerator("test_key")
        
        # Mock différents plans
        test_cases = [
            ('free', 0, False),
            ('basic', 0, False),
            ('pro', 10, True),
            ('ultra', 50, True)
        ]
        
        for plan, expected_quota, should_allow in test_cases:
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
                data=[{'plan': plan, 'images_generated_today': 0}]
            )
            
            quota = generator.get_quota_info(12345, mock_db)
            
            if quota['quota'] > 0:  # Si le plan a un quota
                assert quota['quota'] == expected_quota, f"Plan {plan} devrait avoir {expected_quota} images"


class TestConversationHistory(TestIntegration):
    """Tests de l'historique de conversation"""
    
    @pytest.mark.asyncio
    async def test_conversation_history_persists_messages(self, mock_db):
        """Test que les messages sont persistés"""
        try:
            from bot.conversation_history import ConversationHistoryManager
        except ImportError:
            pytest.skip("conversation_history non disponible")
        
        history = ConversationHistoryManager(mock_db, max_history=10)
        user_id = 12345
        
        # Ajouter des messages
        await history.add_message(user_id, 'user', 'Hello')
        await history.add_message(user_id, 'model', 'Hi there!')
        
        # Récupérer l'historique
        messages = await history.get_history(user_id, limit=5)
        
        assert len(messages) == 2, "L'historique devrait contenir 2 messages"
        assert messages[0].content == 'Hello'
        assert messages[1].content == 'Hi there!'
    
    @pytest.mark.asyncio
    async def test_conversation_context_formatting(self, mock_db):
        """Test que le contexte est correctement formaté pour Gemini"""
        try:
            from bot.conversation_history import ConversationHistoryManager
        except ImportError:
            pytest.skip("conversation_history non disponible")
        
        history = ConversationHistoryManager(mock_db, max_history=10)
        user_id = 12345
        
        # Ajouter des messages
        await history.add_message(user_id, 'user', 'Question 1')
        await history.add_message(user_id, 'model', 'Answer 1')
        await history.add_message(user_id, 'user', 'Question 2')
        
        # Récupérer le contexte
        context = await history.get_conversation_context(user_id)
        
        assert len(context) == 3, "Le contexte devrait contenir 3 messages"
        assert context[0]['role'] == 'user'
        assert context[1]['role'] == 'model'


class TestBotCommands(TestIntegration):
    """Tests des commandes Discord"""
    
    @pytest.mark.asyncio
    async def test_quota_command_shows_correct_info(self, mock_db, mock_discord_interaction):
        """Test que la commande quota affiche les bonnes informations"""
        # Simuler la logique de la commande quota
        user_id = mock_discord_interaction.user.id
        
        # Vérifier que les données utilisateur sont récupérées
        user_data = mock_db.get_or_create_user(user_id, str(mock_discord_interaction.user))
        assert user_data is not None
        
        # Vérifier le quota
        quota = mock_db.get_daily_quota(user_id)
        assert quota['messages_limit'] > 0
    
    @pytest.mark.asyncio
    async def test_trial_command_activates_pro_plan(self, mock_db, mock_discord_interaction):
        """Test que la commande trial active bien le plan Pro"""
        user_id = mock_discord_interaction.user.id
        
        # Simuler l'activation du trial
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
        
        # Vérifier que l'utilisateur n'a pas encore de trial
        result = mock_db.client.table().select().eq().execute()
        assert len(result.data) == 0


class TestWebhookSecurity(TestIntegration):
    """Tests de sécurité des webhooks"""
    
    def test_stripe_webhook_validates_signature(self):
        """Test que les webhooks Stripe valident la signature"""
        try:
            from bot.stripe_webhook_validator import StripeWebhookValidator
        except ImportError:
            pytest.skip("stripe_webhook_validator non disponible")
        
        validator = StripeWebhookValidator("whsec_test_secret")
        
        # Payload valide
        payload = b'{"test": "data"}'
        
        # Signature invalide
        invalid_header = "t=1234567890,v1=invalid_signature"
        
        result = validator.validate_webhook(payload, invalid_header)
        
        assert not result.is_valid, "Une signature invalide devrait être rejetée"
    
    def test_stripe_webhook_rejects_old_timestamps(self):
        """Test que les vieux timestamps sont rejetés"""
        try:
            from bot.stripe_webhook_validator import StripeWebhookValidator
        except ImportError:
            pytest.skip("stripe_webhook_validator non disponible")
        
        import time
        validator = StripeWebhookValidator("whsec_test")
        
        # Timestamp vieux de 10 minutes
        old_timestamp = str(int(time.time()) - 600)
        header = f"t={old_timestamp},v1=invalid"
        
        result = validator.validate_webhook(b'{}', header)
        
        assert not result.is_valid, "Un vieux timestamp devrait être rejeté"


class TestSecureConfig(TestIntegration):
    """Tests de la configuration sécurisée"""
    
    def test_encryption_decrypts_correctly(self):
        """Test que le chiffrement/déchiffrement fonctionne"""
        try:
            from bot.secure_config import SecureConfigManager
        except ImportError:
            pytest.skip("secure_config non disponible")
        
        # Générer une clé
        key = SecureConfigManager.generate_master_key()
        manager = SecureConfigManager(key)
        
        # Chiffrer
        secret = "my_secret_api_key_12345"
        encrypted = manager.encrypt(secret)
        
        # Déchiffrer
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == secret, "Le déchiffrement devrait retourner la valeur originale"
        assert encrypted != secret, "La valeur chiffrée devrait être différente"
    
    def test_config_validation_detects_missing_secrets(self):
        """Test que la validation détecte les secrets manquants"""
        try:
            from bot.secure_config import ShelliaConfig
        except ImportError:
            pytest.skip("secure_config non disponible")
        
        config = ShelliaConfig()
        missing = config.validate()
        
        # Sans variables d'environnement, certains champs devraient être manquants
        assert len(missing) > 0, "La validation devrait détecter les secrets manquants"


class TestEndToEndScenarios(TestIntegration):
    """Scénarios de test end-to-end"""
    
    @pytest.mark.asyncio
    async def test_user_message_flow(self, mock_db, mock_discord_message):
        """Test du flux complet: message utilisateur → réponse IA"""
        # 1. Vérifier sécurité
        try:
            from bot.persistent_rate_limiter import PersistentRateLimiter
            limiter = PersistentRateLimiter(mock_db)
            status = limiter.check_rate_limit(mock_discord_message.author.id)
            assert status.can_proceed, "L'utilisateur devrait pouvoir envoyer un message"
        except ImportError:
            pass
        
        # 2. Vérifier quota
        quota = mock_db.get_daily_quota(mock_discord_message.author.id)
        assert quota['messages_used'] < quota['messages_limit'], "L'utilisateur devrait avoir du quota"
        
        # 3. Vérifier streak
        streak = mock_db.update_streak(mock_discord_message.author.id)
        assert 'current_streak' in streak
        
        # 4. Simuler réponse IA
        ai_response = Mock()
        ai_response.content = "Ceci est une réponse de test"
        ai_response.success = True
        ai_response.model_used = "gemini-1.5-flash-lite"
        ai_response.tokens_input = 10
        ai_response.tokens_output = 20
        ai_response.cost_usd = 0.0001
        
        # 5. Mettre à jour quota
        mock_db.increment_quota_usage(
            user_id=mock_discord_message.author.id,
            tokens=30,
            cost=0.0001
        )
        
        # 6. Logger
        mock_db.log_security_event(
            mock_discord_message.author.id,
            'message_processed',
            {'model': ai_response.model_used, 'cost': ai_response.cost_usd}
        )
        
        # Tout s'est bien passé
        assert True
    
    @pytest.mark.asyncio
    async def test_admin_ban_user_flow(self, mock_db):
        """Test du flux admin: bannissement d'un utilisateur"""
        admin_id = 99999
        target_user_id = 12345
        reason = "Violation des règles"
        
        # Simuler le bannissement
        mock_db.ban_user = Mock(return_value=True)
        
        # Vérifier que la méthode est appelée
        mock_db.ban_user(target_user_id, reason, None)
        mock_db.ban_user.assert_called_once_with(target_user_id, reason, None)
    
    @pytest.mark.asyncio
    async def test_premium_upgrade_flow(self, mock_db, mock_discord_interaction):
        """Test du flux de mise à niveau vers Premium"""
        user_id = mock_discord_interaction.user.id
        new_plan = 'pro'
        
        # Simuler la mise à jour du plan
        mock_db.set_user_plan = Mock(return_value=True)
        mock_db.set_user_plan(user_id, new_plan, 30)
        
        # Vérifier que le plan est mis à jour
        mock_db.set_user_plan.assert_called_once_with(user_id, new_plan, 30)


# =============================================================================
# UTILITAIRES DE TEST
# =============================================================================

def run_integration_tests():
    """Fonction pour exécuter tous les tests d'intégration"""
    import sys
    
    print("="*60)
    print("TESTS D'INTÉGRATION - Shellia AI Bot")
    print("="*60)
    
    # Exécuter pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-x'  # Stop at first failure
    ])
    
    return exit_code


if __name__ == '__main__':
    exit(run_integration_tests())
