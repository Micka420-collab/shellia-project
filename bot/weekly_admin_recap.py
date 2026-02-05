"""
📊 SYSTÈME DE RÉCAP HEBDOMADAIRE ADMIN - Shellia AI
L'IA génère un récapitulatif complet chaque semaine pour les admins
"""

import discord
from discord.ext import commands, tasks
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeeklyMetrics:
    """Métriques de la semaine"""
    # Communauté
    new_members: int
    total_members: int
    active_members: int
    messages_sent: int
    
    # Économie
    revenue: float
    mrr: float
    new_subscriptions: int
    churned_subscriptions: int
    
    # Giveaways
    giveaways_completed: int
    giveaway_participants: int
    giveaway_cost: float
    giveaway_roi: float
    
    # Marketing
    promotions_sent: int
    promotions_converted: int
    conversion_rate: float
    
    # Contenu
    images_generated: int
    ai_requests: int
    api_cost: float
    
    # Modération
    warns_issued: int
    bans_issued: int
    tickets_resolved: int


class WeeklyAdminRecap:
    """
    📊 Génère un récapitulatif hebdomadaire complet pour les admins
    L'IA analyse les données et donne des recommandations
    """
    
    def __init__(self, bot: commands.Bot, ai_engine=None, db=None):
        self.bot = bot
        self.ai_engine = ai_engine
        self.db = db
        
        self.admin_channel_id: Optional[int] = None
        self.recap_day = 0  # 0 = Lundi, 6 = Dimanche
        self.recap_hour = 9  # 9h du matin
        
        self.recap_task = None
        
    async def setup(self, admin_channel_id: int, day: int = 0, hour: int = 9):
        """Configure le système"""
        self.admin_channel_id = admin_channel_id
        self.recap_day = day
        self.recap_hour = hour
        
        # Démarrer la tâche de récap
        self.recap_task = self.bot.loop.create_task(self._weekly_recap_loop())
        
        logger.info(f"✅ WeeklyAdminRecap configuré (jour={day}, heure={hour})")
        
    async def _weekly_recap_loop(self):
        """Boucle de récap hebdomadaire"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                now = datetime.utcnow()
                
                # Vérifier si c'est le jour et l'heure du récap
                if now.weekday() == self.recap_day and now.hour == self.recap_hour:
                    await self._generate_and_send_recap()
                    
                    # Attendre 1 jour pour éviter les doublons
                    await asyncio.sleep(86400)
                else:
                    # Vérifier toutes les heures
                    await asyncio.sleep(3600)
                    
            except Exception as e:
                logger.error(f"Erreur récap hebdomadaire: {e}")
                await asyncio.sleep(3600)
                
    async def _generate_and_send_recap(self):
        """Génère et envoie le récap"""
        logger.info("📊 Génération du récap hebdomadaire...")
        
        # 1. Collecter les données
        metrics = await self._collect_weekly_metrics()
        
        # 2. Générer l'analyse avec l'IA
        analysis = await self._generate_ai_analysis(metrics)
        
        # 3. Créer l'embed
        embed = await self._create_recap_embed(metrics, analysis)
        
        # 4. Envoyer
        await self._send_recap(embed, metrics)
        
        # 5. Sauvegarder
        await self._save_recap(metrics, analysis)
        
        logger.info("✅ Récap hebdomadaire envoyé")
        
    async def _collect_weekly_metrics(self) -> WeeklyMetrics:
        """Collecte les métriques de la semaine"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        if not self.db:
            return WeeklyMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            
        # Communauté
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM users WHERE created_at > %s",
            (week_ago,)
        )
        new_members = result[0]['count'] if result else 0
        
        result = await self.db.fetch("SELECT COUNT(*) as count FROM users")
        total_members = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM users WHERE last_active_at > %s",
            (week_ago,)
        )
        active_members = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COALESCE(SUM(message_count), 0) as count FROM daily_stats WHERE date > %s",
            (week_ago,)
        )
        messages_sent = result[0]['count'] if result else 0
        
        # Économie
        result = await self.db.fetch(
            """
            SELECT COALESCE(SUM(amount), 0) as revenue,
                   COUNT(*) as new_subs
            FROM payments 
            WHERE created_at > %s AND status = 'completed'
            """,
            (week_ago,)
        )
        revenue = result[0]['revenue'] if result else 0
        new_subscriptions = result[0]['new_subs'] if result else 0
        
        result = await self.db.fetch(
            """
            SELECT COALESCE(SUM(monthly_value), 0) as mrr
            FROM user_subscriptions 
            WHERE status = 'active'
            """
        )
        mrr = result[0]['mrr'] if result else 0
        
        result = await self.db.fetch(
            """
            SELECT COUNT(*) as churned
            FROM user_subscriptions 
            WHERE status = 'cancelled' AND cancelled_at > %s
            """,
            (week_ago,)
        )
        churned_subscriptions = result[0]['churned'] if result else 0
        
        # Giveaways
        result = await self.db.fetch(
            """
            SELECT COUNT(*) as completed,
                   COALESCE(SUM(cost), 0) as cost,
                   COALESCE(SUM(new_users), 0) as participants
            FROM giveaway_roi_analysis 
            WHERE recorded_at > %s
            """,
            (week_ago,)
        )
        giveaways_completed = result[0]['completed'] if result else 0
        giveaway_cost = result[0]['cost'] if result else 0
        giveaway_participants = result[0]['participants'] if result else 0
        
        # Calculer ROI moyen
        result = await self.db.fetch(
            "SELECT AVG(roi_ratio) as avg_roi FROM giveaway_roi_analysis WHERE recorded_at > %s",
            (week_ago,)
        )
        giveaway_roi = result[0]['avg_roi'] if result and result[0]['avg_roi'] else 0
        
        # Marketing
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM user_promotions WHERE created_at > %s",
            (week_ago,)
        )
        promotions_sent = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            """
            SELECT COUNT(*) as converted
            FROM promotion_stats 
            WHERE converted_to_paid = TRUE AND created_at > %s
            """,
            (week_ago,)
        )
        promotions_converted = result[0]['converted'] if result else 0
        
        conversion_rate = (promotions_converted / promotions_sent * 100) if promotions_sent > 0 else 0
        
        # Contenu
        result = await self.db.fetch(
            "SELECT COALESCE(SUM(images_generated), 0) as count FROM daily_stats WHERE date > %s",
            (week_ago,)
        )
        images_generated = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COALESCE(SUM(ai_requests), 0) as count FROM daily_stats WHERE date > %s",
            (week_ago,)
        )
        ai_requests = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COALESCE(SUM(api_cost), 0) as cost FROM daily_stats WHERE date > %s",
            (week_ago,)
        )
        api_cost = result[0]['cost'] if result else 0
        
        # Modération
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM moderation_logs WHERE action = 'warn' AND created_at > %s",
            (week_ago,)
        )
        warns_issued = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM moderation_logs WHERE action = 'ban' AND created_at > %s",
            (week_ago,)
        )
        bans_issued = result[0]['count'] if result else 0
        
        result = await self.db.fetch(
            "SELECT COUNT(*) as count FROM support_tickets WHERE status = 'resolved' AND resolved_at > %s",
            (week_ago,)
        )
        tickets_resolved = result[0]['count'] if result else 0
        
        return WeeklyMetrics(
            new_members=new_members,
            total_members=total_members,
            active_members=active_members,
            messages_sent=messages_sent,
            revenue=revenue,
            mrr=mrr,
            new_subscriptions=new_subscriptions,
            churned_subscriptions=churned_subscriptions,
            giveaways_completed=giveaways_completed,
            giveaway_participants=giveaway_participants,
            giveaway_cost=giveaway_cost,
            giveaway_roi=giveaway_roi,
            promotions_sent=promotions_sent,
            promotions_converted=promotions_converted,
            conversion_rate=conversion_rate,
            images_generated=images_generated,
            ai_requests=ai_requests,
            api_cost=api_cost,
            warns_issued=warns_issued,
            bans_issued=bans_issued,
            tickets_resolved=tickets_resolved
        )
        
    async def _generate_ai_analysis(self, metrics: WeeklyMetrics) -> Dict[str, Any]:
        """Génère l'analyse avec l'IA"""
        
        # Préparer le contexte pour l'IA
        context = f"""
        MÉTRIQUES DE LA SEMAINE:
        
        COMMUNAUTÉ:
        - Nouveaux membres: {metrics.new_members}
        - Total membres: {metrics.total_members}
        - Membres actifs: {metrics.active_members}
        - Messages envoyés: {metrics.messages_sent}
        
        ÉCONOMIE:
        - Revenus: €{metrics.revenue:.2f}
        - MRR: €{metrics.mrr:.2f}
        - Nouveaux abonnements: {metrics.new_subscriptions}
        - Désabonnements: {metrics.churned_subscriptions}
        
        GIVEAWAYS:
        - Giveaways terminés: {metrics.giveaways_completed}
        - Participants: {metrics.giveaway_participants}
        - Coût: €{metrics.giveaway_cost:.2f}
        - ROI: {metrics.giveaway_roi:.2f}x
        
        MARKETING:
        - Promotions envoyées: {metrics.promotions_sent}
        - Conversions: {metrics.promotions_converted}
        - Taux de conversion: {metrics.conversion_rate:.1f}%
        
        CONTENU:
        - Images générées: {metrics.images_generated}
        - Requêtes IA: {metrics.ai_requests}
        - Coût API: €{metrics.api_cost:.2f}
        
        MODÉRATION:
        - Avertissements: {metrics.warns_issued}
        - Bannissements: {metrics.bans_issued}
        - Tickets résolus: {metrics.tickets_resolved}
        """
        
        prompt = f"""
Tu es une analyste business experte. Analyse ces métriques hebdomadaires et fournis:

1. UN RÉSUMÉ EXÉCUTIF (2-3 phrases)
2. POINTS FORTS (3 points max)
3. POINTS À AMÉLIORER (3 points max)
4. RECOMMANDATIONS ACTIONNABLES (3 actions concrètes)
5. PRÉVISIONS POUR LA SEMAINE PROCHAINE

Soyes concise et directe. Format pour Discord (utilise des emojis et du gras).

{context}
"""
        
        if self.ai_engine:
            try:
                ai_response = await self.ai_engine.generate_text(prompt)
                return self._parse_ai_analysis(ai_response)
            except Exception as e:
                logger.error(f"Erreur analyse IA: {e}")
                
        # Fallback
        return self._generate_fallback_analysis(metrics)
        
    def _parse_ai_analysis(self, response: str) -> Dict[str, Any]:
        """Parse la réponse de l'IA"""
        # Structure simple pour l'instant
        return {
            "executive_summary": response[:500],
            "strengths": ["Croissance communautaire", "Rentabilité giveaways", "Engagement élevé"],
            "weaknesses": ["Churn à surveiller", "Conversion promotions", "Coûts API"],
            "recommendations": [
                "Lancer une campagne winback",
                "Optimiser les promotions",
                "Négocier tarifs API"
            ],
            "predictions": "Croissance stable attendue"
        }
        
    def _generate_fallback_analysis(self, metrics: WeeklyMetrics) -> Dict[str, Any]:
        """Analyse de fallback si l'IA ne répond pas"""
        
        # Calculer les tendances simples
        strengths = []
        weaknesses = []
        recommendations = []
        
        if metrics.new_members > 50:
            strengths.append(f"📈 Croissance excellente: +{metrics.new_members} membres")
        elif metrics.new_members < 10:
            weaknesses.append("📉 Croissance faible, campagne marketing nécessaire")
            recommendations.append("Lancer une campagne de parrainage boostée")
            
        if metrics.giveaway_roi >= 2:
            strengths.append(f"🎁 Giveaways rentables (ROI: {metrics.giveaway_roi:.2f}x)")
        else:
            weaknesses.append("📉 ROI giveaways faible")
            recommendations.append("Réduire les récompenses ou cibler mieux")
            
        if metrics.revenue > 500:
            strengths.append(f"💰 Bonnes performances économiques (€{metrics.revenue:.2f})")
            
        if metrics.churned_subscriptions > metrics.new_subscriptions:
            weaknesses.append("🔄 Churn élevé, plus de pertes que de gains")
            recommendations.append("Renforcer le programme de rétention")
            
        if metrics.conversion_rate < 5:
            weaknesses.append(f"📉 Taux de conversion faible ({metrics.conversion_rate:.1f}%)")
            recommendations.append("Améliorer les landing pages et offres")
            
        if not strengths:
            strengths.append("✅ Serveur stable et opérationnel")
            
        if not weaknesses:
            weaknesses.append("⚠️ Rien de particulier à signaler")
            
        if not recommendations:
            recommendations.append("Continuer les bonnes pratiques actuelles")
            
        return {
            "executive_summary": f"Semaine {'exceptionnelle' if metrics.new_members > 100 else 'correcte' if metrics.new_members > 30 else 'difficile'} avec {metrics.new_members} nouveaux membres et €{metrics.revenue:.2f} de revenus.",
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:3],
            "recommendations": recommendations[:3],
            "predictions": "Stabilité attendue si les actions recommandées sont appliquées."
        }
        
    async def _create_recap_embed(
        self, 
        metrics: WeeklyMetrics, 
        analysis: Dict[str, Any]
    ) -> discord.Embed:
        """Crée l'embed du récap"""
        
        embed = discord.Embed(
            title="📊 RÉCAP HEBDOMADAIRE ADMIN",
            description=analysis["executive_summary"],
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Section Communauté
        embed.add_field(
            name="👥 Communauté",
            value=(
                f"• **+{metrics.new_members}** nouveaux\n"
                f"• **{metrics.total_members}** total\n"
                f"• **{metrics.active_members}** actifs\n"
                f"• **{metrics.messages_sent:,}** messages"
            ),
            inline=True
        )
        
        # Section Économie
        embed.add_field(
            name="💰 Économie",
            value=(
                f"• **€{metrics.revenue:.2f}** revenus\n"
                f"• **€{metrics.mrr:.2f}** MRR\n"
                f"• **+{metrics.new_subscriptions}** nouveaux\n"
                f"• **-{metrics.churned_subscriptions}** churn"
            ),
            inline=True
        )
        
        # Section Giveaways
        embed.add_field(
            name="🎁 Giveaways",
            value=(
                f"• **{metrics.giveaways_completed}** terminés\n"
                f"• **{metrics.giveaway_participants}** participants\n"
                f"• **€{metrics.giveaway_cost:.2f}** coût\n"
                f"• **{metrics.giveaway_roi:.2f}x** ROI"
            ),
            inline=True
        )
        
        # Section Marketing
        embed.add_field(
            name="📢 Marketing",
            value=(
                f"• **{metrics.promotions_sent}** promos\n"
                f"• **{metrics.promotions_converted}** conversions\n"
                f"• **{metrics.conversion_rate:.1f}%** taux conv."
            ),
            inline=True
        )
        
        # Section Contenu
        embed.add_field(
            name="🤖 Contenu IA",
            value=(
                f"• **{metrics.images_generated}** images\n"
                f"• **{metrics.ai_requests:,}** requêtes\n"
                f"• **€{metrics.api_cost:.2f}** coût API"
            ),
            inline=True
        )
        
        # Section Modération
        embed.add_field(
            name="🛡️ Modération",
            value=(
                f"• **{metrics.warns_issued}** warns\n"
                f"• **{metrics.bans_issued}** bans\n"
                f"• **{metrics.tickets_resolved}** tickets"
            ),
            inline=True
        )
        
        # Points forts
        if analysis["strengths"]:
            embed.add_field(
                name="✅ Points Forts",
                value="\n".join([f"• {s}" for s in analysis["strengths"]]),
                inline=False
            )
            
        # Points à améliorer
        if analysis["weaknesses"]:
            embed.add_field(
                name="⚠️ À Surveiller",
                value="\n".join([f"• {w}" for w in analysis["weaknesses"]]),
                inline=False
            )
            
        # Recommandations
        if analysis["recommendations"]:
            embed.add_field(
                name="💡 Recommandations",
                value="\n".join([f"• {r}" for r in analysis["recommendations"]]),
                inline=False
            )
            
        embed.set_footer(text="Généré automatiquement par Shellia AI • Analyse hebdomadaire")
        
        return embed
        
    async def _send_recap(self, embed: discord.Embed, metrics: WeeklyMetrics):
        """Envoie le récap"""
        if not self.admin_channel_id:
            return
            
        channel = self.bot.get_channel(self.admin_channel_id)
        if not channel:
            logger.error("Channel admin non trouvé")
            return
            
        # Envoyer le récap
        await channel.send(content="📊 **RÉCAP HEBDOMADAIRE** @here", embed=embed)
        
        # Envoyer aussi un résumé en MP aux super admins
        await self._notify_super_admins(embed)
        
    async def _notify_super_admins(self, embed: discord.Embed):
        """Notifie les super admins en MP"""
        # Liste des super admins (à configurer)
        super_admin_ids = []  # Remplir avec les IDs
        
        for admin_id in super_admin_ids:
            try:
                user = self.bot.get_user(admin_id)
                if user:
                    await user.send(
                        content="📊 Récap hebdomadaire disponible dans le canal admin",
                        embed=embed
                    )
            except:
                pass
                
    async def _save_recap(self, metrics: WeeklyMetrics, analysis: Dict):
        """Sauvegarde le récap en DB"""
        if not self.db:
            return
            
        await self.db.execute(
            """
            INSERT INTO weekly_recaps 
            (week_start, new_members, total_members, revenue, mrr, giveaway_roi, 
             conversion_rate, analysis_summary, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                datetime.utcnow() - timedelta(days=7),
                metrics.new_members,
                metrics.total_members,
                metrics.revenue,
                metrics.mrr,
                metrics.giveaway_roi,
                metrics.conversion_rate,
                json.dumps(analysis)
            )
        )
        
    async def force_recap(self, admin_channel: discord.TextChannel):
        """Force l'envoi d'un récap immédiat (admin only)"""
        metrics = await self._collect_weekly_metrics()
        analysis = await self._generate_ai_analysis(metrics)
        embed = await self._create_recap_embed(metrics, analysis)
        
        await admin_channel.send(content="📊 **RÉCAP FORCÉ**", embed=embed)
        
        return True
        
    def get_last_recap_date(self) -> Optional[datetime]:
        """Retourne la date du dernier récap"""
        # À implémenter avec la DB
        return None
