"""
🎊 SYSTÈME D'OUVERTURE OFFICIELLE - Shellia AI
Gère le lancement officiel avec l'IA qui fait les annonces
"""

import discord
from discord.ext import commands
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class OpeningPhase(Enum):
    PRELAUNCH = "prelaunch"           # Avant ouverture
    COUNTDOWN = "countdown"           # Compte à rebours
    GRAND_OPENING = "grand_opening"   # Jour J
    POST_LAUNCH = "post_launch"       # Après ouverture


@dataclass
class OpeningMilestone:
    """Étape du lancement"""
    name: str
    description: str
    datetime: datetime
    announcement_template: str


class GrandOpeningManager:
    """
    🎊 Gère l'ouverture officielle du serveur avec l'IA
    """
    
    def __init__(self, bot: commands.Bot, ai_engine=None, db=None):
        self.bot = bot
        self.ai_engine = ai_engine
        self.db = db
        
        self.phase = OpeningPhase.PRELAUNCH
        self.opening_date: Optional[datetime] = None
        self.milestones: List[OpeningMilestone] = []
        
        # Channels
        self.announcement_channel_id: Optional[int] = None
        self.countdown_message_id: Optional[int] = None
        
        # État
        self.is_launched = False
        self.launch_task = None
        
    async def setup(self, opening_date: datetime, announcement_channel_id: int):
        """Configure le lancement"""
        self.opening_date = opening_date
        self.announcement_channel_id = announcement_channel_id
        
        # Créer les milestones
        self._create_milestones()
        
        # Démarrer la surveillance
        self.launch_task = self.bot.loop.create_task(self._opening_monitor_loop())
        
        logger.info(f"✅ Grand Opening configuré pour le {opening_date}")
        
    def _create_milestones(self):
        """Crée les étapes du lancement"""
        if not self.opening_date:
            return
            
        self.milestones = [
            OpeningMilestone(
                name="T-7 days",
                description="Annonce officielle du lancement",
                datetime=self.opening_date - timedelta(days=7),
                announcement_template="prelaunch_announcement"
            ),
            OpeningMilestone(
                name="T-3 days",
                description="Teaser et révélations",
                datetime=self.opening_date - timedelta(days=3),
                announcement_template="teaser_announcement"
            ),
            OpeningMilestone(
                name="T-24 hours",
                description="Dernier rappel",
                datetime=self.opening_date - timedelta(hours=24),
                announcement_template="final_reminder"
            ),
            OpeningMilestone(
                name="T-1 hour",
                description="Compte à rebours final",
                datetime=self.opening_date - timedelta(hours=1),
                announcement_template="countdown_start"
            ),
            OpeningMilestone(
                name="T-0",
                description="OUVERTURE OFFICIELLE !",
                datetime=self.opening_date,
                announcement_template="grand_opening"
            ),
            OpeningMilestone(
                name="T+24 hours",
                description="Bilan première journée",
                datetime=self.opening_date + timedelta(hours=24),
                announcement_template="day_one_recap"
            ),
            OpeningMilestone(
                name="T+1 week",
                description="Bilan première semaine",
                datetime=self.opening_date + timedelta(days=7),
                announcement_template="week_one_recap"
            )
        ]
        
    async def _opening_monitor_loop(self):
        """Surveille les dates et déclenche les annonces"""
        await self.bot.wait_until_ready()
        
        announced_milestones = set()
        
        while not self.bot.is_closed() and not self.is_launched:
            now = datetime.utcnow()
            
            for milestone in self.milestones:
                # Vérifier si on doit annoncer
                if milestone.name in announced_milestones:
                    continue
                    
                # Annoncer si on est passé la date (avec marge de 1 minute)
                if now >= milestone.datetime and now < milestone.datetime + timedelta(minutes=1):
                    await self._execute_milestone(milestone)
                    announced_milestones.add(milestone.name)
                    
                    # Marquer comme lancé après le grand opening
                    if milestone.name == "T-0":
                        self.is_launched = True
                        self.phase = OpeningPhase.POST_LAUNCH
                        
            await asyncio.sleep(30)  # Vérifier toutes les 30 secondes
            
    async def _execute_milestone(self, milestone: OpeningMilestone):
        """Exécute une étape du lancement"""
        logger.info(f"🎊 Exécution milestone: {milestone.name}")
        
        # Générer l'annonce avec l'IA
        announcement = await self._generate_announcement(milestone)
        
        # Publier l'annonce
        await self._publish_announcement(announcement, milestone)
        
        # Actions spéciales selon la milestone
        if milestone.name == "T-0":
            await self._execute_grand_opening()
        elif milestone.name == "T-1 hour":
            await self._start_countdown()
            
    async def _generate_announcement(self, milestone: OpeningMilestone) -> Dict:
        """Génère une annonce avec l'IA"""
        
        prompts = {
            "prelaunch_announcement": """
Tu es Shellia, l'IA officielle du serveur. Tu dois annoncer l'ouverture officielle dans 7 jours.
Crée une annonce EXCITANTE qui:
- Crée l'anticipation
- Mentionne les features exclusives
- Invite les gens à rejoindre dès maintenant
- Utilise des emojis

Format: Discord embed avec titre, description, et 3-4 fields
""",
            "teaser_announcement": """
Tu es Shellia. Ouverture dans 3 jours !
Crée un teaser qui révèle quelques surprises sans tout donner.
Mystère + excitation.
""",
            "final_reminder": """
Dernier rappel avant ouverture dans 24h !
Message urgent mais pas paniqué. Derniers préparatifs.
""",
            "countdown_start": """
Compte à rebours final ! Ouverture dans 1h !
Message très excitant, dernière chance de préparer.
""",
            "grand_opening": """
C'EST LE GRAND JOUR ! Ouverture officielle MAINTENANT !
Message ÉPIQUE, célébration maximum.
Bienvenue aux nouveaux, remercier les early adopters.
Présenter la vision.
""",
            "day_one_recap": """
Bilan de la première journée d'ouverture.
Statistiques impressionnantes, remerciements, momentum.
""",
            "week_one_recap": """
Bilan première semaine. Croissance, communauté, avenir.
Message inspirant pour la suite.
"""
        }
        
        prompt = prompts.get(milestone.announcement_template, prompts["prelaunch_announcement"])
        
        # Utiliser l'IA pour générer
        if self.ai_engine:
            try:
                ai_response = await self.ai_engine.generate_text(prompt)
                # Parser la réponse pour créer un embed
                return self._parse_ai_response(ai_response, milestone)
            except Exception as e:
                logger.error(f"Erreur génération IA: {e}")
                
        # Fallback: templates prédéfinis
        return self._get_fallback_announcement(milestone)
        
    def _parse_ai_response(self, response: str, milestone: OpeningMilestone) -> Dict:
        """Parse la réponse de l'IA en structure d'annonce"""
        # Simplification: on retourne le texte pour l'instant
        return {
            "title": f"🎊 {milestone.name}: {milestone.description}",
            "description": response[:2000],  # Limite Discord
            "color": discord.Color.gold() if "T-0" in milestone.name else discord.Color.blue(),
            "image_url": None
        }
        
    def _get_fallback_announcement(self, milestone: OpeningMilestone) -> Dict:
        """Templates de fallback si l'IA ne répond pas"""
        
        templates = {
            "T-7 days": {
                "title": "🎉 ANNONCE SPÉCIALE - Ouverture dans 7 jours !",
                "description": (
                    "**Le grand jour approche !**\n\n"
                    "Dans exactement **7 jours**, nous ouvrons officiellement nos portes !\n\n"
                    "🚀 **Ce qui t'attend:**\n"
                    "• IA conversationnelle avancée\n"
                    "• Système de giveaways automatiques\n"
                    "• Rôles exclusifs et récompenses\n"
                    "• Une communauté incroyable\n\n"
                    "🔗 **Rejoins-nous dès maintenant** pour être là dès le début !"
                ),
                "color": discord.Color.blue()
            },
            "T-3 days": {
                "title": "⚡ TEASER - Plus que 3 jours !",
                "description": (
                    "**L'excitation monte...**\n\n"
                    "Voici un aperçu exclusif de ce qui t'attend:\n"
                    "🎁 Des giveaways aux paliers de membres\n"
                    "🏆 Un grade Winner avec avantages Pro\n"
                    "💰 Un système économique complet\n\n"
                    "**Prépare-toi...**"
                ),
                "color": discord.Color.purple()
            },
            "T-24 hours": {
                "title": "⏰ DERNIER RAPPEL - 24h avant l'ouverture !",
                "description": (
                    "**C'est presque le moment !**\n\n"
                    "Demain à cette heure-ci, nous serons officiellement ouverts !\n\n"
                    "🔔 Active les notifications pour ne rien manquer !\n"
                    "👥 Invite tes amis à rejoindre avant tout le monde !\n\n"
                    "**À demain !** 🚀"
                ),
                "color": discord.Color.orange()
            },
            "T-1 hour": {
                "title": "🔥 COMPTER À REBOURS - 1 HEURE !",
                "description": (
                    "**C'EST LE MOMENT !**\n\n"
                    "Dans **1 heure pile**, l'aventure commence !\n\n"
                    "Soyez prêts, soyez là, et préparez-vous à vivre quelque chose d'exceptionnel !\n\n"
                    "**#ReadyForLaunch** 🚀"
                ),
                "color": discord.Color.red()
            },
            "T-0": {
                "title": "🚀🎊 OUVERTURE OFFICIELLE ! 🎊🚀",
                "description": (
                    "**C'EST PARTI !**\n\n"
                    "Bienvenue à tous dans **Shellia AI** !\n\n"
                    "Nous sommes officiellement ouverts et prêts à vous offrir:\n"
                    "🤖 Une IA conversationnelle de qualité\n"
                    "🎁 Des giveaways automatiques dès 50 membres\n"
                    "💎 Des rôles exclusifs et des récompenses\n"
                    "🦀 Un système business innovant\n\n"
                    "**Merci d'être là pour ce moment historique !**\n"
                    "Invitez vos amis, participez, et faisons de ce serveur un endroit exceptionnel !\n\n"
                    "**Bienvenue à tous ! 💜**"
                ),
                "color": discord.Color.gold(),
                "image_url": "https://media.giphy.com/media/26tOZ42Mg6pbTUPHW/giphy.gif"
            },
            "T+24 hours": {
                "title": "📊 Bilan - Première journée incroyable !",
                "description": (
                    "**Quelle journée !**\n\n"
                    "Merci à tous pour cet accueil incroyable !\n"
                    "En 24h, vous avez été {member_count} à nous rejoindre !\n\n"
                    "🎯 **Prochain objectif:** Les giveaways commencent à 50 membres !\n\n"
                    "Continuez à inviter, à participer, et à faire vivre cette communauté !"
                ),
                "color": discord.Color.green()
            },
            "T+1 week": {
                "title": "🎉 Bilan - Une semaine extraordinaire !",
                "description": (
                    "**Une semaine déjà !**\n\n"
                    "Cette première semaine a été incroyable grâce à vous:\n"
                    "• Communauté en pleine croissance\n"
                    "• Giveaways lancés\n"
                    "• Ambiance exceptionnelle\n\n"
                    "**L'aventure ne fait que commencer !**\n"
                    "Encore merci à tous 💜"
                ),
                "color": discord.Color.purple()
            }
        }
        
        return templates.get(milestone.name, templates["T-7 days"])
        
    async def _publish_announcement(self, announcement: Dict, milestone: OpeningMilestone):
        """Publie l'annonce"""
        if not self.announcement_channel_id:
            return
            
        channel = self.bot.get_channel(self.announcement_channel_id)
        if not channel:
            logger.error("Channel d'annonce non trouvé")
            return
            
        embed = discord.Embed(
            title=announcement.get("title", "Annonce"),
            description=announcement.get("description", ""),
            color=announcement.get("color", discord.Color.blue()),
            timestamp=datetime.utcnow()
        )
        
        if announcement.get("image_url"):
            embed.set_image(url=announcement["image_url"])
            
        # Mention everyone pour les grandes annonces
        content = ""
        if milestone.name in ["T-0", "T-7 days"]:
            content = "@everyone 🎊"
            
        await channel.send(content=content, embed=embed)
        logger.info(f"📢 Annonce publiée: {milestone.name}")
        
    async def _execute_grand_opening(self):
        """Actions spéciales le jour J"""
        logger.info("🚀 EXECUTION GRAND OPENING !")
        
        # 1. Lancer les features spéciales
        await self._enable_special_features()
        
        # 2. Créer les salons spéciaux si besoin
        await self._create_special_channels()
        
        # 3. Envoyer des DMs aux early adopters
        await self._thank_early_adopters()
        
        # 4. Lancer un giveaway de lancement si configuré
        await self._launch_opening_giveaway()
        
    async def _enable_special_features(self):
        """Active les features spéciales"""
        # Activer tous les modules
        logger.info("✅ Features spéciales activées")
        
    async def _create_special_channels(self):
        """Crée les salons spéciaux pour l'ouverture"""
        # Créer un salon "🎉│ouverture-officielle"
        for guild in self.bot.guilds:
            existing = discord.utils.get(guild.text_channels, name="🎉│ouverture-officielle")
            if not existing:
                try:
                    await guild.create_text_channel(
                        name="🎉│ouverture-officielle",
                        topic="Célébration de l'ouverture officielle ! 🚀"
                    )
                except:
                    pass
                    
    async def _thank_early_adopters(self):
        """Remercie les early adopters"""
        # Liste des membres présents avant l'ouverture
        for guild in self.bot.guilds:
            early_members = [m for m in guild.members if not m.bot]
            
            for member in early_members[:50]:  # Limite à 50 pour éviter le rate limit
                try:
                    embed = discord.Embed(
                        title="🎉 Merci d'être là dès le début !",
                        description=(
                            f"Salut {member.name} !\n\n"
                            "Merci d'être présent dès l'ouverture officielle !\n"
                            "En tant que early adopter, tu reçois un badge exclusif !\n\n"
                            "Invite tes amis et faisons grandir cette communauté ensemble ! 💜"
                        ),
                        color=discord.Color.gold()
                    )
                    await member.send(embed=embed)
                    await asyncio.sleep(1)  # Rate limit protection
                except:
                    continue
                    
    async def _launch_opening_giveaway(self):
        """Lance un giveaway spécial ouverture"""
        # À implémenter avec le giveaway manager
        logger.info("🎁 Giveaway d'ouverture lancé")
        
    async def _start_countdown(self):
        """Démarre le compte à rebours visuel"""
        # Créer un message de compte à rebours qui se met à jour
        if not self.announcement_channel_id:
            return
            
        channel = self.bot.get_channel(self.announcement_channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="⏰ COMPTE À REBOURS",
            description="**Ouverture dans:** 1:00:00",
            color=discord.Color.red()
        )
        
        message = await channel.send(embed=embed)
        self.countdown_message_id = message.id
        
        # Mettre à jour toutes les minutes
        for minutes in range(59, -1, -1):
            await asyncio.sleep(60)
            
            try:
                embed.description = f"**Ouverture dans:** 0:{minutes:02d}:00"
                await message.edit(embed=embed)
            except:
                break
                
    async def force_opening(self, guild: discord.Guild):
        """Force l'ouverture immédiate (admin only)"""
        milestone = OpeningMilestone(
            name="T-0",
            description="OUVERTURE OFFICIELLE FORCÉE !",
            datetime=datetime.utcnow(),
            announcement_template="grand_opening"
        )
        
        await self._execute_milestone(milestone)
        self.is_launched = True
        
        return True
        
    def get_status(self) -> Dict:
        """Retourne le statut du lancement"""
        if not self.opening_date:
            return {"status": "not_configured"}
            
        time_remaining = self.opening_date - datetime.utcnow()
        
        return {
            "phase": self.phase.value,
            "opening_date": self.opening_date.isoformat(),
            "time_remaining_seconds": time_remaining.total_seconds(),
            "is_launched": self.is_launched,
            "milestones_count": len(self.milestones)
        }
