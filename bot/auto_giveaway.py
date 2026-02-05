"""
🎁 Système de Giveaways Automatiques aux Paliers
Déclenche des giveaways automatiquement quand des paliers de membres sont atteints
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import asyncio
import random
import json
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GiveawayStatus(Enum):
    PENDING = "pending"      # En attente du palier
    ACTIVE = "active"        # En cours
    ENDED = "ended"          # Terminé
    CANCELLED = "cancelled"  # Annulé


@dataclass
class MilestoneReward:
    """Récompense pour un palier"""
    member_count: int
    role_reward: Optional[int] = None  # ID du rôle à donner
    currency_reward: int = 0           # Montant de la monnaie virtuelle
    nitro_reward: bool = False         # Nitro Discord
    custom_reward: str = ""            # Description récompense personnalisée
    giveaway_duration_hours: int = 24  # Durée du giveaway
    winners_count: int = 1             # Nombre de gagnants
    description: str = ""              # Description du giveaway
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MilestoneReward':
        return cls(**data)


@dataclass
class GiveawayEntry:
    """Participation à un giveaway"""
    user_id: int
    joined_at: datetime
    message_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat(),
            'message_id': self.message_id
        }


@dataclass
class ActiveGiveaway:
    """Giveaway en cours"""
    id: str
    milestone: int
    reward: MilestoneReward
    channel_id: int
    message_id: Optional[int]
    host_id: int
    started_at: datetime
    ends_at: datetime
    entries: List[GiveawayEntry]
    status: GiveawayStatus
    winners: List[int]
    
    @property
    def entry_count(self) -> int:
        return len(self.entries)
    
    @property
    def time_remaining(self) -> timedelta:
        return self.ends_at - datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'milestone': self.milestone,
            'reward': self.reward.to_dict(),
            'channel_id': self.channel_id,
            'message_id': self.message_id,
            'host_id': self.host_id,
            'started_at': self.started_at.isoformat(),
            'ends_at': self.ends_at.isoformat(),
            'entries': [e.to_dict() for e in self.entries],
            'status': self.status.value,
            'winners': self.winners
        }


class AutoGiveawayManager:
    """
    Gestionnaire de giveaways automatiques aux paliers
    """
    
    # Paliers par défaut
    DEFAULT_MILESTONES = {
        50: MilestoneReward(
            member_count=50,
            currency_reward=500,
            description="🎉 50 membres ! Merci à tous !",
            giveaway_duration_hours=48,
            winners_count=2
        ),
        100: MilestoneReward(
            member_count=100,
            role_reward=None,  # À configurer
            currency_reward=1000,
            description="🚀 100 membres ! Vous êtes incroyables !",
            giveaway_duration_hours=72,
            winners_count=3
        ),
        250: MilestoneReward(
            member_count=250,
            currency_reward=2500,
            nitro_reward=True,
            description="⭐ 250 membres ! Giveaway NITRO !",
            giveaway_duration_hours=96,
            winners_count=1
        ),
        500: MilestoneReward(
            member_count=500,
            currency_reward=5000,
            custom_reward="Rôle exclusif 'OG Member'",
            description="🔥 500 membres ! Vous êtes une communauté de fou !",
            giveaway_duration_hours=120,
            winners_count=5
        ),
        1000: MilestoneReward(
            member_count=1000,
            currency_reward=10000,
            nitro_reward=True,
            custom_reward="Rôle légendaire + Badge personnalisé",
            description="👑 1000 MEMBRES ! C'EST MONUMENTAL !",
            giveaway_duration_hours=168,  # 1 semaine
            winners_count=10
        ),
        2500: MilestoneReward(
            member_count=2500,
            currency_reward=25000,
            nitro_reward=True,
            custom_reward="Giveaway ULTRA avec récompenses exclusives",
            description="💎 2500 membres ! Communauté ELITE !",
            giveaway_duration_hours=168,
            winners_count=15
        ),
        5000: MilestoneReward(
            member_count=5000,
            currency_reward=50000,
            nitro_reward=True,
            custom_reward="Événement spécial + Rôles exclusifs",
            description="🌟 5000 MEMBRES ! LÉGENDAIRE !",
            giveaway_duration_hours=336,  # 2 semaines
            winners_count=25
        )
    }
    
    def __init__(self, bot: commands.Bot, db=None):
        self.bot = bot
        self.db = db
        self.milestones: Dict[int, MilestoneReward] = self.DEFAULT_MILESTONES.copy()
        self.active_giveaways: Dict[str, ActiveGiveaway] = {}
        self.completed_milestones: set = set()
        self.check_milestones_task = None
        self.update_giveaway_messages_task = None
        self.announcement_channel_id: Optional[int] = None
        self.log_channel_id: Optional[int] = None
        
    async def setup(self, announcement_channel_id: Optional[int] = None):
        """Initialise le gestionnaire"""
        self.announcement_channel_id = announcement_channel_id
        
        # Charger les paliers complétés depuis la DB
        if self.db:
            await self._load_from_db()
        
        # Démarrer les tâches de fond
        self.check_milestones_task = self.bot.loop.create_task(
            self._check_milestones_loop()
        )
        self.update_giveaway_messages_task = self.bot.loop.create_task(
            self._update_giveaway_messages_loop()
        )
        
        logger.info("✅ AutoGiveawayManager initialisé")
        
    async def _load_from_db(self):
        """Charge l'état depuis la base de données"""
        try:
            # Charger les paliers complétés
            result = await self.db.fetch(
                "SELECT milestone FROM completed_milestones WHERE guild_id = %s",
                (self.get_default_guild_id(),)
            )
            self.completed_milestones = {row['milestone'] for row in result}
            
            # Charger les giveaways actifs
            result = await self.db.fetch(
                "SELECT * FROM active_giveaways WHERE status = 'active' AND ends_at > NOW()"
            )
            for row in result:
                giveaway = self._row_to_giveaway(row)
                self.active_giveaways[giveaway.id] = giveaway
                
        except Exception as e:
            logger.error(f"Erreur chargement DB: {e}")
            
    def get_default_guild_id(self) -> int:
        """Récupère l'ID du serveur par défaut"""
        # À configurer selon votre serveur
        return 0
        
    async def _check_milestones_loop(self):
        """Boucle de vérification des paliers"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await self._check_all_guilds()
            except Exception as e:
                logger.error(f"Erreur vérification paliers: {e}")
                
            await asyncio.sleep(300)  # Vérifier toutes les 5 minutes
            
    async def _check_all_guilds(self):
        """Vérifie les paliers pour tous les serveurs"""
        for guild in self.bot.guilds:
            await self._check_guild_milestone(guild)
            
    async def _check_guild_milestone(self, guild: discord.Guild):
        """Vérifie si un palier a été atteint pour un serveur"""
        member_count = guild.member_count
        
        # Chercher le prochain palier non atteint
        for milestone in sorted(self.milestones.keys()):
            if milestone > member_count:
                continue
                
            # Vérifier si ce palier a déjà été célébré
            milestone_key = f"{guild.id}:{milestone}"
            if milestone_key in self.completed_milestones:
                continue
                
            # 🎉 Palier atteint ! Démarrer un giveaway
            await self._trigger_milestone_giveaway(guild, milestone)
            self.completed_milestones.add(milestone_key)
            
            # Sauvegarder dans la DB
            if self.db:
                await self._save_completed_milestone(guild.id, milestone)
                
    async def _trigger_milestone_giveaway(
        self, 
        guild: discord.Guild, 
        milestone: int
    ):
        """Déclenche un giveaway pour un palier atteint"""
        reward = self.milestones[milestone]
        
        # Déterminer le canal d'annonce
        channel = None
        if self.announcement_channel_id:
            channel = guild.get_channel(self.announcement_channel_id)
        
        if not channel:
            # Chercher un canal #giveaways ou #annonces
            for ch in guild.text_channels:
                if any(keyword in ch.name.lower() for keyword in ['giveaway', 'annonces', 'general', 'main']):
                    channel = ch
                    break
                    
        if not channel:
            logger.warning(f"Aucun canal trouvé pour le giveaway sur {guild.name}")
            return
            
        # Créer le giveaway
        giveaway = await self.create_giveaway(
            guild=guild,
            channel=channel,
            milestone=milestone,
            reward=reward,
            host_id=self.bot.user.id
        )
        
        # Annoncer le palier
        await self._announce_milestone(guild, channel, milestone, giveaway)
        
        logger.info(f"🎉 Giveaway démarré pour {milestone} membres sur {guild.name}")
        
    async def create_giveaway(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        milestone: int,
        reward: MilestoneReward,
        host_id: int
    ) -> ActiveGiveaway:
        """Crée un nouveau giveaway"""
        import uuid
        
        giveaway_id = str(uuid.uuid4())[:8]
        
        ends_at = datetime.utcnow() + timedelta(hours=reward.giveaway_duration_hours)
        
        giveaway = ActiveGiveaway(
            id=giveaway_id,
            milestone=milestone,
            reward=reward,
            channel_id=channel.id,
            message_id=None,
            host_id=host_id,
            started_at=datetime.utcnow(),
            ends_at=ends_at,
            entries=[],
            status=GiveawayStatus.ACTIVE,
            winners=[]
        )
        
        # Envoyer le message du giveaway
        message = await self._send_giveaway_message(channel, giveaway)
        giveaway.message_id = message.id
        
        # Ajouter la réaction 🎉
        await message.add_reaction("🎉")
        
        # Stocker
        self.active_giveaways[giveaway_id] = giveaway
        
        # Sauvegarder dans la DB
        if self.db:
            await self._save_giveaway(giveaway)
            
        return giveaway
        
    async def _send_giveaway_message(
        self, 
        channel: discord.TextChannel, 
        giveaway: ActiveGiveaway
    ) -> discord.Message:
        """Envoie le message du giveaway"""
        reward = giveaway.reward
        
        # Construire la description des récompenses
        rewards_list = []
        if reward.currency_reward > 0:
            rewards_list.append(f"💰 {reward.currency_reward:,} coins")
        if reward.nitro_reward:
            rewards_list.append("🎁 Discord Nitro")
        if reward.role_reward:
            role = channel.guild.get_role(reward.role_reward)
            if role:
                rewards_list.append(f"🏷️ Rôle: {role.mention}")
        if reward.custom_reward:
            rewards_list.append(f"✨ {reward.custom_reward}")
            
        embed = discord.Embed(
            title=f"🎉 GIVEWAY PALIER {giveaway.milestone} MEMBRES !",
            description=(
                f"**{reward.description}**\n\n"
                f"{' | '.join(rewards_list)}\n\n"
                f"🎯 **Gagnants:** {reward.winners_count}\n"
                f"⏰ **Termine:** <t:{int(giveaway.ends_at.timestamp())}:R>\n"
                f"🎊 **Participants:** {giveaway.entry_count}\n\n"
                f"Clique sur 🎉 pour participer !"
            ),
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text=f"ID: {giveaway.id} • Organisé par Shellia AI")
        
        message = await channel.send(embed=embed)
        return message
        
    async def _announce_milestone(
        self, 
        guild: discord.Guild, 
        channel: discord.TextChannel,
        milestone: int,
        giveaway: ActiveGiveaway
    ):
        """Annonce le palier atteint"""
        embed = discord.Embed(
            title=f"🎊 PALIER {milestone} MEMBRES ATTEINT !",
            description=(
                f"Incroyable ! Nous avons atteint **{milestone} membres** !\n\n"
                f"Pour célébrer ça, un giveaway automatique vient d'être lancé !\n"
                f"👉 [Clique ici pour participer]({giveaway.message_id})"
            ),
            color=discord.Color.green()
        )
        
        embed.set_image(url="https://media.giphy.com/media/26tOZ42Mg6pbTUPHW/giphy.gif")
        
        await channel.send(embed=embed)
        
    async def add_entry(
        self, 
        giveaway_id: str, 
        user_id: int,
        message_id: Optional[int] = None
    ) -> bool:
        """Ajoute une participation à un giveaway"""
        giveaway = self.active_giveaways.get(giveaway_id)
        if not giveaway:
            return False
            
        if giveaway.status != GiveawayStatus.ACTIVE:
            return False
            
        if datetime.utcnow() > giveaway.ends_at:
            return False
            
        # Vérifier si déjà participé
        if any(e.user_id == user_id for e in giveaway.entries):
            return False
            
        entry = GiveawayEntry(
            user_id=user_id,
            joined_at=datetime.utcnow(),
            message_id=message_id
        )
        
        giveaway.entries.append(entry)
        
        # Mettre à jour la DB
        if self.db:
            await self._save_entry(giveaway_id, entry)
            
        return True
        
    async def remove_entry(self, giveaway_id: str, user_id: int) -> bool:
        """Retire une participation"""
        giveaway = self.active_giveaways.get(giveaway_id)
        if not giveaway:
            return False
            
        giveaway.entries = [e for e in giveaway.entries if e.user_id != user_id]
        
        if self.db:
            await self._remove_entry_db(giveaway_id, user_id)
            
        return True
        
    async def end_giveaway(self, giveaway_id: str, manual: bool = False) -> Optional[ActiveGiveaway]:
        """Termine un giveaway et tire les gagnants"""
        giveaway = self.active_giveaways.get(giveaway_id)
        if not giveaway:
            return None
            
        if giveaway.status == GiveawayStatus.ENDED:
            return giveaway
            
        # Tirer les gagnants
        winners = await self._draw_winners(giveaway)
        giveaway.winners = [w.id for w in winners]
        giveaway.status = GiveawayStatus.ENDED
        
        # Mettre à jour le message
        await self._update_giveaway_ended(giveaway, winners)
        
        # Annoncer les gagnants
        await self._announce_winners(giveaway, winners)
        
        # Attribuer les récompenses
        await self._distribute_rewards(giveaway, winners)
        
        # Mettre à jour la DB
        if self.db:
            await self._update_giveaway_status(giveaway_id, GiveawayStatus.ENDED)
            
        # Nettoyer
        if giveaway_id in self.active_giveaways:
            del self.active_giveaways[giveaway_id]
            
        logger.info(f"Giveaway {giveaway_id} terminé avec {len(winners)} gagnants")
        
        return giveaway
        
    async def _draw_winners(
        self, 
        giveaway: ActiveGiveaway
    ) -> List[discord.Member]:
        """Tire au sort les gagnants"""
        if not giveaway.entries:
            return []
            
        guild = self.bot.get_guild(giveaway.channel_id)
        if not guild:
            return []
            
        # Récupérer les membres valides
        valid_entries = []
        for entry in giveaway.entries:
            member = guild.get_member(entry.user_id)
            if member and not member.bot:
                valid_entries.append(entry)
                
        if not valid_entries:
            return []
            
        # Tirer au sort
        winners_count = min(giveaway.reward.winners_count, len(valid_entries))
        winner_entries = random.sample(valid_entries, winners_count)
        
        winners = []
        for entry in winner_entries:
            member = guild.get_member(entry.user_id)
            if member:
                winners.append(member)
                
        return winners
        
    async def _update_giveaway_ended(
        self, 
        giveaway: ActiveGiveaway, 
        winners: List[discord.Member]
    ):
        """Met à jour le message du giveaway terminé"""
        channel = self.bot.get_channel(giveaway.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(giveaway.message_id)
        except:
            return
            
        winner_mentions = ", ".join([w.mention for w in winners]) if winners else "Aucun"
        
        embed = discord.Embed(
            title=f"🎉 GIVEWAY TERMINÉ - {giveaway.milestone} MEMBRES",
            description=(
                f"**{giveaway.reward.description}**\n\n"
                f"🏆 **Gagnants:** {winner_mentions}\n"
                f"🎊 **Total participants:** {giveaway.entry_count}\n\n"
                f"✅ Félicitations aux gagnants !"
            ),
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text=f"ID: {giveaway.id} • Terminé")
        
        await message.edit(embed=embed)
        await message.clear_reactions()
        
    async def _announce_winners(
        self, 
        giveaway: ActiveGiveaway, 
        winners: List[discord.Member]
    ):
        """Annonce les gagnants"""
        channel = self.bot.get_channel(giveaway.channel_id)
        if not channel:
            return
            
        if not winners:
            await channel.send("😢 Personne n'a participé au giveaway...")
            return
            
        winner_mentions = ", ".join([w.mention for w in winners])
        
        embed = discord.Embed(
            title="🎊 ET LES GAGNANTS SONT...",
            description=f"**{winner_mentions}**\n\nFélicitations ! 🎉",
            color=discord.Color.gold()
        )
        
        embed.set_image(url="https://media.giphy.com/media/l4q8gHsK0DmKUln6w/giphy.gif")
        
        await channel.send(embed=embed)
        
    async def _distribute_rewards(
        self, 
        giveaway: ActiveGiveaway, 
        winners: List[discord.Member]
    ):
        """Distribue les récompenses aux gagnants"""
        reward = giveaway.reward
        
        for winner in winners:
            try:
                # Donner la monnaie virtuelle
                if reward.currency_reward > 0:
                    await self._give_currency(winner.id, reward.currency_reward)
                    
                # Donner le rôle
                if reward.role_reward:
                    role = winner.guild.get_role(reward.role_reward)
                    if role:
                        await winner.add_roles(role, reason=f"Giveaway palier {giveaway.milestone}")
                        
                # Envoyer MP
                await self._send_winner_dm(winner, giveaway, reward)
                
            except Exception as e:
                logger.error(f"Erreur distribution récompense à {winner.id}: {e}")
                
    async def _give_currency(self, user_id: int, amount: int):
        """Donne de la monnaie virtuelle à un utilisateur"""
        if not self.db:
            return
            
        await self.db.execute(
            """
            INSERT INTO user_economy (user_id, balance)
            VALUES (%s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET balance = user_economy.balance + EXCLUDED.balance
            """,
            (user_id, amount)
        )
        
    async def _send_winner_dm(
        self, 
        winner: discord.Member, 
        giveaway: ActiveGiveaway,
        reward: MilestoneReward
    ):
        """Envoie un MP au gagnant"""
        try:
            embed = discord.Embed(
                title="🎉 Félicitations ! Tu as gagné !",
                description=(
                    f"Tu as remporté le giveaway du palier **{giveaway.milestone} membres** !\n\n"
                    f"{'💰 Tu as reçu ' + str(reward.currency_reward) + ' coins' if reward.currency_reward else ''}\n"
                    f"{'🏷️ Un nouveau rôle t\'a été attribué' if reward.role_reward else ''}\n"
                    f"{'✨ ' + reward.custom_reward if reward.custom_reward else ''}\n\n"
                    f"Merci de faire partie de cette incroyable communauté ! 💜"
                ),
                color=discord.Color.gold()
            )
            
            await winner.send(embed=embed)
        except:
            pass  # DM fermés
            
    async def _update_giveaway_messages_loop(self):
        """Met à jour les messages des giveaways actifs"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                await self._update_active_giveaways()
            except Exception as e:
                logger.error(f"Erreur mise à jour giveaways: {e}")
                
            await asyncio.sleep(60)  # Mettre à jour chaque minute
            
    async def _update_active_giveaways(self):
        """Met à jour tous les giveaways actifs"""
        now = datetime.utcnow()
        
        for giveaway_id, giveaway in list(self.active_giveaways.items()):
            # Vérifier si terminé
            if now >= giveaway.ends_at:
                await self.end_giveaway(giveaway_id)
                continue
                
            # Mettre à jour le message (compteur participants)
            await self._refresh_giveaway_message(giveaway)
            
    async def _refresh_giveaway_message(self, giveaway: ActiveGiveaway):
        """Rafraîchit le message d'un giveaway"""
        channel = self.bot.get_channel(giveaway.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(giveaway.message_id)
        except:
            return
            
        # Mettre à jour seulement si le nombre de participants a changé
        # (pour éviter le rate limiting)
        
    # ============ COMMANDES DE GESTION ============
    
    async def add_custom_milestone(
        self, 
        member_count: int, 
        reward: MilestoneReward
    ) -> bool:
        """Ajoute un palier personnalisé"""
        if member_count in self.milestones:
            return False
            
        self.milestones[member_count] = reward
        
        if self.db:
            await self._save_milestone_config(member_count, reward)
            
        return True
        
    async def remove_milestone(self, member_count: int) -> bool:
        """Supprime un palier"""
        if member_count not in self.milestones:
            return False
            
        if member_count in self.DEFAULT_MILESTONES:
            return False  # Ne pas supprimer les paliers par défaut
            
        del self.milestones[member_count]
        
        if self.db:
            await self._remove_milestone_config(member_count)
            
        return True
        
    async def force_giveaway(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        milestone: int,
        host: discord.Member
    ) -> Optional[ActiveGiveaway]:
        """Force le démarrage d'un giveaway (admin uniquement)"""
        if milestone not in self.milestones:
            return None
            
        reward = self.milestones[milestone]
        
        return await self.create_giveaway(
            guild=guild,
            channel=channel,
            milestone=milestone,
            reward=reward,
            host_id=host.id
        )
        
    async def cancel_giveaway(self, giveaway_id: str) -> bool:
        """Annule un giveaway actif"""
        giveaway = self.active_giveaways.get(giveaway_id)
        if not giveaway:
            return False
            
        giveaway.status = GiveawayStatus.CANCELLED
        
        # Mettre à jour le message
        channel = self.bot.get_channel(giveaway.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(giveaway.message_id)
                embed = discord.Embed(
                    title="❌ GIVEWAY ANNULÉ",
                    description="Ce giveaway a été annulé par un administrateur.",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed)
                await message.clear_reactions()
            except:
                pass
                
        # Nettoyer
        del self.active_giveaways[giveaway_id]
        
        if self.db:
            await self._update_giveaway_status(giveaway_id, GiveawayStatus.CANCELLED)
            
        return True
        
    async def reroll_giveaway(self, giveaway_id: str, winners_count: int = 1) -> List[discord.Member]:
        """Retire au sort de nouveaux gagnants (pour remplacer des gagnants absents)"""
        # Récupérer depuis la DB
        if not self.db:
            return []
            
        result = await self.db.fetch(
            "SELECT * FROM ended_giveaways WHERE id = %s",
            (giveaway_id,)
        )
        
        if not result:
            return []
            
        row = result[0]
        entries_data = row['entries']
        
        # Reconstituer les entrées
        entries = [GiveawayEntry(**e) for e in entries_data]
        
        # Exclure les gagnants précédents
        previous_winners = set(row['winners'])
        available_entries = [e for e in entries if e.user_id not in previous_winners]
        
        if not available_entries:
            return []
            
        # Tirer au sort
        guild = self.bot.get_guild(row['guild_id'])
        if not guild:
            return []
            
        winners_count = min(winners_count, len(available_entries))
        new_winners_entries = random.sample(available_entries, winners_count)
        
        new_winners = []
        for entry in new_winners_entries:
            member = guild.get_member(entry.user_id)
            if member:
                new_winners.append(member)
                
        return new_winners
        
    # ============ MÉTHODES DB ============
    
    async def _save_completed_milestone(self, guild_id: int, milestone: int):
        """Sauvegarde un palier complété"""
        await self.db.execute(
            """
            INSERT INTO completed_milestones (guild_id, milestone, completed_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (guild_id, milestone) DO NOTHING
            """,
            (guild_id, milestone)
        )
        
    async def _save_giveaway(self, giveaway: ActiveGiveaway):
        """Sauvegarde un giveaway"""
        await self.db.execute(
            """
            INSERT INTO active_giveaways 
            (id, guild_id, milestone, reward, channel_id, message_id, host_id, 
             started_at, ends_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                entries = EXCLUDED.entries,
                status = EXCLUDED.status
            """,
            (
                giveaway.id,
                self.get_default_guild_id(),
                giveaway.milestone,
                json.dumps(giveaway.reward.to_dict()),
                giveaway.channel_id,
                giveaway.message_id,
                giveaway.host_id,
                giveaway.started_at,
                giveaway.ends_at,
                giveaway.status.value
            )
        )
        
    async def _save_entry(self, giveaway_id: str, entry: GiveawayEntry):
        """Sauvegarde une entrée"""
        await self.db.execute(
            """
            UPDATE active_giveaways 
            SET entries = entries || %s::jsonb
            WHERE id = %s
            """,
            (json.dumps([entry.to_dict()]), giveaway_id)
        )
        
    async def _remove_entry_db(self, giveaway_id: str, user_id: int):
        """Supprime une entrée de la DB"""
        await self.db.execute(
            """
            UPDATE active_giveaways 
            SET entries = (
                SELECT jsonb_agg(e)
                FROM jsonb_array_elements(entries) AS e
                WHERE (e->>'user_id')::bigint != %s
            )
            WHERE id = %s
            """,
            (user_id, giveaway_id)
        )
        
    async def _update_giveaway_status(
        self, 
        giveaway_id: str, 
        status: GiveawayStatus
    ):
        """Met à jour le statut d'un giveaway"""
        if status == GiveawayStatus.ENDED:
            # Déplacer vers ended_giveaways
            await self.db.execute(
                """
                INSERT INTO ended_giveaways 
                SELECT *, NOW() as ended_at FROM active_giveaways WHERE id = %s;
                DELETE FROM active_giveaways WHERE id = %s;
                """,
                (giveaway_id, giveaway_id)
            )
        else:
            await self.db.execute(
                "UPDATE active_giveaways SET status = %s WHERE id = %s",
                (status.value, giveaway_id)
            )
            
    async def _save_milestone_config(self, milestone: int, reward: MilestoneReward):
        """Sauvegarde la config d'un palier"""
        await self.db.execute(
            """
            INSERT INTO giveaway_milestones (milestone, reward_config, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (milestone) DO UPDATE SET
                reward_config = EXCLUDED.reward_config
            """,
            (milestone, json.dumps(reward.to_dict()))
        )
        
    async def _remove_milestone_config(self, milestone: int):
        """Supprime un palier personnalisé"""
        await self.db.execute(
            "DELETE FROM giveaway_milestones WHERE milestone = %s",
            (milestone,)
        )
        
    def _row_to_giveaway(self, row: dict) -> ActiveGiveaway:
        """Convertit une ligne DB en objet ActiveGiveaway"""
        reward_data = json.loads(row['reward'])
        entries_data = json.loads(row.get('entries', '[]'))
        
        return ActiveGiveaway(
            id=row['id'],
            milestone=row['milestone'],
            reward=MilestoneReward.from_dict(reward_data),
            channel_id=row['channel_id'],
            message_id=row['message_id'],
            host_id=row['host_id'],
            started_at=row['started_at'],
            ends_at=row['ends_at'],
            entries=[GiveawayEntry(**e) for e in entries_data],
            status=GiveawayStatus(row['status']),
            winners=row.get('winners', [])
        )
