"""
CONFIGURATION - Shellia AI Bot avec Supabase
"""

import os
from dataclasses import dataclass
from typing import Dict, List

# ============================================================================
# ENVIRONNEMENT
# ============================================================================

class EnvConfig:
    """Variables d'environnement"""
    # Discord
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Stripe (optionnel)
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')


# ============================================================================
# SÉCURITÉ
# ============================================================================

@dataclass
class SecurityConfig:
    COOLDOWN_SECONDS = 3
    MAX_MESSAGES_PER_MINUTE = 10
    MAX_MESSAGES_PER_HOUR = 100
    MAX_MESSAGE_LENGTH = 4000
    SPAM_THRESHOLD = 5
    AUTO_BAN_WARNINGS = 3
    
    # Rôles Discord à créer
    ROLES = {
        'ADMIN': {
            'name': '🛡️ Admin',
            'color': 0xFF0000,
            'permissions': ['administrator'],
            'hoist': True,
            'mentionable': True
        },
        'MODERATOR': {
            'name': '🔨 Modérateur',
            'color': 0x00FF00,
            'permissions': [
                'kick_members', 'ban_members', 'manage_messages',
                'manage_nicknames', 'moderate_members'
            ],
            'hoist': True,
            'mentionable': True
        },
        'SUPPORT': {
            'name': '💬 Support',
            'color': 0x3498db,
            'permissions': ['manage_messages'],
            'hoist': True,
            'mentionable': True
        },
        'PREMIUM': {
            'name': '💎 Premium',
            'color': 0x9b59b6,
            'permissions': [],
            'hoist': True,
            'mentionable': False
        },
        'FOUNDER': {
            'name': '🔥 Founder',
            'color': 0xe74c3c,
            'permissions': [],
            'hoist': True,
            'mentionable': False
        },
        'USER': {
            'name': '👤 Membre',
            'color': 0x95a5a6,
            'permissions': [],
            'hoist': False,
            'mentionable': False
        }
    }


# ============================================================================
# PLANS
# ============================================================================

@dataclass
class Plan:
    name: str
    price_monthly: float
    price_yearly: float
    daily_quota: int
    max_message_length: int
    flash_lite_ratio: float
    flash_ratio: float
    pro_ratio: float
    has_private_channel: bool
    channel_customization: bool
    history_days: int
    can_export: bool
    can_upload: bool
    max_file_size: int
    can_generate_images: bool
    image_quota: int
    support_priority: str
    streak_multiplier: float
    referral_multiplier: float
    discord_role: str = None


PLANS = {
    'free': Plan(
        name='Free', price_monthly=0, price_yearly=0,
        daily_quota=10, max_message_length=1000,
        flash_lite_ratio=1.0, flash_ratio=0.0, pro_ratio=0.0,
        has_private_channel=False, channel_customization=False,
        history_days=1, can_export=False, can_upload=False, max_file_size=0,
        can_generate_images=False, image_quota=0,
        support_priority='community', streak_multiplier=1.0, referral_multiplier=1.0,
        discord_role='USER'
    ),
    'basic': Plan(
        name='Basic', price_monthly=4.99, price_yearly=47.90,
        daily_quota=50, max_message_length=2000,
        flash_lite_ratio=1.0, flash_ratio=0.0, pro_ratio=0.0,
        has_private_channel=False, channel_customization=False,
        history_days=7, can_export=False, can_upload=True, max_file_size=5,
        can_generate_images=False, image_quota=0,
        support_priority='normal', streak_multiplier=1.0, referral_multiplier=1.0,
        discord_role='PREMIUM'
    ),
    'pro': Plan(
        name='Pro', price_monthly=9.99, price_yearly=95.90,
        daily_quota=150, max_message_length=4000,
        flash_lite_ratio=0.85, flash_ratio=0.15, pro_ratio=0.0,
        has_private_channel=True, channel_customization=True,
        history_days=30, can_export=True, can_upload=True, max_file_size=25,
        can_generate_images=True, image_quota=10,
        support_priority='priority', streak_multiplier=1.5, referral_multiplier=1.5,
        discord_role='PREMIUM'
    ),
    'ultra': Plan(
        name='Ultra', price_monthly=29.99, price_yearly=287.90,
        daily_quota=400, max_message_length=8000,
        flash_lite_ratio=0.75, flash_ratio=0.25, pro_ratio=0.0,
        has_private_channel=True, channel_customization=True,
        history_days=365, can_export=True, can_upload=True, max_file_size=100,
        can_generate_images=True, image_quota=50,
        support_priority='vip', streak_multiplier=2.0, referral_multiplier=2.0,
        discord_role='PREMIUM'
    ),
    'founder': Plan(
        name='Founder', price_monthly=3.49, price_yearly=33.90,
        daily_quota=75, max_message_length=2000,
        flash_lite_ratio=1.0, flash_ratio=0.0, pro_ratio=0.0,
        has_private_channel=True, channel_customization=False,
        history_days=14, can_export=False, can_upload=True, max_file_size=10,
        can_generate_images=False, image_quota=0,
        support_priority='priority', streak_multiplier=1.25, referral_multiplier=1.25,
        discord_role='FOUNDER'
    )
}


# ============================================================================
# CHANNELS
# ============================================================================

class ChannelConfig:
    CATEGORIES = {
        'INFO': {
            'name': '📋 INFORMATIONS',
            'channels': [
                {'name': '📌│règles', 'topic': 'Règles du serveur'},
                {'name': '📢│annonces', 'topic': 'Annonces officielles'},
                {'name': '🎁│nouveautés', 'topic': 'Nouvelles fonctionnalités'},
            ]
        },
        'WELCOME': {
            'name': '👋 BIENVENUE',
            'channels': [
                {'name': '👋│bienvenue', 'topic': 'Souhaitez la bienvenue aux nouveaux'},
                {'name': '🎫│vérification', 'topic': 'Vérifiez-vous pour accéder au serveur'},
                {'name': '🎁│roles', 'topic': 'Choisissez vos rôles'},
            ]
        },
        'COMMUNITY': {
            'name': '💬 COMMUNAUTÉ',
            'channels': [
                {'name': '💬│général', 'topic': 'Discussion générale'},
                {'name': '🎮│détente', 'topic': 'Hors-sujet'},
                {'name': '📸│médias', 'topic': 'Partagez vos créations'},
                {'name': '🌍│international', 'topic': 'English & other languages'},
            ]
        },
        'AI_CHAT': {
            'name': '🤖 IA CHAT',
            'channels': [
                {'name': '🤖│chat-ia', 'topic': 'Discutez avec Shellia AI'},
                {'name': '💡│aide-ia', 'topic': 'Aide et tutoriels'},
                {'name': '🎨│images-ia', 'topic': 'Génération d\'images (Pro/Ultra)'},
            ]
        },
        'SUPPORT': {
            'name': '🆘 SUPPORT',
            'channels': [
                {'name': '❓│questions', 'topic': 'Questions générales'},
                {'name': '🐛│bugs', 'topic': 'Signalez les bugs'},
                {'name': '💡│suggestions', 'topic': 'Vos idées et suggestions'},
                {'name': '🎫│tickets', 'topic': 'Ouvrez un ticket privé'},
            ]
        },
        'LEADERBOARD': {
            'name': '🏆 CLASSEMENTS',
            'channels': [
                {'name': '📊│leaderboard', 'topic': 'Classement des utilisateurs'},
                {'name': '🏅│badges', 'topic': 'Badges débloqués'},
                {'name': '🔥│streaks', 'topic': 'Streaks en cours'},
            ]
        },
        'VIP': {
            'name': '💎 ESPACE VIP',
            'channels': [
                {'name': '💎│vip-chat', 'topic': 'Chat exclusif Premium'},
                {'name': '🎁│vip-annonces', 'topic': 'Annonces exclusives'},
                {'name': '🎯│beta', 'topic': 'Accès aux fonctionnalités beta'},
            ]
        },
        'PRIVATE': {
            'name': '🔒 ESPACES PRIVÉS',
            'channels': []  # Créés dynamiquement
        },
        'LOGS': {
            'name': '🔍 LOGS',
            'channels': [
                {'name': '📊│stats', 'topic': 'Statistiques du bot'},
                {'name': '🔍│logs', 'topic': 'Logs du serveur'},
                {'name': '⚠️│alertes', 'topic': 'Alertes automatiques'},
            ]
        },
        'ADMIN': {
            'name': '🔒 ADMINISTRATION',
            'channels': [
                {'name': '💬│admin-chat', 'topic': 'Discussion admin'},
                {'name': '📋│mod-logs', 'topic': 'Actions de modération'},
                {'name': '💰│revenus', 'topic': 'Suivi des revenus'},
                {'name': '🤖│bot-control', 'topic': 'Contrôle du bot'},
            ]
        }
    }


# ============================================================================
# GEMINI
# ============================================================================

class ModelConfig:
    FLASH_LITE = "gemini-2.5-flash-lite"
    FLASH = "gemini-2.5-flash"
    PRO = "gemini-2.5-pro"
    
    COSTS = {
        FLASH_LITE: {'input': 0.10, 'output': 0.40},
        FLASH: {'input': 0.30, 'output': 2.50},
        PRO: {'input': 0.60, 'output': 10.00}
    }


# ============================================================================
# STREAKS
# ============================================================================

class StreakConfig:
    BONUS = {1: 0, 2: 5, 3: 10, 4: 15, 5: 20, 6: 25, 7: 50, 14: 75, 30: 100, 60: 150, 100: 200}
    
    BADGES = {
        3: {'emoji': '🔥', 'name': 'Sur la lancée'},
        7: {'emoji': '⚡', 'name': 'Habitué'},
        14: {'emoji': '🌟', 'name': 'Expert'},
        30: {'emoji': '👑', 'name': 'Addict'},
        60: {'emoji': '💎', 'name': 'Maître'},
        100: {'emoji': '🏆', 'name': 'Légende'}
    }


# ============================================================================
# BADGES
# ============================================================================

BADGES = {
    'first_message': {'name': '💬 Premier pas', 'desc': 'Envoyer votre premier message'},
    'chatter_100': {'name': '🗣️ Bavard', 'desc': '100 messages'},
    'chatter_1000': {'name': '📢 Grand bavard', 'desc': '1000 messages'},
    'chatter_10000': {'name': '👑 Maître', 'desc': '10000 messages'},
    'streak_3': {'emoji': '🔥', 'name': 'Sur la lancée', 'desc': '3 jours consécutifs'},
    'streak_7': {'emoji': '⚡', 'name': 'Habitué', 'desc': '7 jours consécutifs'},
    'streak_30': {'emoji': '🌟', 'name': 'Addict', 'desc': '30 jours consécutifs'},
    'streak_100': {'emoji': '🏆', 'name': 'Légende', 'desc': '100 jours consécutifs'},
    'basic_member': {'name': '💎 Basic', 'desc': 'Plan Basic'},
    'pro_member': {'name': '🚀 Pro', 'desc': 'Plan Pro'},
    'ultra_member': {'name': '👑 Ultra', 'desc': 'Plan Ultra'},
    'founder_member': {'name': '🔥 Founder', 'desc': 'Prix fondateur'},
    'referrer_3': {'name': '🤝 Parrain', 'desc': '3 filleuls'},
    'referrer_10': {'name': '🌟 Super Parrain', 'desc': '10 filleuls'},
    'top_10': {'name': '🏆 TOP 10', 'desc': 'Entrer dans le TOP 10'},
}
