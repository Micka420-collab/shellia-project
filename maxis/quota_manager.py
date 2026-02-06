"""
📊 QUOTA MANAGER - Gestion des quotas avec achat via Stripe
Rentabilité optimisée - Prix dégressifs à volume
"""

import discord
from discord.ext import commands
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import uuid


@dataclass
class QuotaPackage:
    """Package de quota disponible à l'achat"""
    id: str
    name: str
    amount: int  # Nombre de requêtes
    price_cents: int  # Prix en cents (Stripe)
    price_display: str  # Prix affiché (ex: "€2.99")
    popular: bool = False
    discount_percent: int = 0
    
    @property
    def cost_per_request(self) -> float:
        """Coût par requête en euros"""
        return (self.price_cents / 100) / self.amount


# Configuration des packages - OPTIMISÉ POUR RENTABILITÉ
QUOTA_PACKAGES = {
    "starter": QuotaPackage(
        id="quota_100",
        name="Starter",
        amount=100,
        price_cents=299,  # €2.99
        price_display="€2.99",
        popular=False
    ),
    "regular": QuotaPackage(
        id="quota_500",
        name="Regular",
        amount=500,
        price_cents=999,  # €9.99
        price_display="€9.99",
        popular=False
    ),
    "popular": QuotaPackage(
        id="quota_1000",
        name="Plus",
        amount=1000,
        price_cents=1499,  # €14.99
        price_display="€14.99",
        popular=True,
        discount_percent=0  # Référence
    ),
    "business": QuotaPackage(
        id="quota_5000",
        name="Business",
        amount=5000,
        price_cents=4999,  # €49.99 (-17% vs achat unitaire)
        price_display="€49.99",
        popular=False,
        discount_percent=17
    ),
    "enterprise": QuotaPackage(
        id="quota_10000",
        name="Enterprise",
        amount=10000,
        price_cents=8999,  # €89.99 (-40% vs achat unitaire)
        price_display="€89.99",
        popular=False,
        discount_percent=40
    ),
    "mega": QuotaPackage(
        id="quota_50000",
        name="Mega",
        amount=50000,
        price_cents=34999,  # €349.99 (-53% vs achat unitaire)
        price_display="€349.99",
        popular=False,
        discount_percent=53
    )
}


@dataclass
class UserQuota:
    """Quota d'un utilisateur"""
    user_id: int
    daily_limit: int  # Limite quotidienne selon plan
    daily_used: int  # Utilisé aujourd'hui
    daily_reset_at: datetime
    
    purchased_quota: int  # Quota acheté (jamais expire)
    purchased_used: int  # Utilisé du quota acheté
    
    total_used_lifetime: int  # Stats
    last_purchase_at: Optional[datetime] = None
    
    @property
    def has_quota_available(self) -> bool:
        """Vérifie si l'utilisateur a du quota disponible"""
        # Reset quotidien si nécessaire
        if datetime.utcnow() >= self.daily_reset_at:
            self.daily_used = 0
            self.daily_reset_at = datetime.utcnow() + timedelta(days=1)
            
        daily_remaining = self.daily_limit - self.daily_used
        purchased_remaining = self.purchased_quota - self.purchased_used
        
        return daily_remaining > 0 or purchased_remaining > 0
    
    @property
    def remaining_today(self) -> int:
        """Quota restant aujourd'hui"""
        if datetime.utcnow() >= self.daily_reset_at:
            self.daily_used = 0
            self.daily_reset_at = datetime.utcnow() + timedelta(days=1)
            
        daily_remaining = max(0, self.daily_limit - self.daily_used)
        purchased_remaining = max(0, self.purchased_quota - self.purchased_used)
        
        return daily_remaining + purchased_remaining
    
    def consume(self, amount: int = 1) -> bool:
        """Consomme du quota. Retourne True si succès."""
        if not self.has_quota_available:
            return False
            
        # D'abord utiliser le quota quotidien
        daily_remaining = self.daily_limit - self.daily_used
        if daily_remaining > 0:
            use_from_daily = min(amount, daily_remaining)
            self.daily_used += use_from_daily
            amount -= use_from_daily
            
        # Ensuite utiliser le quota acheté
        if amount > 0:
            purchased_remaining = self.purchased_quota - self.purchased_used
            if purchased_remaining >= amount:
                self.purchased_used += amount
                amount = 0
            else:
                return False
                
        self.total_used_lifetime += amount
        return True
    
    def add_purchased_quota(self, amount: int):
        """Ajoute du quota acheté"""
        self.purchased_quota += amount
        self.last_purchase_at = datetime.utcnow()


class QuotaManager:
    """
    📊 Gestionnaire de Quotas avec monetisation
    """
    
    # Quotas selon les plans
    PLAN_QUOTAS = {
        "free": 50,
        "pro": 1000,
        "ultra": 5000,
        "founder": 10000
    }
    
    def __init__(self, bot: commands.Bot, db=None, stripe_manager=None):
        self.bot = bot
        self.db = db
        self.stripe_manager = stripe_manager
        self.user_quotas: Dict[int, UserQuota] = {}
        
    async def setup(self):
        """Initialise le gestionnaire de quotas"""
        if self.db:
            await self._load_quotas_from_db()
        print("✅ QuotaManager initialisé")
        
    async def _load_quotas_from_db(self):
        """Charge les quotas depuis la DB"""
        try:
            result = await self.db.fetch("SELECT * FROM user_quotas")
            for row in result:
                quota = UserQuota(
                    user_id=row['user_id'],
                    daily_limit=row['daily_limit'],
                    daily_used=row.get('daily_used', 0),
                    daily_reset_at=row.get('daily_reset_at', datetime.utcnow() + timedelta(days=1)),
                    purchased_quota=row.get('purchased_quota', 0),
                    purchased_used=row.get('purchased_used', 0),
                    total_used_lifetime=row.get('total_used_lifetime', 0),
                    last_purchase_at=row.get('last_purchase_at')
                )
                self.user_quotas[quota.user_id] = quota
        except Exception as e:
            print(f"⚠️ Erreur chargement quotas: {e}")
            
    async def get_or_create_quota(self, user_id: int, plan: str = "free") -> UserQuota:
        """Récupère ou crée le quota d'un utilisateur"""
        if user_id in self.user_quotas:
            return self.user_quotas[user_id]
            
        quota = UserQuota(
            user_id=user_id,
            daily_limit=self.PLAN_QUOTAS.get(plan, 50),
            daily_used=0,
            daily_reset_at=datetime.utcnow() + timedelta(days=1),
            purchased_quota=0,
            purchased_used=0,
            total_used_lifetime=0
        )
        
        if self.db:
            await self.db.execute(
                """
                INSERT INTO user_quotas 
                (user_id, daily_limit, daily_used, daily_reset_at, purchased_quota, purchased_used, total_used_lifetime)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO NOTHING
                """,
                quota.user_id, quota.daily_limit, quota.daily_used, quota.daily_reset_at,
                quota.purchased_quota, quota.purchased_used, quota.total_used_lifetime
            )
            
        self.user_quotas[user_id] = quota
        return quota
        
    async def update_plan_quota(self, user_id: int, plan: str):
        """Met à jour le quota lors d'un changement de plan"""
        quota = await self.get_or_create_quota(user_id, plan)
        quota.daily_limit = self.PLAN_QUOTAS.get(plan, 50)
        
        if self.db:
            await self.db.execute(
                "UPDATE user_quotas SET daily_limit = $1 WHERE user_id = $2",
                quota.daily_limit, user_id
            )
            
    async def create_checkout_session(self, user_id: int, package_id: str) -> Optional[Dict]:
        """Crée une session Stripe pour l'achat de quota"""
        package = QUOTA_PACKAGES.get(package_id)
        if not package or not self.stripe_manager:
            return None
            
        try:
            session = await self.stripe_manager.create_checkout_session(
                user_id=user_id,
                price_id=package.id,  # Doit correspondre à un price Stripe
                success_url=f"https://shellia.ai/quota/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url="https://shellia.ai/quota/cancel",
                metadata={
                    "type": "quota_purchase",
                    "package_id": package_id,
                    "quota_amount": str(package.amount),
                    "user_id": str(user_id)
                }
            )
            
            # Log la tentative d'achat
            if self.db:
                await self.db.execute(
                    """
                    INSERT INTO quota_purchase_attempts 
                    (user_id, package_id, amount, price_cents, stripe_session_id, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id, package_id, package.amount, package.price_cents,
                    session['session_id'], datetime.utcnow().isoformat()
                )
                
            return session
            
        except Exception as e:
            print(f"❌ Erreur création session quota: {e}")
            return None
            
    async def process_successful_purchase(self, session_id: str):
        """Traite un achat de quota réussi (appelé par webhook Stripe)"""
        try:
            # Récupérer les infos de la session
            if self.db:
                result = await self.db.fetch(
                    "SELECT * FROM quota_purchase_attempts WHERE stripe_session_id = $1",
                    session_id
                )
                
                if not result:
                    print(f"⚠️ Session {session_id} non trouvée")
                    return
                    
                attempt = result[0]
                user_id = attempt['user_id']
                amount = attempt['amount']
                
                # Mettre à jour le quota de l'utilisateur
                quota = await self.get_or_create_quota(user_id)
                quota.add_purchased_quota(amount)
                
                # Sauvegarder
                await self.db.execute(
                    """
                    UPDATE user_quotas 
                    SET purchased_quota = $1, last_purchase_at = $2
                    WHERE user_id = $3
                    """,
                    quota.purchased_quota, quota.last_purchase_at, user_id
                )
                
                # Marquer comme complété
                await self.db.execute(
                    """
                    UPDATE quota_purchase_attempts 
                    SET status = 'completed', completed_at = $1
                    WHERE stripe_session_id = $2
                    """,
                    datetime.utcnow().isoformat(), session_id
                )
                
                # Notifier l'utilisateur
                await self._notify_purchase_success(user_id, amount)
                
                print(f"✅ Quota ajouté: {amount} pour user {user_id}")
                
        except Exception as e:
            print(f"❌ Erreur traitement achat quota: {e}")
            
    async def _notify_purchase_success(self, user_id: int, amount: int):
        """Notifie l'utilisateur de l'achat réussi"""
        try:
            user = await self.bot.fetch_user(user_id)
            if user:
                embed = discord.Embed(
                    title="✅ Achat de Quota Confirmé !",
                    description=f"**{amount:,}** requêtes ont été ajoutées à votre compte.",
                    color=0x10b981
                )
                embed.add_field(
                    name="📊 Nouveau Solde",
                    value="Consultez avec `/quota`",
                    inline=False
                )
                embed.add_field(
                    name="💡 Le quota n'expire jamais !",
                    value="Utilisez-le quand vous en avez besoin.",
                    inline=False
                )
                
                await user.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Erreur notification: {e}")
            
    def get_packages(self) -> List[QuotaPackage]:
        """Retourne tous les packages disponibles"""
        return list(QUOTA_PACKAGES.values())
        
    def get_package(self, package_id: str) -> Optional[QuotaPackage]:
        """Retourne un package spécifique"""
        return QUOTA_PACKAGES.get(package_id)
        
    async def get_stats(self, user_id: int) -> Dict:
        """Retourne les stats de quota d'un utilisateur"""
        quota = await self.get_or_create_quota(user_id)
        
        return {
            "daily_limit": quota.daily_limit,
            "daily_used": quota.daily_used,
            "daily_remaining": max(0, quota.daily_limit - quota.daily_used),
            "purchased_quota": quota.purchased_quota,
            "purchased_used": quota.purchased_used,
            "purchased_remaining": max(0, quota.purchased_quota - quota.purchased_used),
            "total_remaining": quota.remaining_today,
            "reset_at": quota.daily_reset_at.isoformat(),
            "total_used_lifetime": quota.total_used_lifetime
        }


class QuotaCommands(commands.Cog):
    """Commandes Discord pour la gestion des quotas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.quota_manager = None
        
    def setup_manager(self, manager: QuotaManager):
        self.quota_manager = manager
        
    @commands.hybrid_command(name="quota")
    async def quota(self, ctx: commands.Context):
        """📊 Voir votre quota disponible"""
        if not self.quota_manager:
            return
            
        stats = await self.quota_manager.get_stats(ctx.author.id)
        
        embed = discord.Embed(
            title="📊 Votre Quota",
            color=0x3b82f6
        )
        
        # Barre de progression
        daily_percent = (stats['daily_used'] / stats['daily_limit']) * 100 if stats['daily_limit'] > 0 else 0
        bar_filled = int(daily_percent / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        
        embed.add_field(
            name=f"📅 Quota Quotidien {bar}",
            value=f"```\n{stats['daily_used']:,} / {stats['daily_limit']:,} requêtes\n```",
            inline=False
        )
        
        if stats['purchased_quota'] > 0:
            embed.add_field(
                name="💎 Quota Acheté (illimité)",
                value=f"```\n{stats['purchased_remaining']:,} / {stats['purchased_quota']:,} requêtes restantes\n```",
                inline=False
            )
            
        embed.add_field(
            name="🔄 Reset dans",
            value=f"<t:{int(datetime.fromisoformat(stats['reset_at']).timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="📈 Total utilisé",
            value=f"{stats['total_used_lifetime']:,} requêtes",
            inline=True
        )
        
        if stats['total_remaining'] < 100:
            embed.add_field(
                name="⚠️ Quota faible !",
                value="Utilisez `/buy_quota` pour en acheter plus.",
                inline=False
            )
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="buy_quota")
    async def buy_quota(self, ctx: commands.Context):
        """💎 Acheter du quota supplémentaire"""
        if not self.quota_manager:
            return
            
        packages = self.quota_manager.get_packages()
        
        embed = discord.Embed(
            title="💎 Acheter du Quota",
            description="Ajoutez des requêtes à votre compte. **Le quota n'expire jamais !**",
            color=0xffd700
        )
        
        for pkg in packages:
            value = f"**{pkg.price_display}** - {pkg.amount:,} requêtes"
            if pkg.discount_percent > 0:
                value += f"\n✨ **-{pkg.discount_percent}%** vs prix unitaire"
            value += f"\n*Coût: €{pkg.cost_per_request:.4f}/req*"
            
            embed.add_field(
                name=f"{'🔥 ' if pkg.popular else ''}{pkg.name}",
                value=value,
                inline=True
            )
            
        # Boutons d'achat
        view = discord.ui.View()
        for pkg in packages:
            if pkg.popular:
                btn = discord.ui.Button(
                    style=discord.ButtonStyle.success,
                    label=f"{pkg.name} - {pkg.price_display}",
                    emoji="🔥",
                    custom_id=f"buy_quota_{pkg.id}"
                )
            else:
                btn = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=f"{pkg.name} - {pkg.price_display}",
                    custom_id=f"buy_quota_{pkg.id}"
                )
            btn.callback = self._create_buy_callback(pkg.id)
            view.add_item(btn)
            
        await ctx.send(embed=embed, view=view, ephemeral=True)
        
    def _create_buy_callback(self, package_id: str):
        """Crée un callback pour l'achat"""
        async def callback(interaction: discord.Interaction):
            if not self.quota_manager:
                return
                
            session = await self.quota_manager.create_checkout_session(
                interaction.user.id,
                package_id
            )
            
            if session:
                await interaction.response.send_message(
                    f"💳 **Redirection vers Stripe...**\n\n"
                    f"Cliquez ici pour finaliser votre achat:\n"
                    f"{session['checkout_url']}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Erreur lors de la création de la session de paiement.",
                    ephemeral=True
                )
        return callback
