"""
🤝 AFFILIATE MANAGER - Système d'Affiliation Complet
Gestion des affiliés, codes promo, commissions et paiements
"""

import discord
from discord.ext import commands, tasks
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
import random
import string


class AffiliateTier(Enum):
    """Tiers d'affiliation avec commissions croissantes"""
    BRONZE = "bronze"      # 0-9 conversions: 15%
    SILVER = "silver"      # 10-49 conversions: 20%
    GOLD = "gold"          # 50-99 conversions: 25%
    PLATINUM = "platinum"  # 100-499 conversions: 30%
    DIAMOND = "diamond"    # 500+ conversions: 35%


TIER_CONFIG = {
    AffiliateTier.BRONZE: {
        "min_conversions": 0,
        "commission_percent": 15,
        "name": "Bronze",
        "emoji": "🥉",
        "color": 0xcd7f32
    },
    AffiliateTier.SILVER: {
        "min_conversions": 10,
        "commission_percent": 20,
        "name": "Silver",
        "emoji": "🥈",
        "color": 0xc0c0c0
    },
    AffiliateTier.GOLD: {
        "min_conversions": 50,
        "commission_percent": 25,
        "name": "Gold",
        "emoji": "🥇",
        "color": 0xffd700
    },
    AffiliateTier.PLATINUM: {
        "min_conversions": 100,
        "commission_percent": 30,
        "name": "Platinum",
        "emoji": "💎",
        "color": 0xe5e4e2
    },
    AffiliateTier.DIAMOND: {
        "min_conversions": 500,
        "commission_percent": 35,
        "name": "Diamond",
        "emoji": "👑",
        "color": 0xb9f2ff
    }
}


@dataclass
class Affiliate:
    """Représentation d'un affilié"""
    user_id: int
    username: str
    code: str
    tier: AffiliateTier
    conversions: int = 0
    revenue_generated: float = 0.0
    commission_earned: float = 0.0
    commission_paid: float = 0.0
    commission_pending: float = 0.0
    is_active: bool = True
    is_vip: bool = False
    custom_commission: Optional[int] = None
    created_at: str = ""
    last_conversion: Optional[str] = None
    payout_method: str = "paypal"  # paypal, bank, crypto
    payout_email: Optional[str] = None
    
    def get_commission_percent(self) -> int:
        """Retourne le pourcentage de commission"""
        if self.custom_commission:
            return self.custom_commission
        return TIER_CONFIG[self.tier]["commission_percent"]
    
    def get_next_tier(self) -> Optional[AffiliateTier]:
        """Retourne le prochain tier à atteindre"""
        tiers = list(AffiliateTier)
        current_index = tiers.index(self.tier)
        if current_index < len(tiers) - 1:
            return tiers[current_index + 1]
        return None
    
    def get_next_tier_progress(self) -> dict:
        """Retourne la progression vers le prochain tier"""
        next_tier = self.get_next_tier()
        if not next_tier:
            return {"has_next": False}
        
        next_config = TIER_CONFIG[next_tier]
        needed = next_config["min_conversions"] - self.conversions
        progress = (self.conversions / next_config["min_conversions"]) * 100
        
        return {
            "has_next": True,
            "tier": next_tier.value,
            "name": next_config["name"],
            "needed": needed,
            "progress": min(progress, 100)
        }
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'code': self.code,
            'tier': self.tier.value,
            'conversions': self.conversions,
            'revenue_generated': self.revenue_generated,
            'commission_earned': self.commission_earned,
            'commission_paid': self.commission_paid,
            'commission_pending': self.commission_pending,
            'is_active': self.is_active,
            'is_vip': self.is_vip,
            'custom_commission': self.custom_commission,
            'created_at': self.created_at,
            'last_conversion': self.last_conversion,
            'payout_method': self.payout_method,
            'payout_email': self.payout_email
        }


@dataclass
class Conversion:
    """Une conversion (vente via affiliation)"""
    id: str
    affiliate_id: int
    customer_id: int
    order_id: str
    amount: float
    commission: float
    status: str  # pending, validated, cancelled
    created_at: str
    validated_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'affiliate_id': self.affiliate_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'commission': self.commission,
            'status': self.status,
            'created_at': self.created_at,
            'validated_at': self.validated_at
        }


@dataclass
class Payout:
    """Une demande de paiement"""
    id: str
    affiliate_id: int
    amount: float
    status: str  # pending, processing, paid, rejected
    method: str
    created_at: str
    paid_at: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'affiliate_id': self.affiliate_id,
            'amount': self.amount,
            'status': self.status,
            'method': self.method,
            'created_at': self.created_at,
            'paid_at': self.paid_at,
            'transaction_id': self.transaction_id,
            'notes': self.notes
        }


class AffiliateManager:
    """
    🤝 Gestionnaire d'Affiliation Complet
    """
    
    def __init__(self, bot: commands.Bot, db=None, stripe_manager=None):
        self.bot = bot
        self.db = db
        self.stripe_manager = stripe_manager
        self.affiliates: Dict[int, Affiliate] = {}
        self.conversions: Dict[str, Conversion] = {}
        self.payouts: Dict[str, Payout] = {}
        
        # Configuration
        self.min_payout = 50.0  # €
        self.validation_days = 30
        self.cookie_days = 30
        self.auto_approve = True
        
    async def setup(self):
        """Initialise le gestionnaire d'affiliation"""
        if self.db:
            await self._load_affiliates_from_db()
        
        # Démarrer les tâches périodiques
        self.check_validation_period.start()
        self.process_auto_payouts.start()
        print("✅ AffiliateManager initialisé")
        
    async def _load_affiliates_from_db(self):
        """Charge les affiliés depuis la DB"""
        try:
            # Affiliés
            result = await self.db.fetch("SELECT * FROM affiliates")
            for row in result:
                affiliate = Affiliate(
                    user_id=row['user_id'],
                    username=row['username'],
                    code=row['code'],
                    tier=AffiliateTier(row['tier']),
                    conversions=row.get('conversions', 0),
                    revenue_generated=row.get('revenue_generated', 0.0),
                    commission_earned=row.get('commission_earned', 0.0),
                    commission_paid=row.get('commission_paid', 0.0),
                    commission_pending=row.get('commission_pending', 0.0),
                    is_active=row.get('is_active', True),
                    is_vip=row.get('is_vip', False),
                    custom_commission=row.get('custom_commission'),
                    created_at=row['created_at'],
                    last_conversion=row.get('last_conversion'),
                    payout_method=row.get('payout_method', 'paypal'),
                    payout_email=row.get('payout_email')
                )
                self.affiliates[affiliate.user_id] = affiliate
                
            # Conversions
            conv_result = await self.db.fetch("SELECT * FROM conversions")
            for row in conv_result:
                conv = Conversion(
                    id=row['id'],
                    affiliate_id=row['affiliate_id'],
                    customer_id=row['customer_id'],
                    order_id=row['order_id'],
                    amount=row['amount'],
                    commission=row['commission'],
                    status=row['status'],
                    created_at=row['created_at'],
                    validated_at=row.get('validated_at')
                )
                self.conversions[conv.id] = conv
                
            # Payouts
            payout_result = await self.db.fetch("SELECT * FROM payouts ORDER BY created_at DESC")
            for row in payout_result:
                payout = Payout(
                    id=row['id'],
                    affiliate_id=row['affiliate_id'],
                    amount=row['amount'],
                    status=row['status'],
                    method=row['method'],
                    created_at=row['created_at'],
                    paid_at=row.get('paid_at'),
                    transaction_id=row.get('transaction_id'),
                    notes=row.get('notes')
                )
                self.payouts[payout.id] = payout
                
        except Exception as e:
            print(f"⚠️ Erreur chargement affiliés: {e}")
            
    def generate_code(self, username: str) -> str:
        """Génère un code affilié unique"""
        base = username.upper()[:6]
        random_suffix = ''.join(random.choices(string.digits, k=2))
        return f"{base}{random_suffix}"
        
    async def create_affiliate(self, user_id: int, username: str, 
                              custom_code: Optional[str] = None,
                              custom_commission: Optional[int] = None,
                              is_vip: bool = False) -> Affiliate:
        """Crée un nouvel affilié"""
        # Vérifier si déjà affilié
        if user_id in self.affiliates:
            return self.affiliates[user_id]
            
        # Générer le code
        code = custom_code or self.generate_code(username)
        
        # Vérifier unicité du code
        while any(a.code == code for a in self.affiliates.values()):
            code = self.generate_code(username + str(random.randint(1, 99)))
            
        affiliate = Affiliate(
            user_id=user_id,
            username=username,
            code=code,
            tier=AffiliateTier.BRONZE,
            custom_commission=custom_commission,
            is_vip=is_vip,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Sauvegarder en DB
        if self.db:
            await self.db.execute(
                """
                INSERT INTO affiliates 
                (user_id, username, code, tier, custom_commission, is_vip, created_at, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
                """,
                affiliate.user_id, affiliate.username, affiliate.code,
                affiliate.tier.value, affiliate.custom_commission, affiliate.is_vip,
                affiliate.created_at
            )
            
        self.affiliates[user_id] = affiliate
        
        # Envoyer notification DM
        await self._notify_new_affiliate(affiliate)
        
        return affiliate
        
    async def _notify_new_affiliate(self, affiliate: Affiliate):
        """Notifie un nouvel affilié"""
        try:
            user = await self.bot.fetch_user(affiliate.user_id)
            if user:
                embed = discord.Embed(
                    title="🎉 Bienvenue dans le Programme d'Affiliation !",
                    description=f"Félicitations **{affiliate.username}** !\n\n"
                               f"Vous faites maintenant partie de nos affiliés.",
                    color=TIER_CONFIG[affiliate.tier]["color"]
                )
                embed.add_field(
                    name="🎫 Votre Code",
                    value=f"`{affiliate.code}`",
                    inline=False
                )
                embed.add_field(
                    name="💰 Commission",
                    value=f"**{affiliate.get_commission_percent()}%** sur chaque vente",
                    inline=True
                )
                embed.add_field(
                    name="🎯 Objectif",
                    value=f"{TIER_CONFIG[AffiliateTier.SILVER]['min_conversions']} conversions pour passer Silver",
                    inline=True
                )
                embed.add_field(
                    name="📊 Dashboard",
                    value="[Voir mes stats](https://shellia.ai/affiliate/dashboard)",
                    inline=False
                )
                
                await user.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Erreur notification affilié: {e}")
            
    async def track_conversion(self, code: str, customer_id: int, order_id: str, 
                              amount: float, order_type: str = "subscription") -> Optional[Conversion]:
        """Track une conversion (vente via un code affilié)"""
        # Trouver l'affilié
        affiliate = None
        for a in self.affiliates.values():
            if a.code.upper() == code.upper() and a.is_active:
                affiliate = a
                break
                
        if not affiliate:
            return None
            
        # Vérifier auto-parrainage
        if customer_id == affiliate.user_id:
            return None
            
        # Calculer commission
        commission_rate = affiliate.get_commission_percent() / 100
        commission = amount * commission_rate
        
        # Créer la conversion
        conversion = Conversion(
            id=str(uuid.uuid4())[:12],
            affiliate_id=affiliate.user_id,
            customer_id=customer_id,
            order_id=order_id,
            amount=amount,
            commission=commission,
            status="pending",
            created_at=datetime.utcnow().isoformat()
        )
        
        # Sauvegarder
        if self.db:
            await self.db.execute(
                """
                INSERT INTO conversions 
                (id, affiliate_id, customer_id, order_id, amount, commission, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                conversion.id, conversion.affiliate_id, conversion.customer_id,
                conversion.order_id, conversion.amount, conversion.commission,
                conversion.status, conversion.created_at
            )
            
        self.conversions[conversion.id] = conversion
        
        # Mettre à jour les stats de l'affilié
        affiliate.conversions += 1
        affiliate.revenue_generated += amount
        affiliate.commission_pending += commission
        affiliate.last_conversion = datetime.utcnow().isoformat()
        
        # Vérifier changement de tier
        await self._check_tier_upgrade(affiliate)
        
        # Sauvegarder les changements
        await self._save_affiliate_stats(affiliate)
        
        # Notifier l'affilié
        await self._notify_conversion(affiliate, conversion)
        
        return conversion
        
    async def _check_tier_upgrade(self, affiliate: Affiliate):
        """Vérifie si l'affilié doit changer de tier"""
        current_tier = affiliate.tier
        new_tier = current_tier
        
        # Vérifier tous les tiers supérieurs
        for tier in AffiliateTier:
            config = TIER_CONFIG[tier]
            if affiliate.conversions >= config["min_conversions"]:
                new_tier = tier
                
        if new_tier != current_tier:
            affiliate.tier = new_tier
            await self._notify_tier_upgrade(affiliate, current_tier, new_tier)
            
    async def _notify_tier_upgrade(self, affiliate: Affiliate, old_tier: AffiliateTier, new_tier: AffiliateTier):
        """Notifie d'un changement de tier"""
        try:
            user = await self.bot.fetch_user(affiliate.user_id)
            if user:
                old_config = TIER_CONFIG[old_tier]
                new_config = TIER_CONFIG[new_tier]
                
                embed = discord.Embed(
                    title=f"{new_config['emoji']} Félicitations ! Vous passez {new_config['name']} !",
                    description=f"Vous avez atteint **{affiliate.conversions} conversions** !",
                    color=new_config["color"]
                )
                embed.add_field(
                    name="💰 Nouvelle Commission",
                    value=f"**{old_config['commission_percent']}%** → **{new_config['commission_percent']}%**",
                    inline=False
                )
                embed.add_field(
                    name="🎁 Avantages",
                    value="• Badge exclusif\n• Support prioritaire\n• Bonus mensuel",
                    inline=False
                )
                
                await user.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Erreur notification upgrade: {e}")
            
    async def _notify_conversion(self, affiliate: Affiliate, conversion: Conversion):
        """Notifie d'une nouvelle conversion"""
        try:
            user = await self.bot.fetch_user(affiliate.user_id)
            if user:
                tier_config = TIER_CONFIG[affiliate.tier]
                
                embed = discord.Embed(
                    title="💰 Nouvelle Conversion !",
                    description=f"Une nouvelle vente vient d'être réalisée avec votre code !",
                    color=tier_config["color"]
                )
                embed.add_field(
                    name="💵 Montant de la vente",
                    value=f"€{conversion.amount:.2f}",
                    inline=True
                )
                embed.add_field(
                    name="💸 Commission",
                    value=f"€{conversion.commission:.2f} ({affiliate.get_commission_percent()}%)",
                    inline=True
                )
                embed.add_field(
                    name="⏳ Statut",
                    value="En attente de validation (30j)",
                    inline=False
                )
                embed.add_field(
                    name="📊 Vos Stats",
                    value=f"Conversions: {affiliate.conversions}\n"
                          f"En attente: €{affiliate.commission_pending:.2f}",
                    inline=False
                )
                
                await user.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Erreur notification conversion: {e}")
            
    @tasks.loop(hours=24)
    async def check_validation_period(self):
        """Vérifie les conversions à valider (après 30 jours)"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.validation_days)
        
        for conv in self.conversions.values():
            if conv.status == "pending":
                conv_date = datetime.fromisoformat(conv.created_at)
                if conv_date < cutoff_date:
                    await self.validate_conversion(conv.id)
                    
    async def validate_conversion(self, conversion_id: str):
        """Valide une conversion (commission confirmée)"""
        conv = self.conversions.get(conversion_id)
        if not conv or conv.status != "pending":
            return
            
        conv.status = "validated"
        conv.validated_at = datetime.utcnow().isoformat()
        
        # Mettre à jour l'affilié
        affiliate = self.affiliates.get(conv.affiliate_id)
        if affiliate:
            affiliate.commission_earned += conv.commission
            affiliate.commission_pending -= conv.commission
            await self._save_affiliate_stats(affiliate)
            
        # Mettre à jour DB
        if self.db:
            await self.db.execute(
                "UPDATE conversions SET status = 'validated', validated_at = $1 WHERE id = $2",
                conv.validated_at, conversion_id
            )
            
    @tasks.loop(hours=24)
    async def process_auto_payouts(self):
        """Traite les paiements automatiques"""
        for affiliate in self.affiliates.values():
            if affiliate.commission_pending >= self.min_payout:
                await self.create_payout(affiliate.user_id, affiliate.commission_pending)
                
    async def create_payout(self, affiliate_id: int, amount: float, 
                           method: str = "paypal") -> Optional[Payout]:
        """Crée une demande de paiement"""
        affiliate = self.affiliates.get(affiliate_id)
        if not affiliate or amount <= 0:
            return None
            
        payout = Payout(
            id=str(uuid.uuid4())[:12],
            affiliate_id=affiliate_id,
            amount=amount,
            status="pending",
            method=method,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Sauvegarder
        if self.db:
            await self.db.execute(
                """
                INSERT INTO payouts (id, affiliate_id, amount, status, method, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                payout.id, payout.affiliate_id, payout.amount,
                payout.status, payout.method, payout.created_at
            )
            
        self.payouts[payout.id] = payout
        
        # Notifier l'affilié
        await self._notify_payout_request(affiliate, payout)
        
        return payout
        
    async def _notify_payout_request(self, affiliate: Affiliate, payout: Payout):
        """Notifie d'une demande de paiement"""
        try:
            user = await self.bot.fetch_user(affiliate.user_id)
            if user:
                embed = discord.Embed(
                    title="💸 Demande de Paiement",
                    description=f"Votre demande de paiement a été enregistrée.",
                    color=0x3b82f6
                )
                embed.add_field(
                    name="💰 Montant",
                    value=f"€{payout.amount:.2f}",
                    inline=True
                )
                embed.add_field(
                    name="📅 Date",
                    value=datetime.fromisoformat(payout.created_at).strftime("%d/%m/%Y"),
                    inline=True
                )
                embed.add_field(
                    name="⏳ Statut",
                    value="En attente de traitement",
                    inline=True
                )
                
                await user.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Erreur notification payout: {e}")
            
    async def process_payout(self, payout_id: str, transaction_id: Optional[str] = None):
        """Traite un paiement (admin)"""
        payout = self.payouts.get(payout_id)
        if not payout or payout.status != "pending":
            return False
            
        payout.status = "paid"
        payout.paid_at = datetime.utcnow().isoformat()
        payout.transaction_id = transaction_id
        
        # Mettre à jour l'affilié
        affiliate = self.affiliates.get(payout.affiliate_id)
        if affiliate:
            affiliate.commission_paid += payout.amount
            affiliate.commission_earned -= payout.amount
            await self._save_affiliate_stats(affiliate)
            
        # Mettre à jour DB
        if self.db:
            await self.db.execute(
                """
                UPDATE payouts 
                SET status = 'paid', paid_at = $1, transaction_id = $2 
                WHERE id = $3
                """,
                payout.paid_at, transaction_id, payout_id
            )
            
        # Notifier
        await self._notify_payout_processed(affiliate, payout)
        
        return True
        
    async def _notify_payout_processed(self, affiliate: Affiliate, payout: Payout):
        """Notifie qu'un paiement a été traité"""
        try:
            user = await self.bot.fetch_user(affiliate.user_id)
            if user:
                embed = discord.Embed(
                    title="✅ Paiement Effectué !",
                    description=f"Votre commission a été payée.",
                    color=0x10b981
                )
                embed.add_field(
                    name="💰 Montant",
                    value=f"€{payout.amount:.2f}",
                    inline=False
                )
                if payout.transaction_id:
                    embed.add_field(
                        name="🆔 Transaction",
                        value=f"`{payout.transaction_id}`",
                        inline=False
                    )
                
                await user.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Erreur notification paiement: {e}")
            
    async def _save_affiliate_stats(self, affiliate: Affiliate):
        """Sauvegarde les stats d'un affilié"""
        if self.db:
            await self.db.execute(
                """
                UPDATE affiliates 
                SET conversions = $1, revenue_generated = $2, commission_earned = $3,
                    commission_paid = $4, commission_pending = $5, tier = $6, last_conversion = $7
                WHERE user_id = $8
                """,
                affiliate.conversions, affiliate.revenue_generated, affiliate.commission_earned,
                affiliate.commission_paid, affiliate.commission_pending, affiliate.tier.value,
                affiliate.last_conversion, affiliate.user_id
            )
            
    def get_leaderboard(self, limit: int = 10) -> List[Affiliate]:
        """Retourne le classement des affiliés"""
        sorted_affiliates = sorted(
            self.affiliates.values(),
            key=lambda a: a.revenue_generated,
            reverse=True
        )
        return sorted_affiliates[:limit]
        
    def get_stats(self) -> Dict:
        """Retourne les stats globales"""
        total_affiliates = len(self.affiliates)
        active_affiliates = sum(1 for a in self.affiliates.values() if a.is_active)
        total_revenue = sum(a.revenue_generated for a in self.affiliates.values())
        total_commissions = sum(a.commission_earned for a in self.affiliates.values())
        total_conversions = sum(a.conversions for a in self.affiliates.values())
        
        pending_payouts = sum(
            p.amount for p in self.payouts.values() 
            if p.status == "pending"
        )
        
        return {
            'total_affiliates': total_affiliates,
            'active_affiliates': active_affiliates,
            'total_revenue': total_revenue,
            'total_commissions': total_commissions,
            'total_conversions': total_conversions,
            'pending_payouts': pending_payouts,
            'avg_commission': total_commissions / total_conversions if total_conversions > 0 else 0
        }


class AffiliateCommands(commands.Cog):
    """Commandes Discord pour le système d'affiliation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.affiliate_manager = None
        
    def setup_manager(self, manager: AffiliateManager):
        self.affiliate_manager = manager
        
    @commands.hybrid_command(name="affiliate")
    async def affiliate(self, ctx: commands.Context):
        """🤝 Voir votre dashboard affilié"""
        if not self.affiliate_manager:
            return
            
        affiliate = self.affiliate_manager.affiliates.get(ctx.author.id)
        
        if not affiliate:
            # Proposer de devenir affilié
            embed = discord.Embed(
                title="🤝 Programme d'Affiliation",
                description="Vous n'êtes pas encore affilié !\n\n"
                           "Rejoignez notre programme et gagnez jusqu'à **35% de commission** "
                           "sur chaque vente que vous générez.",
                color=0x3b82f6
            )
            embed.add_field(
                name="💰 Commissions par Tier:",
                value="🥉 Bronze: 15%\n🥈 Silver: 20%\n🥇 Gold: 25%\n💎 Platinum: 30%\n👑 Diamond: 35%",
                inline=False
            )
            embed.add_field(
                name="🎯 Comment ça marche?",
                value="1. Recevez votre code unique\n"
                      "2. Partagez-le avec votre audience\n"
                      "3. Gagnez des commissions sur chaque vente\n"
                      "4. Retirez vos gains (min. €50)",
                inline=False
            )
            
            view = discord.ui.View()
            join_btn = discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="Devenir Affilié",
                emoji="🚀"
            )
            join_btn.callback = lambda i: self._join_affiliate(i, ctx.author)
            view.add_item(join_btn)
            
            await ctx.send(embed=embed, view=view, ephemeral=True)
            return
            
        # Dashboard affilié
        tier_config = TIER_CONFIG[affiliate.tier]
        next_tier = affiliate.get_next_tier_progress()
        
        embed = discord.Embed(
            title=f"{tier_config['emoji']} Votre Dashboard Affilié",
            description=f"Tier actuel: **{tier_config['name']}** ({affiliate.get_commission_percent()}%)",
            color=tier_config['color']
        )
        embed.add_field(
            name="🎫 Votre Code",
            value=f"`{affiliate.code}`",
            inline=False
        )
        embed.add_field(
            name="📊 Stats",
            value=f"Conversions: **{affiliate.conversions}**\n"
                  f"Revenue généré: **€{affiliate.revenue_generated:.2f}**",
            inline=True
        )
        embed.add_field(
            name="💰 Commissions",
            value=f"Gagnées: **€{affiliate.commission_earned:.2f}**\n"
                  f"Payées: **€{affiliate.commission_paid:.2f}**\n"
                  f"En attente: **€{affiliate.commission_pending:.2f}**",
            inline=True
        )
        
        if next_tier['has_next']:
            embed.add_field(
                name=f"🎯 Prochain Tier: {next_tier['name']}",
                value=f"Progression: **{next_tier['progress']:.1f}%**\n"
                      f"Encore **{next_tier['needed']}** conversions",
                inline=False
            )
            
        embed.add_field(
            name="🔗 Votre Lien",
            value=f"`https://shellia.ai/?ref={affiliate.code}`",
            inline=False
        )
        
        # Boutons d'action
        view = discord.ui.View()
        
        if affiliate.commission_pending >= 50:
            payout_btn = discord.ui.Button(
                style=discord.ButtonStyle.success,
                label=f"Retirer €{affiliate.commission_pending:.2f}",
                emoji="💸"
            )
            payout_btn.callback = lambda i: self._request_payout(i, affiliate)
            view.add_item(payout_btn)
            
        await ctx.send(embed=embed, view=view, ephemeral=True)
        
    async def _join_affiliate(self, interaction: discord.Interaction, user: discord.User):
        """Rejoint le programme d'affiliation"""
        if self.affiliate_manager:
            affiliate = await self.affiliate_manager.create_affiliate(
                user_id=user.id,
                username=user.name
            )
            await interaction.response.send_message(
                f"✅ Vous êtes maintenant affilié !\nVotre code: `{affiliate.code}`",
                ephemeral=True
            )
            
    async def _request_payout(self, interaction: discord.Interaction, affiliate: Affiliate):
        """Demande un paiement"""
        if self.affiliate_manager:
            payout = await self.affiliate_manager.create_payout(
                affiliate.user_id,
                affiliate.commission_pending
            )
            if payout:
                await interaction.response.send_message(
                    f"💸 Demande de paiement de €{payout.amount:.2f} enregistrée !",
                    ephemeral=True
                )
                
    @commands.hybrid_command(name="affiliate_leaderboard")
    async def affiliate_leaderboard(self, ctx: commands.Context):
        """🏆 Classement des affiliés"""
        if not self.affiliate_manager:
            return
            
        leaderboard = self.affiliate_manager.get_leaderboard(10)
        
        embed = discord.Embed(
            title="🏆 Top Affiliés",
            description="Les meilleurs affiliés ce mois-ci !",
            color=0xffd700
        )
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, aff in enumerate(leaderboard):
            tier_config = TIER_CONFIG[aff.tier]
            embed.add_field(
                name=f"{medals[i]} {aff.username}",
                value=f"{tier_config['emoji']} {tier_config['name']} • "
                      f"€{aff.revenue_generated:.0f} revenue • "
                      f"{aff.conversions} conv.",
                inline=False
            )
            
        await ctx.send(embed=embed, ephemeral=True)
