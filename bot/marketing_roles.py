"""
🎭 SYSTÈME DE RÔLES MARKETING - Shellia AI
Gère les rôles activables pour le marketing du serveur
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class MarketingRoleType(Enum):
    """Types de rôles marketing"""
    AMBASSADOR = "ambassador"      # Ambassadeur
    INFLUENCER = "influencer"      # Influenceur
    CREATOR = "creator"            # Créateur de contenu
    HELPER = "helper"              # Helper communauté
    EVENT_HOST = "event_host"      # Organisateur d'événements
    TESTER = "tester"              # Testeur beta
    PARTNER = "partner"            # Partenaire


@dataclass
class MarketingRole:
    """Configuration d'un rôle marketing"""
    id: str
    type: MarketingRoleType
    name: str
    description: str
    color: int
    permissions: List[str]
    benefits: List[str]
    requirements: Dict[str, Any]
    max_slots: Optional[int] = None
    is_active: bool = True


class MarketingRolesManager:
    """
    🎯 Gestionnaire des rôles marketing activables
    """
    
    DEFAULT_ROLES = {
        MarketingRoleType.AMBASSADOR: MarketingRole(
            id="ambassador",
            type=MarketingRoleType.AMBASSADOR,
            name="🌟 Ambassadeur",
            description="Représente la communauté et attire de nouveaux membres",
            color=0xFFD700,  # Or
            permissions=["send_messages", "embed_links", "attach_files", "use_external_emojis"],
            benefits=[
                "Badge exclusif Ambassadeur",
                "Accès au salon #🏆│ambassadeurs",
                "Commission sur parrainages: 20%",
                "Accès anticipé aux nouvelles features",
                "Support prioritaire"
            ],
            requirements={
                "min_invites": 10,
                "min_messages": 500,
                "account_age_days": 30,
                "no_warns": True
            },
            max_slots=20
        ),
        MarketingRoleType.INFLUENCER: MarketingRole(
            id="influencer",
            type=MarketingRoleType.INFLUENCER,
            name="📢 Influenceur",
            description="Crée du contenu et fait connaître le serveur",
            color=0x9B59B6,  # Violet
            permissions=["send_messages", "embed_links", "attach_files", "use_external_emojis", "mention_everyone"],
            benefits=[
                "Badge Influenceur",
                "Salon privé #📢│influenceurs",
                "Partenariat contenu: €50-200/mois",
                "Accès aux stats avancées",
                "Contact direct avec l'équipe"
            ],
            requirements={
                "min_followers": 1000,
                "content_quality_score": 80,
                "posts_per_week": 2
            },
            max_slots=10
        ),
        MarketingRoleType.CREATOR: MarketingRole(
            id="creator",
            type=MarketingRoleType.CREATOR,
            name="🎨 Créateur",
            description="Crée des visuels, vidéos, ou contenu pour la communauté",
            color=0xE74C3C,  # Rouge
            permissions=["send_messages", "embed_links", "attach_files"],
            benefits=[
                "Badge Créateur",
                "Salon #🎨│createurs",
                "Rémunération par contenu: €10-50/piece",
                "Accès aux ressources graphiques",
                "Feedback direct sur les créations"
            ],
            requirements={
                "portfolio_submitted": True,
                "sample_content_approved": True
            },
            max_slots=15
        ),
        MarketingRoleType.HELPER: MarketingRole(
            id="helper",
            type=MarketingRoleType.HELPER,
            name="🆘 Helper",
            description="Aide les nouveaux membres et modère la communauté",
            color=0x3498DB,  # Bleu
            permissions=["send_messages", "embed_links", "add_reactions"],
            benefits=[
                "Badge Helper",
                "Salon #🆘│helpers",
                "Récompenses mensuelles: €20-50",
                "Accès aux outils de modération basiques",
                "Reconnaissance communautaire"
            ],
            requirements={
                "help_messages": 100,
                "community_score": 90,
                "time_on_server_days": 60
            },
            max_slots=30
        ),
        MarketingRoleType.EVENT_HOST: MarketingRole(
            id="event_host",
            type=MarketingRoleType.EVENT_HOST,
            name="🎉 Event Host",
            description="Organise des événements et des activités pour la communauté",
            color=0x2ECC71,  # Vert
            permissions=["send_messages", "embed_links", "mention_here", "manage_messages"],
            benefits=[
                "Badge Event Host",
                "Budget événement: €50-200/événement",
                "Outils d'organisation avancés",
                "Promotion de ses événements",
                "Commission sur participants"
            ],
            requirements={
                "events_hosted": 3,
                "avg_participants": 20,
                "event_ideas_approved": True
            },
            max_slots=8
        ),
        MarketingRoleType.TESTER: MarketingRole(
            id="tester",
            type=MarketingRoleType.TESTER,
            name="🧪 Beta Tester",
            description="Teste les nouvelles features avant tout le monde",
            color=0xF39C12,  # Orange
            permissions=["send_messages", "embed_links", "attach_files"],
            benefits=[
                "Badge Beta Tester",
                "Accès anticipé aux features",
                "Plan Pro gratuit pendant tests",
                "Feedback direct avec les devs",
                "Récompenses pour bugs trouvés"
            ],
            requirements={
                "technical_knowledge": "intermediate",
                "availability_hours": 5,
                "feedback_quality_score": 80
            },
            max_slots=25
        ),
        MarketingRoleType.PARTNER: MarketingRole(
            id="partner",
            type=MarketingRoleType.PARTNER,
            name="🤝 Partenaire",
            description="Partenaire officiel du serveur (streamers, serveurs, etc.)",
            color=0x1ABC9C,  # Turquoise
            permissions=["send_messages", "embed_links", "attach_files", "mention_here"],
            benefits=[
                "Badge Partenaire officiel",
                "Salon partenaires exclusif",
                "Cross-promotion",
                "Commission affiliation: 30%",
                "Support dédié"
            ],
            requirements={
                "partnership_approved": True,
                "min_audience": 500,
                "brand_alignment": True
            },
            max_slots=5
        )
    }
    
    def __init__(self, bot: commands.Bot, db=None):
        self.bot = bot
        self.db = db
        self.roles: Dict[str, MarketingRole] = {}
        self.user_roles: Dict[int, List[str]] = {}  # user_id -> [role_ids]
        
    async def setup(self):
        """Initialise le système"""
        # Charger les rôles par défaut
        for role_type, role in self.DEFAULT_ROLES.items():
            self.roles[role.id] = role
            
        # Charger depuis DB
        if self.db:
            await self._load_from_db()
            
        logger.info(f"✅ MarketingRolesManager initialisé avec {len(self.roles)} rôles")
        
    async def _load_from_db(self):
        """Charge les données depuis la DB"""
        try:
            # Charger les attributions de rôles
            result = await self.db.fetch("SELECT user_id, role_id FROM user_marketing_roles")
            for row in result:
                user_id = row['user_id']
                role_id = row['role_id']
                if user_id not in self.user_roles:
                    self.user_roles[user_id] = []
                self.user_roles[user_id].append(role_id)
        except Exception as e:
            logger.error(f"Erreur chargement rôles marketing: {e}")
            
    async def can_apply(self, user_id: int, role_id: str) -> tuple:
        """
        Vérifie si un utilisateur peut postuler à un rôle
        Retourne: (can_apply: bool, reason: str, missing_requirements: list)
        """
        role = self.roles.get(role_id)
        if not role:
            return False, "Rôle non trouvé", []
            
        if not role.is_active:
            return False, "Ce rôle n'est pas actuellement disponible", []
            
        # Vérifier si a déjà le rôle
        if user_id in self.user_roles and role_id in self.user_roles[user_id]:
            return False, "Vous avez déjà ce rôle", []
            
        # Vérifier les slots disponibles
        if role.max_slots:
            current_count = await self._get_role_count(role_id)
            if current_count >= role.max_slots:
                return False, f"Plus de places disponibles ({role.max_slots} maximum)", []
                
        # Vérifier les requirements
        missing = await self._check_requirements(user_id, role.requirements)
        
        if missing:
            return False, "Requirements non satisfaits", missing
            
        return True, "Vous pouvez postuler !", []
        
    async def _check_requirements(self, user_id: int, requirements: Dict) -> List[str]:
        """Vérifie les requirements et retourne ceux qui manquent"""
        missing = []
        
        if not self.db:
            return missing
            
        # Récupérer les stats utilisateur
        result = await self.db.fetch(
            """
            SELECT messages_sent, created_at, 
                   (SELECT COUNT(*) FROM referral_tracking WHERE referrer_id = %s) as invites,
                   (SELECT COUNT(*) FROM moderation_logs WHERE user_id = %s AND action = 'warn') as warns
            FROM users WHERE user_id = %s
            """,
            (user_id, user_id, user_id)
        )
        
        if not result:
            return ["Compte utilisateur non trouvé"]
            
        user_data = result[0]
        
        # Vérifier chaque requirement
        for req, value in requirements.items():
            if req == "min_invites":
                if user_data['invites'] < value:
                    missing.append(f"Invitations: {user_data['invites']}/{value}")
                    
            elif req == "min_messages":
                if user_data['messages_sent'] < value:
                    missing.append(f"Messages: {user_data['messages_sent']}/{value}")
                    
            elif req == "account_age_days":
                account_age = (datetime.utcnow() - user_data['created_at']).days
                if account_age < value:
                    missing.append(f"Ancienneté: {account_age}j/{value}j")
                    
            elif req == "no_warns":
                if user_data['warns'] > 0:
                    missing.append(f"Sanctions: {user_data['warns']} (doit être 0)")
                    
        return missing
        
    async def _get_role_count(self, role_id: str) -> int:
        """Compte le nombre d'utilisateurs ayant un rôle"""
        if not self.db:
            return 0
            
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM user_marketing_roles WHERE role_id = %s",
            (role_id,)
        )
        return result[0]['count'] if result else 0
        
    async def apply_for_role(self, user_id: int, role_id: str, application_text: str = "") -> bool:
        """Soumet une candidature pour un rôle"""
        role = self.roles.get(role_id)
        if not role:
            return False
            
        # Vérifier si peut postuler
        can_apply, reason, missing = await self.can_apply(user_id, role_id)
        if not can_apply:
            return False
            
        # Créer la candidature
        if self.db:
            await self.db.execute(
                """
                INSERT INTO marketing_role_applications 
                (user_id, role_id, application_text, status, created_at)
                VALUES (%s, %s, %s, 'pending', NOW())
                """,
                (user_id, role_id, application_text)
            )
            
        return True
        
    async def approve_application(self, user_id: int, role_id: str, admin_id: int) -> bool:
        """Approuve une candidature"""
        role = self.roles.get(role_id)
        if not role:
            return False
            
        # Ajouter le rôle à l'utilisateur
        await self._grant_role(user_id, role_id, admin_id)
        
        # Mettre à jour la candidature
        if self.db:
            await self.db.execute(
                """
                UPDATE marketing_role_applications 
                SET status = 'approved', reviewed_by = %s, reviewed_at = NOW()
                WHERE user_id = %s AND role_id = %s
                """,
                (admin_id, user_id, role_id)
            )
            
        # Assigner le rôle Discord
        await self._assign_discord_role(user_id, role)
        
        # Envoyer notification
        await self._send_role_granted_notification(user_id, role)
        
        return True
        
    async def _grant_role(self, user_id: int, role_id: str, granted_by: int):
        """Accorde un rôle dans la DB"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
            
        if role_id not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_id)
            
        if self.db:
            await self.db.execute(
                """
                INSERT INTO user_marketing_roles (user_id, role_id, granted_by, granted_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                (user_id, role_id, granted_by)
            )
            
    async def _assign_discord_role(self, user_id: int, role: MarketingRole):
        """Assigne le rôle Discord"""
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if not member:
                continue
                
            # Chercher ou créer le rôle Discord
            discord_role = discord.utils.get(guild.roles, name=role.name)
            
            if not discord_role:
                try:
                    # Créer le rôle
                    perms = discord.Permissions()
                    for perm_name in role.permissions:
                        setattr(perms, perm_name, True)
                        
                    discord_role = await guild.create_role(
                        name=role.name,
                        color=discord.Color(role.color),
                        permissions=perms,
                        hoist=True,
                        mentionable=True
                    )
                except Exception as e:
                    logger.error(f"Erreur création rôle Discord: {e}")
                    continue
                    
            # Assigner à l'utilisateur
            try:
                await member.add_roles(discord_role, reason=f"Marketing role: {role.name}")
            except Exception as e:
                logger.error(f"Erreur assignation rôle: {e}")
                
    async def _send_role_granted_notification(self, user_id: int, role: MarketingRole):
        """Envoie une notification à l'utilisateur"""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                return
                
            embed = discord.Embed(
                title=f"🎉 Félicitations ! Tu es maintenant {role.name} !",
                description=role.description,
                color=discord.Color(role.color)
            )
            
            embed.add_field(
                name="✨ Tes avantages",
                value="\n".join([f"• {b}" for b in role.benefits]),
                inline=False
            )
            
            embed.set_footer(text="Merci pour ton engagement dans la communauté ! 💜")
            
            await user.send(embed=embed)
        except:
            pass
            
    async def revoke_role(self, user_id: int, role_id: str, admin_id: int, reason: str = ""):
        """Révoque un rôle"""
        role = self.roles.get(role_id)
        if not role:
            return False
            
        # Retirer de la DB
        if user_id in self.user_roles and role_id in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_id)
            
        if self.db:
            await self.db.execute(
                "DELETE FROM user_marketing_roles WHERE user_id = %s AND role_id = %s",
                (user_id, role_id)
            )
            
            await self.db.execute(
                """
                INSERT INTO marketing_role_revocations 
                (user_id, role_id, revoked_by, reason, revoked_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (user_id, role_id, admin_id, reason)
            )
            
        # Retirer le rôle Discord
        await self._remove_discord_role(user_id, role)
        
        return True
        
    async def _remove_discord_role(self, user_id: int, role: MarketingRole):
        """Retire le rôle Discord"""
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if not member:
                continue
                
            discord_role = discord.utils.get(guild.roles, name=role.name)
            if discord_role:
                try:
                    await member.remove_roles(discord_role)
                except:
                    pass
                    
    def get_role_info(self, role_id: str) -> Optional[Dict]:
        """Récupère les infos d'un rôle"""
        role = self.roles.get(role_id)
        if not role:
            return None
            
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "color": role.color,
            "benefits": role.benefits,
            "requirements": role.requirements,
            "max_slots": role.max_slots,
            "is_active": role.is_active
        }
        
    async def get_user_roles(self, user_id: int) -> List[Dict]:
        """Récupère les rôles d'un utilisateur"""
        if user_id not in self.user_roles:
            return []
            
        return [self.get_role_info(rid) for rid in self.user_roles[user_id] if self.get_role_info(rid)]
        
    async def get_role_stats(self, role_id: str) -> Dict:
        """Récupère les stats d'un rôle"""
        role = self.roles.get(role_id)
        if not role:
            return {}
            
        current_count = await self._get_role_count(role_id)
        
        return {
            "role_name": role.name,
            "current_count": current_count,
            "max_slots": role.max_slots,
            "slots_remaining": role.max_slots - current_count if role.max_slots else None,
            "is_active": role.is_active,
            "fill_percentage": (current_count / role.max_slots * 100) if role.max_slots else 0
        }
