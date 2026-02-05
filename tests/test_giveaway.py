"""
🧪 Tests pour le système de giveaways automatiques
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import discord

# Imports à tester
import sys
sys.path.insert(0, 'bot')

from auto_giveaway import (
    AutoGiveawayManager, 
    MilestoneReward, 
    GiveawayEntry,
    ActiveGiveaway,
    GiveawayStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_bot():
    """Crée un bot mock"""
    bot = Mock()
    bot.user = Mock()
    bot.user.id = 123456789
    bot.loop = asyncio.get_event_loop()
    bot.is_closed = Mock(return_value=False)
    bot.wait_until_ready = AsyncMock()
    return bot


@pytest.fixture
def mock_db():
    """Crée une DB mock"""
    db = Mock()
    db.fetch = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def giveaway_manager(mock_bot, mock_db):
    """Crée un gestionnaire de giveaways"""
    return AutoGiveawayManager(mock_bot, mock_db)


@pytest.fixture
def sample_reward():
    """Crée une récompense d'exemple"""
    return MilestoneReward(
        member_count=50,
        currency_reward=500,
        description="Test giveaway",
        giveaway_duration_hours=24,
        winners_count=2
    )


# ============================================================================
# TESTS MILESTONE REWARD
# ============================================================================

class TestMilestoneReward:
    """Tests pour les récompenses de palier"""
    
    def test_create_reward(self):
        """Test création d'une récompense"""
        reward = MilestoneReward(
            member_count=100,
            currency_reward=1000,
            role_reward=None,
            nitro_reward=False,
            custom_reward="Test",
            giveaway_duration_hours=48,
            winners_count=3,
            description="Test description"
        )
        
        assert reward.member_count == 100
        assert reward.currency_reward == 1000
        assert reward.winners_count == 3
        assert reward.description == "Test description"
    
    def test_to_dict(self):
        """Test conversion en dictionnaire"""
        reward = MilestoneReward(member_count=50, currency_reward=500)
        data = reward.to_dict()
        
        assert data['member_count'] == 50
        assert data['currency_reward'] == 500
        assert 'description' in data
    
    def test_from_dict(self):
        """Test création depuis un dictionnaire"""
        data = {
            'member_count': 100,
            'currency_reward': 1000,
            'role_reward': None,
            'nitro_reward': False,
            'custom_reward': 'Test',
            'giveaway_duration_hours': 48,
            'winners_count': 3,
            'description': 'Test'
        }
        
        reward = MilestoneReward.from_dict(data)
        assert reward.member_count == 100
        assert reward.currency_reward == 1000


# ============================================================================
# TESTS GIVEAWAY ENTRY
# ============================================================================

class TestGiveawayEntry:
    """Tests pour les entrées de giveaway"""
    
    def test_create_entry(self):
        """Test création d'une entrée"""
        entry = GiveawayEntry(
            user_id=123456789,
            joined_at=datetime.utcnow(),
            message_id=987654321
        )
        
        assert entry.user_id == 123456789
        assert entry.message_id == 987654321
    
    def test_to_dict(self):
        """Test conversion en dictionnaire"""
        now = datetime.utcnow()
        entry = GiveawayEntry(user_id=123, joined_at=now)
        data = entry.to_dict()
        
        assert data['user_id'] == 123
        assert 'joined_at' in data


# ============================================================================
# TESTS ACTIVE GIVEAWAY
# ============================================================================

class TestActiveGiveaway:
    """Tests pour les giveaways actifs"""
    
    def test_create_giveaway(self, sample_reward):
        """Test création d'un giveaway"""
        giveaway = ActiveGiveaway(
            id="abc123",
            milestone=50,
            reward=sample_reward,
            channel_id=123456,
            message_id=789012,
            host_id=111111,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=24),
            entries=[],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        assert giveaway.id == "abc123"
        assert giveaway.milestone == 50
        assert giveaway.entry_count == 0
        assert giveaway.status == GiveawayStatus.ACTIVE
    
    def test_entry_count(self, sample_reward):
        """Test comptage des entrées"""
        entries = [
            GiveawayEntry(user_id=1, joined_at=datetime.utcnow()),
            GiveawayEntry(user_id=2, joined_at=datetime.utcnow()),
            GiveawayEntry(user_id=3, joined_at=datetime.utcnow()),
        ]
        
        giveaway = ActiveGiveaway(
            id="test",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=1),
            entries=entries,
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        assert giveaway.entry_count == 3
    
    def test_time_remaining(self, sample_reward):
        """Test calcul du temps restant"""
        future = datetime.utcnow() + timedelta(hours=24)
        giveaway = ActiveGiveaway(
            id="test",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=future,
            entries=[],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        remaining = giveaway.time_remaining
        assert remaining.total_seconds() > 0
        assert remaining.total_seconds() <= 86400  # 24h


# ============================================================================
# TESTS AUTO GIVEAWAY MANAGER
# ============================================================================

class TestAutoGiveawayManager:
    """Tests pour le gestionnaire de giveaways"""
    
    @pytest.mark.asyncio
    async def test_setup(self, giveaway_manager):
        """Test initialisation"""
        with patch.object(giveaway_manager, '_load_from_db', new_callable=AsyncMock):
            await giveaway_manager.setup()
            
            assert giveaway_manager.check_milestones_task is not None
            assert giveaway_manager.update_giveaway_messages_task is not None
    
    def test_default_milestones(self, giveaway_manager):
        """Test que les paliers par défaut sont chargés"""
        assert len(giveaway_manager.milestones) > 0
        assert 50 in giveaway_manager.milestones
        assert 100 in giveaway_manager.milestones
        assert 1000 in giveaway_manager.milestones
    
    @pytest.mark.asyncio
    async def test_add_custom_milestone(self, giveaway_manager):
        """Test ajout d'un palier personnalisé"""
        reward = MilestoneReward(
            member_count=75,
            currency_reward=750,
            description="Test custom",
            giveaway_duration_hours=24,
            winners_count=1
        )
        
        with patch.object(giveaway_manager, '_save_milestone_config', new_callable=AsyncMock):
            success = await giveaway_manager.add_custom_milestone(75, reward)
            
            assert success is True
            assert 75 in giveaway_manager.milestones
    
    @pytest.mark.asyncio
    async def test_add_duplicate_milestone(self, giveaway_manager):
        """Test ajout d'un palier déjà existant"""
        reward = MilestoneReward(
            member_count=50,  # Déjà existe
            currency_reward=500,
            description="Duplicate",
            giveaway_duration_hours=24,
            winners_count=1
        )
        
        success = await giveaway_manager.add_custom_milestone(50, reward)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_remove_default_milestone(self, giveaway_manager):
        """Test suppression d'un palier par défaut (doit échouer)"""
        success = await giveaway_manager.remove_milestone(50)
        assert success is False
        assert 50 in giveaway_manager.milestones
    
    @pytest.mark.asyncio
    async def test_add_and_remove_custom_milestone(self, giveaway_manager):
        """Test ajout puis suppression d'un palier personnalisé"""
        # D'abord l'ajouter
        reward = MilestoneReward(
            member_count=999,
            currency_reward=999,
            description="Test",
            giveaway_duration_hours=24,
            winners_count=1
        )
        
        with patch.object(giveaway_manager, '_save_milestone_config', new_callable=AsyncMock):
            await giveaway_manager.add_custom_milestone(999, reward)
        
        # Puis le supprimer
        with patch.object(giveaway_manager, '_remove_milestone_config', new_callable=AsyncMock):
            success = await giveaway_manager.remove_milestone(999)
            
            assert success is True
            assert 999 not in giveaway_manager.milestones
    
    @pytest.mark.asyncio
    async def test_add_entry(self, giveaway_manager, sample_reward):
        """Test ajout d'une participation"""
        giveaway = ActiveGiveaway(
            id="test123",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=24),
            entries=[],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        giveaway_manager.active_giveaways["test123"] = giveaway
        
        with patch.object(giveaway_manager, '_save_entry', new_callable=AsyncMock):
            success = await giveaway_manager.add_entry("test123", 123456)
            
            assert success is True
            assert giveaway.entry_count == 1
    
    @pytest.mark.asyncio
    async def test_add_duplicate_entry(self, giveaway_manager, sample_reward):
        """Test ajout d'une participation en double (doit échouer)"""
        entry = GiveawayEntry(user_id=123456, joined_at=datetime.utcnow())
        giveaway = ActiveGiveaway(
            id="test123",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=24),
            entries=[entry],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        giveaway_manager.active_giveaways["test123"] = giveaway
        
        success = await giveaway_manager.add_entry("test123", 123456)
        assert success is False
        assert giveaway.entry_count == 1
    
    @pytest.mark.asyncio
    async def test_remove_entry(self, giveaway_manager, sample_reward):
        """Test retrait d'une participation"""
        entry = GiveawayEntry(user_id=123456, joined_at=datetime.utcnow())
        giveaway = ActiveGiveaway(
            id="test123",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=24),
            entries=[entry],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        giveaway_manager.active_giveaways["test123"] = giveaway
        
        with patch.object(giveaway_manager, '_remove_entry_db', new_callable=AsyncMock):
            success = await giveaway_manager.remove_entry("test123", 123456)
            
            assert success is True
            assert giveaway.entry_count == 0


# ============================================================================
# TESTS INTÉGRATION
# ============================================================================

class TestGiveawayIntegration:
    """Tests d'intégration"""
    
    @pytest.mark.asyncio
    async def test_full_giveaway_lifecycle(self, giveaway_manager, sample_reward):
        """Test le cycle complet d'un giveaway"""
        # Créer un giveaway
        giveaway = ActiveGiveaway(
            id="lifecycle",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=1),
            entries=[],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        giveaway_manager.active_giveaways["lifecycle"] = giveaway
        
        # Ajouter des participants
        for i in range(10):
            await giveaway_manager.add_entry("lifecycle", 100000 + i)
        
        assert giveaway.entry_count == 10
        
        # Terminer le giveaway
        with patch.object(giveaway_manager, '_update_giveaway_ended', new_callable=AsyncMock):
            with patch.object(giveaway_manager, '_announce_winners', new_callable=AsyncMock):
                with patch.object(giveaway_manager, '_distribute_rewards', new_callable=AsyncMock):
                    with patch.object(giveaway_manager, '_update_giveaway_status', new_callable=AsyncMock):
                        result = await giveaway_manager.end_giveaway("lifecycle", manual=True)
                        
                        assert result is not None
                        assert result.status == GiveawayStatus.ENDED


# ============================================================================
# TESTS SÉCURITÉ
# ============================================================================

class TestGiveawaySecurity:
    """Tests de sécurité"""
    
    @pytest.mark.asyncio
    async def test_cannot_add_entry_to_ended_giveaway(self, giveaway_manager, sample_reward):
        """Test qu'on ne peut pas participer à un giveaway terminé"""
        giveaway = ActiveGiveaway(
            id="ended",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=1),
            entries=[],
            status=GiveawayStatus.ENDED,  # Déjà terminé
            winners=[]
        )
        
        giveaway_manager.active_giveaways["ended"] = giveaway
        
        success = await giveaway_manager.add_entry("ended", 123456)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cannot_add_entry_after_end_time(self, giveaway_manager, sample_reward):
        """Test qu'on ne peut pas participer après la fin"""
        giveaway = ActiveGiveaway(
            id="expired",
            milestone=50,
            reward=sample_reward,
            channel_id=1,
            message_id=1,
            host_id=1,
            started_at=datetime.utcnow() - timedelta(hours=2),
            ends_at=datetime.utcnow() - timedelta(hours=1),  # Déjà fini
            entries=[],
            status=GiveawayStatus.ACTIVE,  # Statut pas encore mis à jour
            winners=[]
        )
        
        giveaway_manager.active_giveaways["expired"] = giveaway
        
        success = await giveaway_manager.add_entry("expired", 123456)
        assert success is False


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
