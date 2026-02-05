"""
🦀 OPENCLAW MANAGER - Système de Gestion Automatisée
Gère automatiquement : rentabilité, sécurité, giveaways, promotions, événements
Intégration complète VM OpenClaw + Shellia AI
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class BusinessMetric(Enum):
    """Métriques business suivies"""
    MRR = "monthly_recurring_revenue"
    ARPU = "average_revenue_per_user"
    CONVERSION = "conversion_rate"
    CHURN = "churn_rate"
    LTV = "lifetime_value"
    CAC = "customer_acquisition_cost"
    ENGAGEMENT = "engagement_score"
    NPS = "net_promoter_score"


class PromotionType(Enum):
    """Types de promotions automatiques"""
    WELCOME = "welcome_offer"           # Offre de bienvenue
    WINBACK = "winback"                 # Récupération clients inactifs
    LOYALTY = "loyalty_reward"          # Récompense fidélité
    REFERRAL = "referral_boost"         # Boost parrainage
    MILESTONE = "milestone_bonus"       # Bonus paliers
    FLASH_SALE = "flash_sale"           # Vente flash
    ABANDONED_CART = "abandoned_cart"   # Panier abandonné
    UPSELL = "upsell_offer"             # Upsell automatique


@dataclass
class BusinessConfig:
    """Configuration business d'OpenClaw"""
    # Rentabilité
    target_mrr: float = 5000.0          # Objectif MRR (€)
    target_conversion: float = 0.05     # Objectif conversion (5%)
    max_cac: float = 50.0               # CAC maximum acceptable (€)
    min_ltv_cac_ratio: float = 3.0      # Ratio LTV/CAC minimum
    
    # Promotions
    enable_auto_promotions: bool = True
    max_discount_percent: int = 30      # Réduction max auto
    promotion_cooldown_days: int = 7    # Délai entre promos
    
    # Giveaways
    giveaway_roi_target: float = 2.0    # ROI minimum des giveaways
    max_giveaway_budget_percent: float = 0.10  # 10% du revenu mensuel
    
    # Fidélisation
    churn_threshold_days: int = 7       # Jours d'inactivité = churn risk
    winback_discount: int = 40          # Réduction winback (%)
    
    # Grades
    winner_plan_duration_days: int = 3  # Durée grade Winner offert
    winner_plan_type: str = "pro"       # Type de plan offert aux gagnants


@dataclass
class UserJourney:
    """Parcours utilisateur tracké"""
    user_id: int
    joined_at: datetime
    first_message_at: Optional[datetime] = None
    first_purchase_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    total_spent: float = 0.0
    messages_sent: int = 0
    engagement_score: float = 0.0
    churn_risk: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class Promotion:
    """Promotion active"""
    id: str
    type: PromotionType
    user_id: int
    discount_percent: int
    code: str
    valid_until: datetime
    max_uses: int = 1
    used_count: int = 0
    conditions: Dict = field(default_factory=dict)
    auto_generated: bool = True


@dataclass
class GiveawayROI:
    """ROI d'un giveaway"""
    giveaway_id: str
    cost: float                          # Coût total
    new_users: int                       # Nouveaux inscrits
    conversions: int                     # Conversions payantes
    revenue_generated: float             # Revenu généré
    engagement_increase: float           # +% d'engagement
    roi_ratio: float = 0.0               # ROI = Revenue / Coût
    
    def calculate(self):
        """Calcule le ROI"""
        if self.cost > 0:
            self.roi_ratio = self.revenue_generated / self.cost


class OpenClawManager:
    """
    🤖 Cerveau Business d'OpenClaw
    Gère automatiquement tout le système : rentabilité, sécurité, promotions, giveaways
    """
    
    def __init__(self, bot: commands.Bot, db=None):
        self.bot = bot
        self.db = db
        self.config = BusinessConfig()
        
        # Tracking
        self.user_journeys: Dict[int, UserJourney] = {}
        self.active_promotions: Dict[str, Promotion] = {}
        self.giveaway_rois: Dict[str, GiveawayROI] = {}
        self.metrics_history: List[Dict] = []
        
        # État
        self.monthly_revenue: float = 0.0
        self.monthly_expenses: float = 0.0
        self.active_users: int = 0
        self.paying_users: int = 0
        
        # Tâches
        self.analytics_task = None
        self.promotion_task = None
        self.winback_task = None
        
    async def setup(self):
        """Initialise OpenClaw Manager"""
        logger.info("🦀 Initialisation OpenClaw Manager...")
        
        # Charger les données
        await self._load_business_data()
        
        # Démarrer les tâches automatiques
        self.analytics_task = self.bot.loop.create_task(self._analytics_loop())
        self.promotion_task = self.bot.loop.create_task(self._promotion_engine_loop())
        self.winback_task = self.bot.loop.create_task(self._winback_loop())
        
        logger.info("✅ OpenClaw Manager actif - Mode business automatique")
        
    async def _load_business_data(self):
        """Charge les données business depuis la DB"""
        if not self.db:
            return
            
        try:
            # Charger métriques
            result = await self.db.fetch(
                "SELECT * FROM business_metrics ORDER BY recorded_at DESC LIMIT 30"
            )
            self.metrics_history = [dict(row) for row in result]
            
            # Charger promotions actives
            result = await self.db.fetch(
                "SELECT * FROM active_promotions WHERE valid_until > NOW()"
            )
            for row in result:
                promo = Promotion(
                    id=row['id'],
                    type=PromotionType(row['type']),
                    user_id=row['user_id'],
                    discount_percent=row['discount_percent'],
                    code=row['code'],
                    valid_until=row['valid_until'],
                    max_uses=row['max_uses'],
                    used_count=row['used_count']
                )
                self.active_promotions[promo.id] = promo
                
            # Calculer MRR actuel
            result = await self.db.fetch(
                "SELECT SUM(monthly_value) as mrr FROM user_subscriptions WHERE status = 'active'"
            )
            if result:
                self.monthly_revenue = result[0].get('mrr', 0) or 0
                
        except Exception as e:
            logger.error(f"Erreur chargement données business: {e}")
            
    # ============ ANALYTICS & RENTABILITÉ ============
    
    async def _analytics_loop(self):
        """Boucle d'analytics (toutes les heures)"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await self._update_business_metrics()
                await self._analyze_trends()
                await self._optimize_giveaway_strategy()
            except Exception as e:
                logger.error(f"Erreur analytics: {e}")
                
            await asyncio.sleep(3600)  # Toutes les heures
            
    async def _update_business_metrics(self):
        """Met à jour les métriques business"""
        if not self.db:
            return
            
        # Calculer les métriques
        metrics = await self._calculate_current_metrics()
        
        # Sauvegarder
        await self.db.execute(
            """
            INSERT INTO business_metrics 
            (mrr, arpu, conversion_rate, churn_rate, active_users, paying_users, recorded_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                metrics['mrr'],
                metrics['arpu'],
                metrics['conversion_rate'],
                metrics['churn_rate'],
                metrics['active_users'],
                metrics['paying_users']
            )
        )
        
        self.metrics_history.insert(0, metrics)
        if len(self.metrics_history) > 90:  # Garder 90 jours
            self.metrics_history = self.metrics_history[:90]
            
        logger.info(f"📊 Métriques mises à jour - MRR: €{metrics['mrr']:.2f}")
        
    async def _calculate_current_metrics(self) -> Dict:
        """Calcule les métriques actuelles"""
        if not self.db:
            return {}
            
        # MRR
        result = await self.db.fetch(
            "SELECT COALESCE(SUM(monthly_value), 0) as mrr FROM user_subscriptions WHERE status = 'active'"
        )
        mrr = result[0]['mrr'] if result else 0
        
        # Nombre d'utilisateurs
        result = await self.db.fetch("SELECT COUNT(*) as total FROM users")
        total_users = result[0]['total'] if result else 1
        
        result = await self.db.fetch(
            "SELECT COUNT(*) as paying FROM users WHERE plan IN ('pro', 'ultra')"
        )
        paying = result[0]['paying'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COUNT(*) as active FROM users WHERE last_active_at > NOW() - INTERVAL '7 days'"
        )
        active = result[0]['active'] if result else 0
        
        # Calculs
        arpu = mrr / paying if paying > 0 else 0
        conversion_rate = paying / total_users if total_users > 0 else 0
        
        # Churn (utilisateurs inactifs depuis 30j qui étaient payants)
        result = await self.db.fetch(
            """
            SELECT COUNT(*) as churned 
            FROM user_subscriptions 
            WHERE status = 'cancelled' 
            AND cancelled_at > NOW() - INTERVAL '30 days'
            """
        )
        churned = result[0]['churned'] if result else 0
        churn_rate = churned / paying if paying > 0 else 0
        
        return {
            'mrr': mrr,
            'arpu': arpu,
            'conversion_rate': conversion_rate,
            'churn_rate': churn_rate,
            'active_users': active,
            'paying_users': paying,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def _analyze_trends(self):
        """Analyse les tendances et ajuste les stratégies"""
        if len(self.metrics_history) < 7:
            return
            
        # Calculer la tendance MRR (7 derniers jours)
        recent_mrr = [m['mrr'] for m in self.metrics_history[:7]]
        mrr_trend = (recent_mrr[0] - recent_mrr[-1]) / recent_mrr[-1] if recent_mrr[-1] > 0 else 0
        
        # Détecter les problèmes
        if mrr_trend < -0.10:  # -10% en une semaine
            logger.warning("📉 Alerte: MRR en baisse de 10%+")
            await self._trigger_growth_recovery()
            
        # Conversion rate faible
        current_metrics = self.metrics_history[0]
        if current_metrics.get('conversion_rate', 0) < 0.03:  # < 3%
            logger.warning("📉 Conversion rate faible (< 3%)")
            await self._boost_conversion()
            
    # ============ MOTEUR DE PROMOTIONS ============
    
    async def _promotion_engine_loop(self):
        """Moteur de promotions automatiques"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await self._process_promotion_triggers()
            except Exception as e:
                logger.error(f"Erreur moteur promotions: {e}")
                
            await asyncio.sleep(1800)  # Toutes les 30 minutes
            
    async def _process_promotion_triggers(self):
        """Traite les déclencheurs de promotions"""
        if not self.config.enable_auto_promotions:
            return
            
        # 1. Nouveaux utilisateurs (offre de bienvenue)
        await self._process_welcome_offers()
        
        # 2. Panier abandonné
        await self._process_abandoned_carts()
        
        # 3. Upsell opportunités
        await self._process_upsell_opportunities()
        
    async def _process_welcome_offers(self):
        """Offres de bienvenue pour nouveaux utilisateurs"""
        if not self.db:
            return
            
        # Utilisateurs de moins de 24h qui n'ont pas encore eu d'offre
        result = await self.db.fetch(
            """
            SELECT user_id FROM users 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            AND user_id NOT IN (
                SELECT user_id FROM user_promotions WHERE type = 'welcome_offer'
            )
            LIMIT 10
            """
        )
        
        for row in result:
            user_id = row['user_id']
            
            # Créer une offre personnalisée
            promo = await self._create_promotion(
                user_id=user_id,
                promo_type=PromotionType.WELCOME,
                discount_percent=20,  # 20% de bienvenue
                duration_hours=48,
                message="🎉 Bienvenue ! Profite de 20% de réduction sur ton premier abonnement !"
            )
            
            # Envoyer le message
            await self._send_promotion_message(user_id, promo)
            
    async def _process_abandoned_carts(self):
        """Récupération des paniers abandonnés"""
        if not self.db:
            return
            
        # Paniers abandonnés depuis plus de 1h
        result = await self.db.fetch(
            """
            SELECT user_id FROM carts 
            WHERE updated_at < NOW() - INTERVAL '1 hour'
            AND updated_at > NOW() - INTERVAL '24 hours'
            AND status = 'active'
            AND user_id NOT IN (
                SELECT user_id FROM user_promotions 
                WHERE type = 'abandoned_cart' AND created_at > NOW() - INTERVAL '7 days'
            )
            LIMIT 5
            """
        )
        
        for row in result:
            user_id = row['user_id']
            
            promo = await self._create_promotion(
                user_id=user_id,
                promo_type=PromotionType.ABANDONED_CART,
                discount_percent=15,
                duration_hours=24,
                message="👋 Tu as oublié quelque chose dans ton panier ! 15% de réduction pendant 24h !"
            )
            
            await self._send_promotion_message(user_id, promo)
            
    async def _process_upsell_opportunities(self):
        """Opportunités d'upsell"""
        if not self.db:
            return
            
        # Utilisateurs Pro depuis plus de 30j avec bon engagement
        result = await self.db.fetch(
            """
            SELECT u.user_id, s.started_at
            FROM users u
            JOIN user_subscriptions s ON u.user_id = s.user_id
            WHERE s.plan = 'pro'
            AND s.status = 'active'
            AND s.started_at < NOW() - INTERVAL '30 days'
            AND u.messages_sent > 500
            AND u.user_id NOT IN (
                SELECT user_id FROM user_promotions 
                WHERE type = 'upsell_offer' AND created_at > NOW() - INTERVAL '30 days'
            )
            LIMIT 3
            """
        )
        
        for row in result:
            user_id = row['user_id']
            
            promo = await self._create_promotion(
                user_id=user_id,
                promo_type=PromotionType.UPSELL,
                discount_percent=25,  # Grosse réduction pour upsell
                duration_hours=72,
                message="🚀 Tu es un utilisateur actif ! Passe à Ultra avec 25% de réduction !"
            )
            
            await self._send_promotion_message(user_id, promo)
            
    async def _create_promotion(
        self,
        user_id: int,
        promo_type: PromotionType,
        discount_percent: int,
        duration_hours: int,
        message: str
    ) -> Promotion:
        """Crée une promotion"""
        import uuid
        
        promo_id = str(uuid.uuid4())[:8]
        code = f"{promo_type.value.upper()}{random.randint(1000, 9999)}"
        
        promo = Promotion(
            id=promo_id,
            type=promo_type,
            user_id=user_id,
            discount_percent=discount_percent,
            code=code,
            valid_until=datetime.utcnow() + timedelta(hours=duration_hours),
            max_uses=1,
            used_count=0,
            conditions={'message': message}
        )
        
        self.active_promotions[promo_id] = promo
        
        # Sauvegarder
        if self.db:
            await self.db.execute(
                """
                INSERT INTO user_promotions 
                (id, user_id, type, discount_percent, code, valid_until, max_uses, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (promo_id, user_id, promo_type.value, discount_percent, code, 
                 promo.valid_until, 1, message)
            )
            
        return promo
        
    async def _send_promotion_message(self, user_id: int, promo: Promotion):
        """Envoie un message de promotion"""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                return
                
            embed = discord.Embed(
                title="🎁 Une offre spéciale pour toi !",
                description=promo.conditions.get('message', ''),
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="Code promo",
                value=f"`{promo.code}`",
                inline=False
            )
            
            embed.add_field(
                name="Réduction",
                value=f"**{promo.discount_percent}%**",
                inline=True
            )
            
            embed.add_field(
                name="Valide jusqu'au",
                value=f"<t:{int(promo.valid_until.timestamp())}:F>",
                inline=True
            )
            
            embed.set_footer(text="Offre personnelle - À ne pas partager")
            
            await user.send(embed=embed)
            logger.info(f"📧 Promotion envoyée à {user_id}: {promo.type.value}")
            
        except Exception as e:
            logger.error(f"Erreur envoi promotion à {user_id}: {e}")
            
    # ============ WINBACK (RÉCUPÉRATION CLIENTS) ============
    
    async def _winback_loop(self):
        """Boucle de récupération des clients inactifs"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await self._process_churn_risk_users()
            except Exception as e:
                logger.error(f"Erreur winback: {e}")
                
            await asyncio.sleep(86400)  # Une fois par jour
            
    async def _process_churn_risk_users(self):
        """Traite les utilisateurs à risque de churn"""
        if not self.db:
            return
            
        # Utilisateurs inactifs depuis 7+ jours qui étaient payants
        result = await self.db.fetch(
            """
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN user_subscriptions s ON u.user_id = s.user_id
            WHERE u.last_active_at < NOW() - INTERVAL '7 days'
            AND s.plan IN ('pro', 'ultra')
            AND s.status = 'active'
            AND u.user_id NOT IN (
                SELECT user_id FROM user_promotions 
                WHERE type = 'winback' AND created_at > NOW() - INTERVAL '30 days'
            )
            LIMIT 10
            """
        )
        
        for row in result:
            user_id = row['user_id']
            
            # Grosse réduction pour winback
            promo = await self._create_promotion(
                user_id=user_id,
                promo_type=PromotionType.WINBACK,
                discount_percent=self.config.winback_discount,
                duration_hours=72,
                message="😢 On te manque ? Reviens avec 40% de réduction sur ta prochaine facture !"
            )
            
            await self._send_promotion_message(user_id, promo)
            
            # Marquer comme risque churn
            if user_id in self.user_journeys:
                self.user_journeys[user_id].churn_risk = True
                
        logger.info(f"🔄 {len(result)} utilisateurs winback traités")
        
    # ============ GIVEAWAYS OPTIMISÉS ============
    
    async def calculate_optimal_giveaway(
        self,
        current_members: int,
        next_milestone: int
    ) -> Tuple[bool, Dict]:
        """
        Calcule si un giveaway est rentable et quelles récompenses offrir
        
        Returns:
            (should_run, config)
        """
        # Analyser les métriques actuelles
        if not self.metrics_history:
            return False, {}
            
        current = self.metrics_history[0]
        
        # Calculer le budget disponible (10% du MRR)
        available_budget = current.get('mrr', 0) * self.config.max_giveaway_budget_percent
        
        # Estimer le ROI
        members_needed = next_milestone - current_members
        
        # Si on a besoin de beaucoup de membres, faire un gros giveaway
        if members_needed > 50:
            recommended_value = min(50, available_budget / 10)  # Max 50€ équivalent
            winners = 5
        elif members_needed > 20:
            recommended_value = min(30, available_budget / 15)
            winners = 3
        else:
            recommended_value = min(20, available_budget / 20)
            winners = 2
            
        # Calculer ROI estimé
        # Hypothèse: 5% des nouveaux membres convertissent en payant
        estimated_new_members = members_needed
        estimated_conversions = estimated_new_members * 0.05
        estimated_revenue = estimated_conversions * current.get('arpu', 10)
        
        total_cost = recommended_value * winners
        roi = estimated_revenue / total_cost if total_cost > 0 else 0
        
        # Décider si on lance le giveaway
        should_run = roi >= self.config.giveaway_roi_target
        
        config = {
            'should_run': should_run,
            'roi_estimate': roi,
            'budget': total_cost,
            'winners': winners,
            'currency_reward': int(recommended_value * 100),  # Conversion en coins
            'duration_hours': 48 if members_needed > 30 else 24,
            'strategy': 'aggressive' if members_needed > 50 else 'standard'
        }
        
        return should_run, config
        
    async def on_giveaway_ended(self, giveaway_id: str, stats: Dict):
        """Appelé quand un giveaway se termine - calcule le vrai ROI"""
        # Calculer les vraies stats
        roi_data = GiveawayROI(
            giveaway_id=giveaway_id,
            cost=stats.get('total_cost', 0),
            new_users=stats.get('new_members', 0),
            conversions=stats.get('conversions', 0),
            revenue_generated=stats.get('revenue', 0),
            engagement_increase=stats.get('engagement_boost', 0)
        )
        roi_data.calculate()
        
        self.giveaway_rois[giveaway_id] = roi_data
        
        # Sauvegarder
        if self.db:
            await self.db.execute(
                """
                INSERT INTO giveaway_roi_analysis 
                (giveaway_id, cost, new_users, conversions, revenue, roi_ratio, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (giveaway_id, roi_data.cost, roi_data.new_users, 
                 roi_data.conversions, roi_data.revenue_generated, roi_data.roi_ratio)
            )
            
        logger.info(f"📊 ROI Giveaway {giveaway_id}: {roi_data.roi_ratio:.2f}x")
        
        # Ajuster la stratégie future si besoin
        if roi_data.roi_ratio < self.config.giveaway_roi_target:
            logger.warning(f"📉 Giveaway {giveaway_id} sous-performant (ROI: {roi_data.roi_ratio:.2f})")
            await self._adjust_giveaway_strategy()
            
    async def _adjust_giveaway_strategy(self):
        """Ajuste la stratégie des giveaways basé sur les performances"""
        if len(self.giveaway_rois) < 3:
            return
            
        # Calculer ROI moyen
        avg_roi = sum(r.roi_ratio for r in self.giveaway_rois.values()) / len(self.giveaway_rois)
        
        if avg_roi < self.config.giveaway_roi_target:
            logger.info("🔧 Ajustement stratégie giveaways: réduction des coûts")
            # Réduire les récompenses futures de 20%
            self.config.max_giveaway_budget_percent *= 0.8
            
    # ============ GESTION DES GRADES ============
    
    async def assign_winner_grade(
        self, 
        user_id: int, 
        giveaway_id: str,
        guild: discord.Guild
    ):
        """
        Assigne le grade Winner et les avantages associés
        """
        # 1. Créer ou récupérer le rôle Winner
        winner_role = await self._get_or_create_winner_role(guild)
        
        if winner_role:
            member = guild.get_member(user_id)
            if member:
                await member.add_roles(winner_role, reason=f"Gagnant giveaway {giveaway_id}")
                
        # 2. Offrir le plan temporaire
        plan_end = datetime.utcnow() + timedelta(days=self.config.winner_plan_duration_days)
        
        if self.db:
            await self.db.execute(
                """
                INSERT INTO winner_rewards 
                (user_id, giveaway_id, plan_type, plan_started_at, plan_ends_at, status)
                VALUES (%s, %s, %s, NOW(), %s, 'active')
                ON CONFLICT (user_id, giveaway_id) DO UPDATE SET
                    plan_ends_at = EXCLUDED.plan_ends_at
                """,
                (user_id, giveaway_id, self.config.winner_plan_type, plan_end)
            )
            
            # Mettre à jour l'utilisateur
            await self.db.execute(
                "UPDATE users SET plan = %s, plan_expires_at = %s WHERE user_id = %s",
                (self.config.winner_plan_type, plan_end, user_id)
            )
            
        # 3. Envoyer message de félicitations avec infos
        await self._send_winner_notification(user_id, giveaway_id, plan_end)
        
        logger.info(f"🏆 Grade Winner assigné à {user_id} pour giveaway {giveaway_id}")
        
    async def _get_or_create_winner_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        """Récupère ou crée le rôle Winner"""
        role_name = "🏆 Winner"
        
        # Chercher le rôle existant
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            return role
            
        # Créer le rôle
        try:
            role = await guild.create_role(
                name=role_name,
                color=discord.Color.gold(),
                hoist=True,  # Affiché séparément
                mentionable=True,
                permissions=discord.Permissions(
                    send_messages=True,
                    read_messages=True,
                    embed_links=True,
                    attach_files=True,
                    use_external_emojis=True,
                    add_reactions=True
                )
            )
            
            # Positionner au-dessus des rôles basiques
            # Mais en dessous des rôles admin/mod
            
            logger.info(f"✅ Rôle {role_name} créé sur {guild.name}")
            return role
            
        except Exception as e:
            logger.error(f"Erreur création rôle Winner: {e}")
            return None
            
    async def _send_winner_notification(self, user_id: int, giveaway_id: str, plan_end: datetime):
        """Envoie la notification au gagnant"""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                return
                
            embed = discord.Embed(
                title="🎉 Félicitations ! Tu es un Winner !",
                description=(
                    f"Tu as remporté le giveaway ! En plus de tes coins, tu reçois :\n\n"
                    f"🏆 **Grade Winner** pendant {self.config.winner_plan_duration_days} jours\n"
                    f"✨ **Accès Pro** gratuit pendant cette période\n"
                    f"🎁 **Badge exclusif** sur ton profil\n\n"
                    f"Profite de toutes les fonctionnalités Pro jusqu'au <t:{int(plan_end.timestamp())}:F> !"
                ),
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="💡 Conseil",
                value="Si tu aimes l'expérience Pro, tu peux l'acheter à tout moment avec ton code de réduction personnel !",
                inline=False
            )
            
            await user.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur notification winner {user_id}: {e}")
            
    async def remove_expired_winner_grades(self):
        """Retire les grades Winner expirés"""
        if not self.db:
            return
            
        # Trouver les winners expirés
        result = await self.db.fetch(
            """
            SELECT user_id, giveaway_id FROM winner_rewards
            WHERE plan_ends_at < NOW()
            AND status = 'active'
            """
        )
        
        for row in result:
            user_id = row['user_id']
            giveaway_id = row['giveaway_id']
            
            # Mettre à jour le statut
            await self.db.execute(
                "UPDATE winner_rewards SET status = 'expired' WHERE user_id = %s AND giveaway_id = %s",
                (user_id, giveaway_id)
            )
            
            # Repasser à Free si pas d'autre abonnement
            await self.db.execute(
                """
                UPDATE users SET plan = 'free', plan_expires_at = NULL
                WHERE user_id = %s 
                AND plan = %s
                AND user_id NOT IN (
                    SELECT user_id FROM user_subscriptions 
                    WHERE status = 'active' AND expires_at > NOW()
                )
                """,
                (user_id, self.config.winner_plan_type)
            )
            
            # Notifier l'utilisateur
            try:
                user = self.bot.get_user(user_id)
                if user:
                    embed = discord.Embed(
                        title="⏰ Ton grade Winner expire aujourd'hui",
                        description=(
                            "Ton accès Pro gratuit se termine.\n\n"
                            "Si tu veux continuer à profiter de toutes les fonctionnalités, "
                            "passe à un abonnement payant !"
                        ),
                        color=discord.Color.orange()
                    )
                    await user.send(embed=embed)
            except:
                pass
                
        if result:
            logger.info(f"🧹 {len(result)} grades Winner expirés retirés")
            
    # ============ ÉVÉNEMENTS AUTOMATIQUES ============
    
    async def check_and_trigger_events(self, guild: discord.Guild):
        """Vérifie et déclenche des événements automatiques"""
        current_metrics = self.metrics_history[0] if self.metrics_history else {}
        
        # Événement: Objectif MRR atteint
        if current_metrics.get('mrr', 0) >= self.config.target_mrr:
            await self._trigger_milestone_event(guild, "mrr_target", current_metrics['mrr'])
            
        # Événement: Record de conversion
        if current_metrics.get('conversion_rate', 0) >= self.config.target_conversion:
            await self._trigger_milestone_event(guild, "conversion_record", current_metrics['conversion_rate'])
            
    async def _trigger_milestone_event(self, guild: discord.Guild, event_type: str, value: float):
        """Déclenche un événement de milestone"""
        # Vérifier si déjà célébré récemment
        if self.db:
            result = await self.db.fetch(
                """
                SELECT 1 FROM milestone_events 
                WHERE event_type = %s AND guild_id = %s AND created_at > NOW() - INTERVAL '7 days'
                """,
                (event_type, guild.id)
            )
            if result:
                return
                
        # Créer l'événement
        messages = {
            "mrr_target": f"🎯 OBJECTIF ATTEINT ! MRR de €{value:.2f} !",
            "conversion_record": f"📈 NOUVEAU RECORD ! Conversion à {value*100:.1f}% !"
        }
        
        embed = discord.Embed(
            title="🎉 ÉVÉNEMENT SPÉCIAL",
            description=messages.get(event_type, "Objectif atteint !"),
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🎁 Récompense",
            value="Un giveaway spécial va être lancé dans 24h !",
            inline=False
        )
        
        # Envoyer dans le canal général
        general = discord.utils.get(guild.text_channels, name='général') or guild.text_channels[0]
        await general.send(embed=embed)
        
        # Programmer un giveaway spécial
        # (implémentation dans le giveaway_manager)
        
        # Sauvegarder
        if self.db:
            await self.db.execute(
                "INSERT INTO milestone_events (guild_id, event_type, value) VALUES (%s, %s, %s)",
                (guild.id, event_type, value)
            )
            
    # ============ COMMANDES ADMIN OPENCLOW ============
    
    async def get_business_report(self) -> discord.Embed:
        """Génère un rapport business complet"""
        if not self.metrics_history:
            return discord.Embed(title="Pas encore de données")
            
        current = self.metrics_history[0]
        
        embed = discord.Embed(
            title="📊 Rapport Business OpenClaw",
            description=f"Mise à jour: <t:{int(datetime.utcnow().timestamp())}:R>",
            color=discord.Color.blue()
        )
        
        # KPIs principaux
        embed.add_field(
            name="💰 MRR",
            value=f"€{current.get('mrr', 0):.2f} / €{self.config.target_mrr:.0f}",
            inline=True
        )
        
        embed.add_field(
            name="📈 Conversion",
            value=f"{current.get('conversion_rate', 0)*100:.1f}% / {self.config.target_conversion*100:.0f}%",
            inline=True
        )
        
        embed.add_field(
            name="👥 Utilisateurs",
            value=f"{current.get('active_users', 0)} actifs\n{current.get('paying_users', 0)} payants",
            inline=True
        )
        
        # ARPU et Churn
        embed.add_field(
            name="💵 ARPU",
            value=f"€{current.get('arpu', 0):.2f}",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Churn",
            value=f"{current.get('churn_rate', 0)*100:.1f}%",
            inline=True
        )
        
        # Promotions actives
        active_promos = len(self.active_promotions)
        embed.add_field(
            name="🎁 Promotions",
            value=f"{active_promos} actives",
            inline=True
        )
        
        # Recommandations
        recommendations = []
        
        if current.get('conversion_rate', 0) < self.config.target_conversion:
            recommendations.append("📉 Augmenter les promotions de conversion")
            
        if current.get('churn_rate', 0) > 0.05:
            recommendations.append("🔄 Renforcer le programme winback")
            
        if current.get('mrr', 0) < self.config.target_mrr * 0.8:
            recommendations.append("🚀 Lancer une campagne de growth")
            
        if recommendations:
            embed.add_field(
                name="💡 Recommandations",
                value="\n".join(recommendations),
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Statut",
                value="Tous les indicateurs sont bons !",
                inline=False
            )
            
        return embed
        
    async def adjust_config(self, **kwargs):
        """Ajuste la configuration business"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"🔧 Config ajustée: {key} = {value}")
                
    # ============ DASHBOARD DATA ============
    
    async def get_dashboard_data(self) -> Dict:
        """Récupère les données pour le dashboard OpenClaw"""
        current = self.metrics_history[0] if self.metrics_history else {}
        
        return {
            'metrics': {
                'mrr': current.get('mrr', 0),
                'target_mrr': self.config.target_mrr,
                'mrr_progress': (current.get('mrr', 0) / self.config.target_mrr * 100) if self.config.target_mrr > 0 else 0,
                'conversion_rate': current.get('conversion_rate', 0) * 100,
                'target_conversion': self.config.target_conversion * 100,
                'active_users': current.get('active_users', 0),
                'paying_users': current.get('paying_users', 0),
                'churn_rate': current.get('churn_rate', 0) * 100,
                'arpu': current.get('arpu', 0)
            },
            'promotions': {
                'active': len(self.active_promotions),
                'by_type': defaultdict(int)
            },
            'giveaways': {
                'total_roi': len(self.giveaway_rois),
                'avg_roi': sum(r.roi_ratio for r in self.giveaway_rois.values()) / len(self.giveaway_rois) if self.giveaway_rois else 0
            },
            'config': {
                'auto_promotions': self.config.enable_auto_promotions,
                'max_discount': self.config.max_discount_percent,
                'winner_duration': self.config.winner_plan_duration_days
            }
        }
