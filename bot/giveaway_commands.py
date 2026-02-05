"""
🎁 Commandes Discord pour le système de giveaways automatiques
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio

from auto_giveaway import AutoGiveawayManager, MilestoneReward


class GiveawayCommands(commands.Cog):
    """
    Commandes pour gérer les giveaways automatiques aux paliers
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.giveaway_manager: Optional[AutoGiveawayManager] = None
        
    async def cog_load(self):
        """Initialise le gestionnaire de giveaways"""
        # Le gestionnaire sera initialisé dans bot_secure.py
        pass
        
    def setup_manager(self, manager: AutoGiveawayManager):
        """Configure le gestionnaire de giveaways"""
        self.giveaway_manager = manager
        
    # ============ COMMANDES UTILISATEUR ============
    
    @commands.hybrid_command(name="giveaway", aliases=["gw"])
    async def giveaway_info(self, ctx: commands.Context):
        """
        📊 Affiche les informations sur les giveaways automatiques
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        guild = ctx.guild
        member_count = guild.member_count
        
        # Embed principal
        embed = discord.Embed(
            title="🎁 Système de Giveaways Automatiques",
            description=(
                f"Des giveaways sont automatiquement déclenchés à chaque palier de membres !\n\n"
                f"👥 **Membres actuels:** {member_count}\n"
            ),
            color=discord.Color.gold()
        )
        
        # Prochains paliers
        upcoming = []
        for milestone in sorted(self.giveaway_manager.milestones.keys()):
            if milestone > member_count:
                remaining = milestone - member_count
                reward = self.giveaway_manager.milestones[milestone]
                upcoming.append(
                    f"**{milestone}** membres (+{remaining}) - {reward.description[:50]}..."
                )
                if len(upcoming) >= 3:
                    break
                    
        if upcoming:
            embed.add_field(
                name="🎯 Prochains paliers",
                value="\n".join(upcoming),
                inline=False
            )
        else:
            embed.add_field(
                name="🎉 Félicitations !",
                value="Tous les paliers ont été atteints !",
                inline=False
            )
            
        # Giveaways actifs
        active_giveaways = [
            g for g in self.giveaway_manager.active_giveaways.values()
            if g.channel_id == ctx.channel.id or self._is_guild_wide(g, guild)
        ]
        
        if active_giveaways:
            active_text = "\n".join([
                f"🎉 **{g.milestone} membres** - {g.entry_count} participants - "
                f"<t:{int(g.ends_at.timestamp())}:R>"
                for g in active_giveaways[:3]
            ])
            embed.add_field(
                name="🔥 Giveaways en cours",
                value=active_text,
                inline=False
            )
            
        # Historique récent
        embed.add_field(
            name="📜 Comment participer ?",
            value=(
                "Quand un palier est atteint, un giveaway se lance automatiquement !\n"
                "Réagis avec 🎉 sur le message du giveaway pour participer."
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="giveaway_stats")
    async def giveaway_stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """
        📊 Affiche les statistiques de giveaways
        """
        target = member or ctx.author
        
        # Récupérer les stats depuis la DB
        # Pour l'instant, affichage simple
        embed = discord.Embed(
            title=f"🎁 Statistiques de {target.display_name}",
            color=discord.Color.blue()
        )
        
        # TODO: Récupérer les vraies stats depuis la DB
        embed.description = "Statistiques détaillées bientôt disponibles !"
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"])
    async def economy_leaderboard(self, ctx: commands.Context):
        """
        🏆 Affiche le classement des plus riches
        """
        embed = discord.Embed(
            title="💰 Classement des plus riches",
            description="Top 10 des utilisateurs avec le plus de coins",
            color=discord.Color.gold()
        )
        
        # TODO: Récupérer depuis la DB
        embed.add_field(
            name="🥇 Top 10",
            value="Bientôt disponible...",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="balance", aliases=["bal", "coins"])
    async def check_balance(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """
        💰 Voir son solde de coins
        """
        target = member or ctx.author
        
        # TODO: Récupérer le vrai solde depuis la DB
        embed = discord.Embed(
            title=f"💳 Portefeuille de {target.display_name}",
            description="**0** coins 🪙",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)
        
    # ============ COMMANDES ADMIN ============
    
    @commands.hybrid_command(name="giveaway_force")
    @commands.has_permissions(administrator=True)
    async def force_giveaway(
        self, 
        ctx: commands.Context, 
        milestone: int,
        channel: Optional[discord.TextChannel] = None
    ):
        """
        🚀 Force le démarrage d'un giveaway (Admin uniquement)
        
        Args:
            milestone: Le palier à célébrer (ex: 50, 100)
            channel: Canal où poster (par défaut: canal actuel)
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        target_channel = channel or ctx.channel
        
        # Vérifier si le palier existe
        if milestone not in self.giveaway_manager.milestones:
            available = ", ".join([str(m) for m in self.giveaway_manager.milestones.keys()])
            await ctx.send(f"❌ Palier invalide. Disponibles: {available}")
            return
            
        # Démarrer le giveaway
        try:
            giveaway = await self.giveaway_manager.force_giveaway(
                guild=ctx.guild,
                channel=target_channel,
                milestone=milestone,
                host=ctx.author
            )
            
            await ctx.send(
                f"✅ Giveaway pour le palier **{milestone}** lancé dans {target_channel.mention} !\n"
                f"ID: `{giveaway.id}`"
            )
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {e}")
            
    @commands.hybrid_command(name="giveaway_cancel")
    @commands.has_permissions(administrator=True)
    async def cancel_giveaway(self, ctx: commands.Context, giveaway_id: str):
        """
        ❌ Annule un giveaway actif (Admin uniquement)
        
        Args:
            giveaway_id: L'ID du giveaway à annuler
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        success = await self.giveaway_manager.cancel_giveaway(giveaway_id)
        
        if success:
            await ctx.send(f"✅ Giveaway `{giveaway_id}` annulé.")
        else:
            await ctx.send(f"❌ Giveaway `{giveaway_id}` introuvable ou déjà terminé.")
            
    @commands.hybrid_command(name="giveaway_reroll")
    @commands.has_permissions(administrator=True)
    async def reroll_giveaway(
        self, 
        ctx: commands.Context, 
        giveaway_id: str,
        winners: int = 1
    ):
        """
        🎲 Retire au sort de nouveaux gagnants (Admin uniquement)
        
        Args:
            giveaway_id: L'ID du giveaway
            winners: Nombre de nouveaux gagnants (défaut: 1)
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        new_winners = await self.giveaway_manager.reroll_giveaway(giveaway_id, winners)
        
        if not new_winners:
            await ctx.send("❌ Impossible de retirer au sort (giveaway introuvable ou plus de participants).")
            return
            
        mentions = ", ".join([w.mention for w in new_winners])
        
        embed = discord.Embed(
            title="🎲 Nouveaux gagnants !",
            description=f"Félicitations à {mentions} !",
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="giveaway_add_milestone")
    @commands.has_permissions(administrator=True)
    async def add_milestone(
        self,
        ctx: commands.Context,
        member_count: int,
        winners: int,
        duration_hours: int,
        currency: int = 0,
        *,
        description: str
    ):
        """
        ➕ Ajoute un palier personnalisé (Admin uniquement)
        
        Args:
            member_count: Nombre de membres pour déclencher
            winners: Nombre de gagnants
            duration_hours: Durée du giveaway en heures
            currency: Récompense en coins (optionnel)
            description: Description du giveaway
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        reward = MilestoneReward(
            member_count=member_count,
            currency_reward=currency,
            giveaway_duration_hours=duration_hours,
            winners_count=winners,
            description=description
        )
        
        success = await self.giveaway_manager.add_custom_milestone(member_count, reward)
        
        if success:
            await ctx.send(f"✅ Palier **{member_count}** membres ajouté avec succès !")
        else:
            await ctx.send(f"❌ Le palier **{member_count}** existe déjà.")
            
    @commands.hybrid_command(name="giveaway_remove_milestone")
    @commands.has_permissions(administrator=True)
    async def remove_milestone(self, ctx: commands.Context, member_count: int):
        """
        ➖ Supprime un palier personnalisé (Admin uniquement)
        
        Args:
            member_count: Le palier à supprimer
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        success = await self.giveaway_manager.remove_milestone(member_count)
        
        if success:
            await ctx.send(f"✅ Palier **{member_count}** supprimé.")
        else:
            await ctx.send(f"❌ Impossible de supprimer le palier **{member_count}** (existe pas ou palier par défaut).")
            
    @commands.hybrid_command(name="giveaway_list")
    @commands.has_permissions(administrator=True)
    async def list_milestones(self, ctx: commands.Context):
        """
        📋 Liste tous les paliers configurés (Admin uniquement)
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        embed = discord.Embed(
            title="📋 Paliers de Giveaways Configurés",
            color=discord.Color.blue()
        )
        
        milestones_text = []
        for count in sorted(self.giveaway_manager.milestones.keys()):
            reward = self.giveaway_manager.milestones[count]
            rewards_list = []
            if reward.currency_reward > 0:
                rewards_list.append(f"{reward.currency_reward}🪙")
            if reward.nitro_reward:
                rewards_list.append("Nitro")
            if reward.role_reward:
                rewards_list.append("Rôle")
            if reward.custom_reward:
                rewards_list.append("Custom")
                
            rewards_str = " + ".join(rewards_list) if rewards_list else "Aucune"
            
            is_default = "🔄" if count in self.giveaway_manager.DEFAULT_MILESTONES else "✏️"
            
            milestones_text.append(
                f"{is_default} **{count}** membres - {rewards_str} - {reward.winners_count} gagnant(s)"
            )
            
        embed.description = "\n".join(milestones_text) if milestones_text else "Aucun palier configuré."
        
        embed.set_footer(text="🔄 = Défaut | ✏️ = Personnalisé")
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="giveaway_end")
    @commands.has_permissions(administrator=True)
    async def end_giveaway_early(self, ctx: commands.Context, giveaway_id: str):
        """
        🏁 Termine un giveaway avant la fin (Admin uniquement)
        
        Args:
            giveaway_id: L'ID du giveaway à terminer
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        giveaway = await self.giveaway_manager.end_giveaway(giveaway_id, manual=True)
        
        if giveaway:
            await ctx.send(f"✅ Giveaway `{giveaway_id}` terminé avec {len(giveaway.winners)} gagnant(s) !")
        else:
            await ctx.send(f"❌ Giveaway `{giveaway_id}` introuvable ou déjà terminé.")
            
    @commands.hybrid_command(name="giveaway_config")
    @commands.has_permissions(administrator=True)
    async def configure_giveaway(
        self,
        ctx: commands.Context,
        announcement_channel: Optional[discord.TextChannel] = None
    ):
        """
        ⚙️ Configure le système de giveaways (Admin uniquement)
        
        Args:
            announcement_channel: Canal pour les annonces automatiques
        """
        if not self.giveaway_manager:
            await ctx.send("❌ Système de giveaways non disponible.")
            return
            
        if announcement_channel:
            self.giveaway_manager.announcement_channel_id = announcement_channel.id
            await ctx.send(f"✅ Canal d'annonces configuré: {announcement_channel.mention}")
        else:
            await ctx.send(
                "**Configuration actuelle:**\n"
                f"Canal d'annonces: {'<#' + str(self.giveaway_manager.announcement_channel_id) + '>' if self.giveaway_manager.announcement_channel_id else 'Non configuré (auto-détection)'}\n"
                f"Paliers actifs: {len(self.giveaway_manager.milestones)}"
            )
            
    # ============ EVENT LISTENERS ============
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gère les participations aux giveaways"""
        if not self.giveaway_manager:
            return
            
        # Ignorer les réactions du bot
        if payload.user_id == self.bot.user.id:
            return
            
        # Vérifier si c'est une réaction 🎉
        if str(payload.emoji) != "🎉":
            return
            
        # Chercher le giveaway correspondant
        for giveaway_id, giveaway in self.giveaway_manager.active_giveaways.items():
            if giveaway.message_id == payload.message_id and giveaway.channel_id == payload.channel_id:
                # Ajouter la participation
                success = await self.giveaway_manager.add_entry(
                    giveaway_id=giveaway_id,
                    user_id=payload.user_id,
                    message_id=payload.message_id
                )
                
                if success:
                    # Optionnel: Envoyer un DM de confirmation
                    try:
                        user = self.bot.get_user(payload.user_id)
                        if user:
                            embed = discord.Embed(
                                title="🎉 Participation enregistrée !",
                                description=(
                                    f"Tu participes au giveaway du palier **{giveaway.milestone} membres** !\n\n"
                                    f"🎯 Récompenses: {self._format_reward(giveaway.reward)}\n"
                                    f"⏰ Fin: <t:{int(giveaway.ends_at.timestamp())}:R>\n\n"
                                    f"Bonne chance ! 🍀"
                                ),
                                color=discord.Color.green()
                            )
                            await user.send(embed=embed)
                    except:
                        pass  # DM fermés
                        
                break
                
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Gère le retrait des participations"""
        if not self.giveaway_manager:
            return
            
        if str(payload.emoji) != "🎉":
            return
            
        for giveaway_id, giveaway in self.giveaway_manager.active_giveaways.items():
            if giveaway.message_id == payload.message_id:
                await self.giveaway_manager.remove_entry(giveaway_id, payload.user_id)
                break
                
    # ============ HELPERS ============
    
    def _is_guild_wide(self, giveaway, guild: discord.Guild) -> bool:
        """Vérifie si un giveaway est visible pour tout le serveur"""
        return guild.get_channel(giveaway.channel_id) is not None
        
    def _format_reward(self, reward: MilestoneReward) -> str:
        """Formate une récompense pour l'affichage"""
        parts = []
        if reward.currency_reward > 0:
            parts.append(f"{reward.currency_reward}🪙")
        if reward.nitro_reward:
            parts.append("Nitro")
        if reward.role_reward:
            parts.append("Rôle")
        if reward.custom_reward:
            parts.append(reward.custom_reward)
        return " + ".join(parts) if parts else "Mystère 🤫"


class GiveawayErrorHandler(commands.Cog):
    """Gestionnaire d'erreurs pour les commandes de giveaways"""
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        """Gère les erreurs des commandes giveaways"""
        if ctx.command and not ctx.command.name.startswith('giveaway'):
            return
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Argument manquant: `{error.param.name}`. Utilise `!help {ctx.command.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argument invalide. Vérifie ton entrée.")
        else:
            # Erreur non gérée
            pass


async def setup(bot: commands.Bot):
    """Setup du cog"""
    await bot.add_cog(GiveawayCommands(bot))
    await bot.add_cog(GiveawayErrorHandler(bot))
