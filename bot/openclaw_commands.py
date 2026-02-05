"""
🦀 Commandes OpenClaw - Gestion complète du business
Commandes pour gérer : rentabilité, promotions, giveaways, événements
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio

from openclaw_manager import OpenClawManager, BusinessConfig, PromotionType


class OpenClawCommands(commands.Cog):
    """
    Commandes admin pour OpenClaw Manager
    Gère le business model complet
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.openclaw: Optional[OpenClawManager] = None
        
    def setup_manager(self, manager: OpenClawManager):
        """Configure le manager OpenClaw"""
        self.openclaw = manager
        
    # ============ COMMANDES RAPPORT ============
    
    @commands.hybrid_command(name="openclaw", aliases=["oc"])
    @commands.has_permissions(administrator=True)
    async def openclaw_dashboard(self, ctx: commands.Context):
        """
        📊 Dashboard OpenClaw - Vue d'ensemble business
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw Manager non disponible.", ephemeral=True)
            return
            
        embed = await self.openclaw.get_business_report()
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="oc_metrics")
    @commands.has_permissions(administrator=True)
    async def show_metrics(self, ctx: commands.Context, days: int = 7):
        """
        📈 Affiche les métriques détaillées
        
        Args:
            days: Nombre de jours d'historique (défaut: 7)
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"📈 Métriques sur {days} jours",
            color=discord.Color.blue()
        )
        
        history = self.openclaw.metrics_history[:days]
        
        if not history:
            embed.description = "Pas encore assez d'historique."
            await ctx.send(embed=embed, ephemeral=True)
            return
            
        # Tendance MRR
        mrr_values = [m.get('mrr', 0) for m in history]
        if len(mrr_values) > 1:
            trend = ((mrr_values[0] - mrr_values[-1]) / mrr_values[-1] * 100) if mrr_values[-1] > 0 else 0
            trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
            
            embed.add_field(
                name="💰 MRR",
                value=f"Actuel: €{mrr_values[0]:.2f}\n{trend_emoji} {trend:+.1f}% sur {days}j",
                inline=True
            )
            
        # Tendance conversion
        conv_values = [m.get('conversion_rate', 0) * 100 for m in history]
        if conv_values:
            embed.add_field(
                name="🎯 Conversion",
                value=f"Actuelle: {conv_values[0]:.2f}%\nPic: {max(conv_values):.2f}%",
                inline=True
            )
            
        # Utilisateurs
        active_values = [m.get('active_users', 0) for m in history]
        if active_values:
            embed.add_field(
                name="👥 Utilisateurs",
                value=f"Actifs: {active_values[0]}\nMax: {max(active_values)}",
                inline=True
            )
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="oc_giveaway_roi")
    @commands.has_permissions(administrator=True)
    async def giveaway_roi_report(self, ctx: commands.Context):
        """
        🎁 Analyse ROI des giveaways
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="🎁 ROI des Giveaways",
            color=discord.Color.gold()
        )
        
        if not self.openclaw.giveaway_rois:
            embed.description = "Pas encore de données de giveaways."
            await ctx.send(embed=embed, ephemeral=True)
            return
            
        total_cost = sum(r.cost for r in self.openclaw.giveaway_rois.values())
        total_revenue = sum(r.revenue_generated for r in self.openclaw.giveaway_rois.values())
        total_new_users = sum(r.new_users for r in self.openclaw.giveaway_rois.values())
        avg_roi = total_revenue / total_cost if total_cost > 0 else 0
        
        embed.add_field(
            name="💰 Coût total",
            value=f"€{total_cost:.2f}",
            inline=True
        )
        
        embed.add_field(
            name="💵 Revenu généré",
            value=f"€{total_revenue:.2f}",
            inline=True
        )
        
        embed.add_field(
            name="📊 ROI moyen",
            value=f"{avg_roi:.2f}x",
            inline=True
        )
        
        embed.add_field(
            name="👥 Nouveaux membres",
            value=f"{total_new_users}",
            inline=True
        )
        
        # ROI par giveaway
        roi_list = sorted(
            self.openclaw.giveaway_rois.values(),
            key=lambda x: x.roi_ratio,
            reverse=True
        )[:5]
        
        roi_text = "\n".join([
            f"{r.giveaway_id}: {r.roi_ratio:.2f}x (€{r.cost:.0f} → €{r.revenue_generated:.0f})"
            for r in roi_list
        ])
        
        embed.add_field(
            name="🏆 Top 5 ROI",
            value=roi_text or "Aucun",
            inline=False
        )
        
        await ctx.send(embed=embed, ephemeral=True)
        
    # ============ COMMANDES PROMOTIONS ============
    
    @commands.hybrid_command(name="oc_promos")
    @commands.has_permissions(administrator=True)
    async def list_promotions(self, ctx: commands.Context):
        """
        🎁 Liste les promotions actives
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"🎁 Promotions Actives ({len(self.openclaw.active_promotions)})",
            color=discord.Color.green()
        )
        
        if not self.openclaw.active_promotions:
            embed.description = "Aucune promotion active."
            await ctx.send(embed=embed, ephemeral=True)
            return
            
        # Grouper par type
        by_type = {}
        for promo in self.openclaw.active_promotions.values():
            if promo.type.value not in by_type:
                by_type[promo.type.value] = []
            by_type[promo.type.value].append(promo)
            
        for promo_type, promos in by_type.items():
            value = f"{len(promos)} active(s)"
            if promos:
                avg_discount = sum(p.discount_percent for p in promos) / len(promos)
                value += f"\nRéduction moyenne: {avg_discount:.0f}%"
            embed.add_field(name=promo_type.replace('_', ' ').title(), value=value, inline=True)
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="oc_promo_create")
    @commands.has_permissions(administrator=True)
    async def create_promotion(
        self,
        ctx: commands.Context,
        user: discord.User,
        discount: int,
        duration_hours: int,
        *,
        message: str
    ):
        """
        ➕ Crée une promotion manuelle
        
        Args:
            user: Utilisateur cible
            discount: % de réduction (1-99)
            duration_hours: Durée de validité
            message: Message personnalisé
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        if discount < 1 or discount > 99:
            await ctx.send("❌ La réduction doit être entre 1 et 99%", ephemeral=True)
            return
            
        promo = await self.openclaw._create_promotion(
            user_id=user.id,
            promo_type=PromotionType.LOYALTY,
            discount_percent=discount,
            duration_hours=duration_hours,
            message=message
        )
        
        await self.openclaw._send_promotion_message(user.id, promo)
        
        await ctx.send(
            f"✅ Promotion créée pour {user.mention}\n"
            f"Code: `{promo.code}`\n"
            f"Réduction: {discount}%\n"
            f"Expire: <t:{int(promo.valid_until.timestamp())}:F>",
            ephemeral=True
        )
        
    @commands.hybrid_command(name="oc_promo_disable")
    @commands.has_permissions(administrator=True)
    async def disable_promotions(self, ctx: commands.Context):
        """
        ⏸️ Désactive les promotions automatiques
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        self.openclaw.config.enable_auto_promotions = False
        await ctx.send("⏸️ Promotions automatiques désactivées.", ephemeral=True)
        
    @commands.hybrid_command(name="oc_promo_enable")
    @commands.has_permissions(administrator=True)
    async def enable_promotions(self, ctx: commands.Context):
        """
        ▶️ Active les promotions automatiques
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        self.openclaw.config.enable_auto_promotions = True
        await ctx.send("▶️ Promotions automatiques activées.", ephemeral=True)
        
    # ============ COMMANDES CONFIGURATION ============
    
    @commands.hybrid_command(name="oc_config")
    @commands.has_permissions(administrator=True)
    async def show_config(self, ctx: commands.Context):
        """
        ⚙️ Affiche la configuration OpenClaw
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        config = self.openclaw.config
        
        embed = discord.Embed(
            title="⚙️ Configuration OpenClaw",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💰 Objectifs",
            value=f"MRR cible: €{config.target_mrr:.0f}\nConversion: {config.target_conversion*100:.0f}%",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Promotions",
            value=f"Auto: {'✅' if config.enable_auto_promotions else '❌'}\nMax réduction: {config.max_discount_percent}%\nCooldown: {config.promotion_cooldown_days}j",
            inline=False
        )
        
        embed.add_field(
            name="🎉 Giveaways",
            value=f"Budget max: {config.max_giveaway_budget_percent*100:.0f}% MRR\nROI cible: {config.giveaway_roi_target}x",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Grade Winner",
            value=f"Durée: {config.winner_plan_duration_days}j\nPlan: {config.winner_plan_type}",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Winback",
            value=f"Inactivité: {config.churn_threshold_days}j\nRéduction: {config.winback_discount}%",
            inline=False
        )
        
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="oc_config_set")
    @commands.has_permissions(administrator=True)
    async def set_config(
        self,
        ctx: commands.Context,
        key: str,
        value: str
    ):
        """
        🔧 Modifie une configuration
        
        Args:
            key: Nom du paramètre (target_mrr, max_discount_percent, etc.)
            value: Nouvelle valeur
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        # Convertir la valeur
        try:
            if key in ['target_mrr', 'max_cac', 'max_giveaway_budget_percent', 
                       'giveaway_roi_target', 'min_ltv_cac_ratio']:
                converted = float(value)
            elif key in ['target_conversion']:
                converted = float(value) / 100  # Convertir % en décimal
            else:
                converted = int(value)
        except ValueError:
            await ctx.send("❌ Valeur invalide.", ephemeral=True)
            return
            
        await self.openclaw.adjust_config(**{key: converted})
        
        await ctx.send(f"✅ Configuration mise à jour: `{key}` = `{value}`", ephemeral=True)
        
    # ============ COMMANDES GIVEAWAYS AVANCÉS ============
    
    @commands.hybrid_command(name="oc_giveaway_analyze")
    @commands.has_permissions(administrator=True)
    async def analyze_giveaway(
        self,
        ctx: commands.Context,
        current_members: int,
        target_members: int
    ):
        """
        🔮 Analyse la rentabilité d'un giveaway futur
        
        Args:
            current_members: Membres actuels
            target_members: Objectif de membres
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        should_run, config = await self.openclaw.calculate_optimal_giveaway(
            current_members,
            target_members
        )
        
        embed = discord.Embed(
            title="🔮 Analyse Giveaway",
            color=discord.Color.purple() if should_run else discord.Color.orange()
        )
        
        embed.add_field(
            name="📊 Recommandation",
            value="✅ LANCER" if should_run else "⏸️ ATTENDRE",
            inline=False
        )
        
        embed.add_field(
            name="💰 Budget estimé",
            value=f"€{config.get('budget', 0):.2f}",
            inline=True
        )
        
        embed.add_field(
            name="📈 ROI estimé",
            value=f"{config.get('roi_estimate', 0):.2f}x",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Gagnants",
            value=f"{config.get('winners', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Récompense",
            value=f"{config.get('currency_reward', 0)} coins",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Durée",
            value=f"{config.get('duration_hours', 0)}h",
            inline=True
        )
        
        embed.add_field(
            name="📋 Stratégie",
            value=config.get('strategy', 'standard'),
            inline=True
        )
        
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="oc_winner_cleanup")
    @commands.has_permissions(administrator=True)
    async def cleanup_winners(self, ctx: commands.Context):
        """
        🧹 Nettoie les grades Winner expirés
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        await self.openclaw.remove_expired_winner_grades()
        await ctx.send("🧹 Nettoyage des grades Winner effectué.", ephemeral=True)
        
    # ============ COMMANDES ÉVÉNEMENTS ============
    
    @commands.hybrid_command(name="oc_event_trigger")
    @commands.has_permissions(administrator=True)
    async def trigger_event(
        self,
        ctx: commands.Context,
        event_type: str,
        value: float
    ):
        """
        🎉 Déclenche un événement manuel
        
        Args:
            event_type: Type d'événement (mrr_target, conversion_record, etc.)
            value: Valeur associée
        """
        if not self.openclaw:
            await ctx.send("❌ OpenClaw non disponible.", ephemeral=True)
            return
            
        await self.openclaw._trigger_milestone_event(ctx.guild, event_type, value)
        await ctx.send(f"✅ Événement `{event_type}` déclenché !", ephemeral=True)
        
    # ============ COMMANDES UTILISATEUR (INFOS) ============
    
    @commands.hybrid_command(name="winner")
    async def winner_info(self, ctx: commands.Context):
        """
        🏆 Informations sur le grade Winner
        """
        if not self.openclaw:
            await ctx.send("❌ Information non disponible.")
            return
            
        embed = discord.Embed(
            title="🏆 Grade Winner",
            description="Le grade spécial pour les gagnants de giveaways !",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🎁 Avantages",
            value=(
                f"• Accès **Pro** pendant {self.openclaw.config.winner_plan_duration_days} jours\n"
                f"• Badge exclusif 🏆\n"
                f"• Accès au salon #🏆│winners\n"
                f"• Mention spéciale sur le serveur"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Comment obtenir ?",
            value="Gagne un giveaway automatique quand le serveur atteint un palier de membres !",
            inline=False
        )
        
        embed.add_field(
            name="📊 Prochains paliers",
            value="Utilise `!giveaway` pour voir les prochains objectifs !",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="my_promo")
    async def my_promotions(self, ctx: commands.Context):
        """
        🎁 Voir mes promotions actives
        """
        if not self.openclaw:
            await ctx.send("❌ Information non disponible.")
            return
            
        user_promos = [
            p for p in self.openclaw.active_promotions.values()
            if p.user_id == ctx.author.id
        ]
        
        if not user_promos:
            await ctx.send("😔 Tu n'as pas de promotion active en ce moment.")
            return
            
        embed = discord.Embed(
            title="🎁 Tes promotions actives",
            color=discord.Color.green()
        )
        
        for promo in user_promos:
            embed.add_field(
                name=f"Code: `{promo.code}`",
                value=(
                    f"Réduction: **{promo.discount_percent}%**\n"
                    f"Valide jusqu'au: <t:{int(promo.valid_until.timestamp())}:F>\n"
                    f"Type: {promo.type.value.replace('_', ' ').title()}"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed, ephemeral=True)


class OpenClawEvents(commands.Cog):
    """Événements OpenClaw automatiques"""
    
    def __init__(self, bot: commands.Bot, openclaw: OpenClawManager):
        self.bot = bot
        self.openclaw = openclaw
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Nouveau membre - initier le journey"""
        if not self.openclaw:
            return
            
        from openclaw_manager import UserJourney
        
        self.openclaw.user_journeys[member.id] = UserJourney(
            user_id=member.id,
            joined_at=datetime.utcnow()
        )
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Message - tracker l'engagement"""
        if message.author.bot or not self.openclaw:
            return
            
        user_id = message.author.id
        if user_id in self.openclaw.user_journeys:
            journey = self.openclaw.user_journeys[user_id]
            journey.messages_sent += 1
            journey.last_active_at = datetime.utcnow()
            
            # Premier message
            if not journey.first_message_at:
                journey.first_message_at = datetime.utcnow()
                
                # Tag comme actif
                journey.tags.append("active_user")


async def setup(bot: commands.Bot):
    """Setup du cog OpenClaw"""
    await bot.add_cog(OpenClawCommands(bot))
