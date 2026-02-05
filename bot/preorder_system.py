"""
🛍️ SYSTÈME DE PRÉ-ACHAT - Shellia AI
Gère les pré-commandes avec annonces automatiques et marketing
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import json
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class PreorderStatus(Enum):
    ACTIVE = "active"           # Pré-achat ouvert
    CLOSED = "closed"           # Pré-achat fermé
    DELIVERED = "delivered"     # Livré aux clients
    CANCELLED = "cancelled"     # Annulé


class PreorderTier(Enum):
    EARLY_BIRD = "early_bird"      # -30% (premiers 20)
    FOUNDER = "founder"            # -20% (premiers 50)
    SUPPORTER = "supporter"        # -10% (premiers 100)
    REGULAR = "regular"            # Prix normal


@dataclass
class PreorderItem:
    """Item en pré-achat"""
    id: str
    name: str
    description: str
    base_price: Decimal
    image_url: Optional[str] = None
    stock_limit: Optional[int] = None
    preorder_start: datetime = None
    preorder_end: datetime = None
    delivery_date: datetime = None
    benefits: List[str] = None
    
    def __post_init__(self):
        if self.benefits is None:
            self.benefits = []


@dataclass
class PreorderPurchase:
    """Achat en pré-achat"""
    id: str
    user_id: int
    item_id: str
    tier: PreorderTier
    price_paid: Decimal
    status: PreorderStatus
    purchased_at: datetime
    delivered_at: Optional[datetime] = None
    payment_intent_id: Optional[str] = None


class PreorderMarketingSystem:
    """
    🎯 Système complet de pré-achat avec marketing intégré
    """
    
    TIERS_CONFIG = {
        PreorderTier.EARLY_BIRD: {
            "discount": 30,
            "limit": 20,
            "name": "🚀 Early Bird",
            "description": "Les plus rapides ! -30%",
            "color": discord.Color.gold()
        },
        PreorderTier.FOUNDER: {
            "discount": 20,
            "limit": 50,
            "name": "💎 Founder",
            "description": "Fondateurs ! -20%",
            "color": discord.Color.purple()
        },
        PreorderTier.SUPPORTER: {
            "discount": 10,
            "limit": 100,
            "name": "⭐ Supporter",
            "description": "Supporters ! -10%",
            "color": discord.Color.blue()
        },
        PreorderTier.REGULAR: {
            "discount": 0,
            "limit": None,
            "name": "🛍️ Regular",
            "description": "Prix normal",
            "color": discord.Color.greyple()
        }
    }
    
    def __init__(self, bot: commands.Bot, db=None):
        self.bot = bot
        self.db = db
        self.active_preorders: Dict[str, PreorderItem] = {}
        self.purchases: Dict[str, List[PreorderPurchase]] = {}
        
        # Channels
        self.preorder_channel_id: Optional[int] = None
        self.marketing_channel_id: Optional[int] = None
        
        # Tâches
        self.announcement_task = None
        self.progress_task = None
        
    async def setup(self, preorder_channel_id: Optional[int] = None):
        """Initialise le système"""
        self.preorder_channel_id = preorder_channel_id
        
        # Charger les pré-achats actifs
        if self.db:
            await self._load_preorders()
        
        # Démarrer les tâches marketing
        self.announcement_task = self.bot.loop.create_task(
            self._marketing_automation_loop()
        )
        
        logger.info("✅ PreorderMarketingSystem initialisé")
        
    async def _load_preorders(self):
        """Charge les pré-achats depuis la DB"""
        try:
            result = await self.db.fetch(
                "SELECT * FROM preorder_items WHERE status = 'active'"
            )
            for row in result:
                item = PreorderItem(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    base_price=Decimal(str(row['base_price'])),
                    image_url=row.get('image_url'),
                    stock_limit=row.get('stock_limit'),
                    preorder_start=row['preorder_start'],
                    preorder_end=row['preorder_end'],
                    delivery_date=row['delivery_date'],
                    benefits=json.loads(row['benefits']) if row['benefits'] else []
                )
                self.active_preorders[item.id] = item
        except Exception as e:
            logger.error(f"Erreur chargement pré-achats: {e}")
            
    async def create_preorder(
        self,
        name: str,
        description: str,
        base_price: Decimal,
        preorder_days: int,
        delivery_days: int,
        benefits: List[str],
        image_url: Optional[str] = None,
        stock_limit: Optional[int] = None
    ) -> PreorderItem:
        """Crée un nouveau pré-achat"""
        import uuid
        
        item_id = str(uuid.uuid4())[:8]
        
        now = datetime.utcnow()
        item = PreorderItem(
            id=item_id,
            name=name,
            description=description,
            base_price=base_price,
            image_url=image_url,
            stock_limit=stock_limit,
            preorder_start=now,
            preorder_end=now + timedelta(days=preorder_days),
            delivery_date=now + timedelta(days=delivery_days),
            benefits=benefits
        )
        
        self.active_preorders[item_id] = item
        
        # Sauvegarder en DB
        if self.db:
            await self.db.execute(
                """
                INSERT INTO preorder_items 
                (id, name, description, base_price, image_url, stock_limit,
                 preorder_start, preorder_end, delivery_date, benefits, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
                """,
                (item_id, name, description, float(base_price), image_url, stock_limit,
                 now, item.preorder_end, item.delivery_date, json.dumps(benefits))
            )
        
        # Annoncer le pré-achat
        await self._announce_preorder_launch(item)
        
        return item
        
    async def _announce_preorder_launch(self, item: PreorderItem):
        """Annonce le lancement d'un pré-achat"""
        if not self.preorder_channel_id:
            return
            
        channel = self.bot.get_channel(self.preorder_channel_id)
        if not channel:
            return
            
        # Embed principal
        embed = discord.Embed(
            title=f"🎉 NOUVEAU PRÉ-ACHAT: {item.name}",
            description=item.description,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        # Prix par tier
        for tier in [PreorderTier.EARLY_BIRD, PreorderTier.FOUNDER, 
                     PreorderTier.SUPPORTER, PreorderTier.REGULAR]:
            config = self.TIERS_CONFIG[tier]
            price = item.base_price * Decimal(1 - config['discount'] / 100)
            
            limit_text = f"(Limité à {config['limit']})" if config['limit'] else "(Illimité)"
            
            embed.add_field(
                name=f"{config['name']} {limit_text}",
                value=f"~~€{item.base_price}~~ → **€{price:.2f}** ({config['discount']}% OFF)",
                inline=False
            )
            
        # Bénéfices
        if item.benefits:
            embed.add_field(
                name="✨ Bénéfices exclusifs",
                value="\n".join([f"• {b}" for b in item.benefits]),
                inline=False
            )
            
        # Dates
        embed.add_field(
            name="📅 Dates importantes",
            value=(
                f"🛒 Pré-achat jusqu'au: <t:{int(item.preorder_end.timestamp())}:F>\n"
                f"📦 Livraison prévue: <t:{int(item.delivery_date.timestamp())}:F>"
            ),
            inline=False
        )
        
        if item.image_url:
            embed.set_image(url=item.image_url)
            
        embed.set_footer(text=f"ID: {item.id} • Ne manque pas cette opportunité !")
        
        # Boutons d'action
        view = PreorderActionView(self, item.id)
        
        message = await channel.send(
            content="🚨 **PRÉ-ACHAT EXCLUSIF** @everyone",
            embed=embed,
            view=view
        )
        
        logger.info(f"📢 Pré-achat {item.id} annoncé")
        
    async def process_purchase(
        self,
        user_id: int,
        item_id: str,
        tier: PreorderTier
    ) -> Optional[PreorderPurchase]:
        """Traite un achat en pré-achat"""
        item = self.active_preorders.get(item_id)
        if not item:
            return None
            
        # Vérifier si le tier est encore disponible
        current_count = await self._get_tier_count(item_id, tier)
        tier_limit = self.TIERS_CONFIG[tier]['limit']
        
        if tier_limit and current_count >= tier_limit:
            return None  # Tier complet
            
        # Calculer le prix
        discount = self.TIERS_CONFIG[tier]['discount']
        price = item.base_price * Decimal(1 - discount / 100)
        
        # Créer l'achat
        import uuid
        purchase = PreorderPurchase(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            item_id=item_id,
            tier=tier,
            price_paid=price,
            status=PreorderStatus.ACTIVE,
            purchased_at=datetime.utcnow()
        )
        
        # Sauvegarder
        if self.db:
            await self.db.execute(
                """
                INSERT INTO preorder_purchases 
                (id, user_id, item_id, tier, price_paid, status, purchased_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (purchase.id, user_id, item_id, tier.value, float(price), 
                 'active', purchase.purchased_at)
            )
            
        if item_id not in self.purchases:
            self.purchases[item_id] = []
        self.purchases[item_id].append(purchase)
        
        # Annoncer l'achat (marketing social proof)
        await self._announce_purchase_social_proof(user_id, item, tier)
        
        # Vérifier si on doit annoncer "dernières places"
        await self._check_urgency_announcement(item, tier)
        
        return purchase
        
    async def _announce_purchase_social_proof(
        self, 
        user_id: int, 
        item: PreorderItem, 
        tier: PreorderTier
    ):
        """Annonce l'achat pour créer du social proof"""
        if not self.preorder_channel_id:
            return
            
        channel = self.bot.get_channel(self.preorder_channel_id)
        if not channel:
            return
            
        user = self.bot.get_user(user_id)
        user_mention = user.mention if user else f"<@{user_id}>"
        
        tier_config = self.TIERS_CONFIG[tier]
        
        # Annonce discrète (pas @everyone)
        embed = discord.Embed(
            description=f"{user_mention} vient de réserver **{item.name}** au tier **{tier_config['name']}** ! 🎉",
            color=tier_config['color']
        )
        
        await channel.send(embed=embed, delete_after=300)  # Supprime après 5 min
        
    async def _check_urgency_announcement(self, item: PreorderItem, tier: PreorderTier):
        """Annonce l'urgence si stock faible"""
        current_count = await self._get_tier_count(item.id, tier)
        tier_limit = self.TIERS_CONFIG[tier]['limit']
        
        if not tier_limit:
            return
            
        remaining = tier_limit - current_count
        
        # Annoncer à 5, 3, 1 places restantes
        if remaining in [5, 3, 1]:
            await self._announce_urgency(item, tier, remaining)
            
    async def _announce_urgency(self, item: PreorderItem, tier: PreorderTier, remaining: int):
        """Annonce l'urgence"""
        if not self.preorder_channel_id:
            return
            
        channel = self.bot.get_channel(self.preorder_channel_id)
        if not channel:
            return
            
        tier_config = self.TIERS_CONFIG[tier]
        
        urgency_emoji = "🔥" if remaining <= 3 else "⚡"
        
        embed = discord.Embed(
            title=f"{urgency_emoji} URGENCE - Plus que {remaining} places !",
            description=(
                f"Le tier **{tier_config['name']}** pour **{item.name}** "
                f"n'a plus que **{remaining}** places disponibles !\n\n"
                f"Ne manque pas cette promotion de **{tier_config['discount']}%** !"
            ),
            color=discord.Color.red()
        )
        
        await channel.send(embed=embed)
        
    async def _get_tier_count(self, item_id: str, tier: PreorderTier) -> int:
        """Compte le nombre d'achats pour un tier"""
        if not self.db:
            return 0
            
        result = await self.db.fetch(
            """
            SELECT COUNT(*) as count FROM preorder_purchases
            WHERE item_id = %s AND tier = %s AND status != 'cancelled'
            """,
            (item_id, tier.value)
        )
        
        return result[0]['count'] if result else 0
        
    async def close_preorder(self, item_id: str):
        """Ferme un pré-achat"""
        if item_id in self.active_preorders:
            del self.active_preorders[item_id]
            
        if self.db:
            await self.db.execute(
                "UPDATE preorder_items SET status = 'closed' WHERE id = %s",
                (item_id,)
            )
            
        # Annoncer la fin
        await self._announce_preorder_closed(item_id)
        
    async def _announce_preorder_closed(self, item_id: str):
        """Annonce la fin du pré-achat"""
        if not self.preorder_channel_id:
            return
            
        channel = self.bot.get_channel(self.preorder_channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="🔒 Pré-achat terminé",
            description="Les pré-achats sont maintenant fermés. Merci à tous !",
            color=discord.Color.green()
        )
        
        await channel.send(embed=embed)
        
    async def _marketing_automation_loop(self):
        """Boucle d'automatisation marketing"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await self._process_marketing_triggers()
            except Exception as e:
                logger.error(f"Erreur marketing automation: {e}")
                
            await asyncio.sleep(3600)  # Toutes les heures
            
    async def _process_marketing_triggers(self):
        """Traite les déclencheurs marketing"""
        for item_id, item in list(self.active_preorders.items()):
            # Vérifier si fin approche
            time_remaining = item.preorder_end - datetime.utcnow()
            
            if timedelta(hours=24) < time_remaining <= timedelta(hours=25):
                await self._announce_ending_soon(item, 24)
            elif timedelta(hours=6) < time_remaining <= timedelta(hours=7):
                await self._announce_ending_soon(item, 6)
            elif time_remaining <= timedelta(0):
                await self.close_preorder(item_id)
                
    async def _announce_ending_soon(self, item: PreorderItem, hours: int):
        """Annonce que le pré-achat se termine bientôt"""
        if not self.preorder_channel_id:
            return
            
        channel = self.bot.get_channel(self.preorder_channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title=f"⏰ DERNIÈRE CHANCE - {hours}h restantes !",
            description=(
                f"Le pré-achat **{item.name}** se termine dans moins de **{hours} heures** !\n\n"
                f"C'est ta dernière chance pour profiter des tarifs préférentiels !"
            ),
            color=discord.Color.orange()
        )
        
        await channel.send(embed=embed)
        
    def get_preorder_stats(self, item_id: str) -> Dict[str, Any]:
        """Récupère les stats d'un pré-achat"""
        item = self.active_preorders.get(item_id)
        if not item:
            return {}
            
        purchases = self.purchases.get(item_id, [])
        
        total_revenue = sum(p.price_paid for p in purchases)
        total_sold = len(purchases)
        
        by_tier = {}
        for tier in PreorderTier:
            count = len([p for p in purchases if p.tier == tier])
            revenue = sum(p.price_paid for p in purchases if p.tier == tier)
            by_tier[tier.value] = {"count": count, "revenue": float(revenue)}
            
        return {
            "item_name": item.name,
            "total_sold": total_sold,
            "total_revenue": float(total_revenue),
            "by_tier": by_tier,
            "ends_at": item.preorder_end.isoformat()
        }


class PreorderActionView(discord.ui.View):
    """Boutons d'action pour pré-achat"""
    
    def __init__(self, system: PreorderMarketingSystem, item_id: str):
        super().__init__(timeout=None)
        self.system = system
        self.item_id = item_id
        
    @discord.ui.button(label="🚀 Early Bird (-30%)", style=discord.ButtonStyle.green, custom_id="preorder_early_bird")
    async def early_bird_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_purchase(interaction, PreorderTier.EARLY_BIRD)
        
    @discord.ui.button(label="💎 Founder (-20%)", style=discord.ButtonStyle.blurple, custom_id="preorder_founder")
    async def founder_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_purchase(interaction, PreorderTier.FOUNDER)
        
    @discord.ui.button(label="📋 Voir détails", style=discord.ButtonStyle.grey, custom_id="preorder_details")
    async def details_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Afficher les détails complets
        item = self.system.active_preorders.get(self.item_id)
        if not item:
            await interaction.response.send_message("Pré-achat non trouvé.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"📋 Détails: {item.name}",
            description=item.description,
            color=discord.Color.blue()
        )
        
        # Stats
        stats = self.system.get_preorder_stats(self.item_id)
        if stats:
            embed.add_field(
                name="📊 Stats",
                value=f"{stats['total_sold']} vendus | €{stats['total_revenue']:.2f} de revenus",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    async def _handle_purchase(self, interaction: discord.Interaction, tier: PreorderTier):
        """Gère l'achat"""
        # Vérifier disponibilité
        current = await self.system._get_tier_count(self.item_id, tier)
        limit = self.system.TIERS_CONFIG[tier]['limit']
        
        if limit and current >= limit:
            await interaction.response.send_message(
                f"❌ Le tier {self.system.TIERS_CONFIG[tier]['name']} est complet !",
                ephemeral=True
            )
            return
            
        # Traiter l'achat (intégration Stripe ici)
        purchase = await self.system.process_purchase(
            interaction.user.id,
            self.item_id,
            tier
        )
        
        if purchase:
            await interaction.response.send_message(
                f"✅ Réservation confirmée au tier **{self.system.TIERS_CONFIG[tier]['name']}** !\n"
                f"Prix: €{purchase.price_paid:.2f}\n"
                f"Un MP vous sera envoyé pour le paiement.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Une erreur est survenue. Réessayez plus tard.",
                ephemeral=True
            )
