"""
🔒 SERVER LOCK - Verrouillage complet du serveur Discord
Empêche TOUTE entrée même avec invitations ou liens d'affiliation
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional
import asyncio


class ServerLockManager:
    """
    🔒 Gestionnaire de verrouillage serveur
    Bloque complètement l'accès au serveur
    """
    
    def __init__(self, bot: commands.Bot, db=None):
        self.bot = bot
        self.db = db
        self.is_locked = False
        self.lock_reason = ""
        self.locked_by = None
        self.locked_at = None
        self.allowed_roles = []  # Rôles qui peuvent toujours rejoindre (admin)
        self.kick_on_lock = True  # Expulser les nouveaux qui essaient de rejoindre
        
    async def setup(self):
        """Initialise le gestionnaire"""
        # Charger l'état depuis la DB si disponible
        if self.db:
            try:
                result = await self.db.fetch(
                    "SELECT * FROM server_lock WHERE id = 1"
                )
                if result:
                    row = result[0]
                    self.is_locked = row.get('is_locked', False)
                    self.lock_reason = row.get('reason', '')
                    self.locked_by = row.get('locked_by')
                    self.locked_at = row.get('locked_at')
            except:
                pass
        print("✅ ServerLockManager initialisé")
        
    async def lock_server(self, guild: discord.Guild, reason: str = "Maintenance", 
                         locked_by: int = None, kick_existing: bool = False) -> bool:
        """
        🔒 Verrouille complètement le serveur
        
        Args:
            guild: Le serveur à verrouiller
            reason: Raison du verrouillage
            locked_by: ID de l'admin qui verrouille
            kick_existing: Expulser les membres existants (sauf staff)
        """
        try:
            self.is_locked = True
            self.lock_reason = reason
            self.locked_by = locked_by
            self.locked_at = datetime.utcnow().isoformat()
            
            # Sauvegarder en DB
            if self.db:
                await self.db.execute(
                    """
                    INSERT INTO server_lock (id, is_locked, reason, locked_by, locked_at)
                    VALUES (1, $1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE 
                    SET is_locked = $1, reason = $2, locked_by = $3, locked_at = $4
                    """,
                    True, reason, locked_by, self.locked_at
                )
            
            # Mettre à jour les paramètres du serveur
            await self._apply_lock_settings(guild)
            
            # Expulser les membres non-staff si demandé
            if kick_existing:
                await self._kick_non_staff(guild, reason)
            
            # Annonce dans le serveur
            await self._announce_lock(guild, reason)
            
            print(f"🔒 Serveur {guild.name} VERROUILLÉ par {locked_by}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur verrouillage serveur: {e}")
            return False
            
    async def unlock_server(self, guild: discord.Guild, unlocked_by: int = None) -> bool:
        """
        🔓 Déverrouille le serveur
        """
        try:
            self.is_locked = False
            self.lock_reason = ""
            
            # Sauvegarder en DB
            if self.db:
                await self.db.execute(
                    """
                    UPDATE server_lock 
                    SET is_locked = FALSE, unlocked_by = $1, unlocked_at = $2
                    WHERE id = 1
                    """,
                    unlocked_by, datetime.utcnow().isoformat()
                )
            
            # Restaurer les paramètres
            await self._restore_settings(guild)
            
            # Annonce
            await self._announce_unlock(guild)
            
            print(f"🔓 Serveur {guild.name} DÉVERROUILLÉ par {unlocked_by}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur déverrouillage serveur: {e}")
            return False
            
    async def _apply_lock_settings(self, guild: discord.Guild):
        """Applique les paramètres de verrouillage"""
        # 1. Révoquer toutes les invitations existantes
        invitations = await guild.invites()
        for invite in invitations:
            try:
                await invite.delete(reason=f"Serveur verrouillé: {self.lock_reason}")
            except:
                pass
        
        # 2. Désactiver la création d'invitations pour tous les rôles sauf admin
        for role in guild.roles:
            if role.name.lower() not in ['admin', 'administrator', 'owner', 'founder']:
                try:
                    await role.edit(permissions=discord.Permissions(
                        create_instant_invite=False
                    ))
                except:
                    pass
        
        # 3. Mettre à jour le widget serveur (désactiver)
        try:
            await guild.edit(widget_enabled=False)
        except:
            pass
            
        # 4. Désactiver le discovery si activé
        try:
            await guild.edit(discoverable=False)
        except:
            pass
            
    async def _restore_settings(self, guild: discord.Guild):
        """Restaure les paramètres normaux"""
        # Réactiver le widget
        try:
            await guild.edit(widget_enabled=True)
        except:
            pass
            
        # Réactiver le discovery
        try:
            await guild.edit(discoverable=True)
        except:
            pass
            
    async def _kick_non_staff(self, guild: discord.Guild, reason: str):
        """Expulse tous les membres non-staff"""
        staff_roles = ['admin', 'administrator', 'mod', 'moderator', 'owner', 'founder', 'staff']
        
        for member in guild.members:
            if member.bot:
                continue
                
            is_staff = any(
                role.name.lower() in staff_roles 
                for role in member.roles
            )
            
            if not is_staff and member != guild.owner:
                try:
                    await member.send(
                        f"🔒 Le serveur **{guild.name}** a été temporairement fermé.\n"
                        f"Raison: {reason}\n\n"
                        f"Vous pourrez rejoindre à nouveau quand le serveur rouvrira."
                    )
                except:
                    pass
                    
                try:
                    await member.kick(reason=f"Serveur verrouillé: {reason}")
                    await asyncio.sleep(0.5)  # Rate limit protection
                except:
                    pass
                    
    async def _announce_lock(self, guild: discord.Guild, reason: str):
        """Annonce le verrouillage dans le serveur"""
        # Chercher un channel d'annonces
        announce_channel = None
        for channel in guild.text_channels:
            if any(word in channel.name.lower() for word in ['announce', 'general', 'main']):
                announce_channel = channel
                break
                
        if announce_channel:
            embed = discord.Embed(
                title="🔒 SERVEUR TEMPORAIREMENT FERMÉ",
                description=f"**Raison:** {reason}\n\n"
                           f"Le serveur est maintenant verrouillé.\n"
                           f"• Aucune nouvelle personne ne peut rejoindre\n"
                           f"• Toutes les invitations sont révoquées\n"
                           f"• Les liens d'affiliation ne fonctionnent pas\n\n"
                           f"Le serveur rouvrira quand l'administrateur le décidera.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Verrouillé par {self.locked_by}")
            
            await announce_channel.send(embed=embed)
            
    async def _announce_unlock(self, guild: discord.Guild):
        """Annonce le déverrouillage"""
        announce_channel = None
        for channel in guild.text_channels:
            if any(word in channel.name.lower() for word in ['announce', 'general', 'main']):
                announce_channel = channel
                break
                
        if announce_channel:
            embed = discord.Embed(
                title="🔓 SERVEUR ROUVERT !",
                description="Le serveur est de nouveau ouvert !\n\n"
                           "Vous pouvez :\n"
                           "• Inviter de nouveaux membres\n"
                           "• Utiliser vos liens d'affiliation\n"
                           "• Rejoindre via les invitations\n\n"
                           "Bienvenue à tous ! 🎉",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            await announce_channel.send(embed=embed)
            
    async def handle_member_join(self, member: discord.Member):
        """
        Gère l'arrivée d'un nouveau membre
        Retourne True si le membre doit être accepté
        """
        # Si pas verrouillé, tout le monde peut entrer
        if not self.is_locked:
            return True
            
        # Vérifier si c'est un admin/staff
        staff_roles = ['admin', 'administrator', 'mod', 'moderator', 'owner', 'founder', 'staff']
        is_staff = any(
            role.name.lower() in staff_roles 
            for role in member.roles
        )
        
        # Le owner peut toujours entrer
        if member == member.guild.owner or is_staff:
            return True
            
        # Kick le membre
        try:
            await member.send(
                f"🔒 **{member.guild.name}** est temporairement fermé.\n\n"
                f"Raison: {self.lock_reason}\n\n"
                f"Le serveur rouvrira bientôt. Revenez plus tard !"
            )
        except:
            pass
            
        try:
            await member.kick(reason=f"Serveur verrouillé: {self.lock_reason}")
        except:
            pass
            
        return False
        
    async def handle_invite_create(self, invite: discord.Invite):
        """Bloque la création d'invitations quand verrouillé"""
        if not self.is_locked:
            return True
            
        # Supprimer l'invitation immédiatement
        try:
            await invite.delete(reason="Serveur verrouillé - invitations désactivées")
        except:
            pass
            
        return False


class ServerLockCommands(commands.Cog):
    """Commandes de verrouillage serveur - ADMIN UNIQUEMENT"""
    
    def __init__(self, bot):
        self.bot = bot
        self.lock_manager = None
        
    def setup_manager(self, manager: ServerLockManager):
        self.lock_manager = manager
        
    @commands.hybrid_command(name="server_lock")
    @commands.has_permissions(administrator=True)
    async def server_lock(self, ctx: commands.Context, *, reason: str = "Maintenance"):
        """
        🔒 Ferme complètement le serveur
        Empêche TOUTE entrée même avec invitations
        """
        if not self.lock_manager:
            await ctx.send("❌ Système de verrouillage non disponible", ephemeral=True)
            return
            
        confirm_embed = discord.Embed(
            title="⚠️ CONFIRMATION REQUISE",
            description=f"Vous allez **FERMER** le serveur.\n\n"
                       f"**Raison:** {reason}\n\n"
                       f"Conséquences:\n"
                       f"• ❌ Aucune entrée possible\n"
                       f"• ❌ Toutes les invitations révoquées\n"
                       f"• ❌ Liens d'affiliation inactifs\n"
                       f"• ❌ Widget serveur désactivé\n\n"
                       f"Seul un administrateur pourra rouvrir.",
            color=0xff0000
        )
        
        view = discord.ui.View()
        
        confirm_btn = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="CONFIRMER LA FERMETURE",
            emoji="🔒"
        )
        
        async def confirm_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ Non autorisé", ephemeral=True)
                return
                
            success = await self.lock_manager.lock_server(
                ctx.guild,
                reason=reason,
                locked_by=ctx.author.id
            )
            
            if success:
                await interaction.response.send_message(
                    f"🔒 **SERVEUR FERMÉ**\n\n"
                    f"Raison: {reason}\n"
                    f"Par: {ctx.author.mention}\n\n"
                    f"Aucune entrée possible jusqu'à réouverture.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Erreur lors du verrouillage",
                    ephemeral=True
                )
                
        confirm_btn.callback = confirm_callback
        view.add_item(confirm_btn)
        
        cancel_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Annuler"
        )
        cancel_btn.callback = lambda i: i.response.send_message("❌ Annulé", ephemeral=True)
        view.add_item(cancel_btn)
        
        await ctx.send(embed=confirm_embed, view=view, ephemeral=True)
        
    @commands.hybrid_command(name="server_unlock")
    @commands.has_permissions(administrator=True)
    async def server_unlock(self, ctx: commands.Context):
        """
        🔓 Rouvre le serveur
        """
        if not self.lock_manager:
            return
            
        if not self.lock_manager.is_locked:
            await ctx.send("ℹ️ Le serveur n'est pas verrouillé", ephemeral=True)
            return
            
        success = await self.lock_manager.unlock_server(
            ctx.guild,
            unlocked_by=ctx.author.id
        )
        
        if success:
            await ctx.send(
                f"🔓 **SERVEUR ROUVERT !**\n\n"
                f"Par: {ctx.author.mention}\n\n"
                f"Les invitations sont de nouveau actives.",
                ephemeral=False
            )
        else:
            await ctx.send("❌ Erreur lors du déverrouillage", ephemeral=True)
            
    @commands.hybrid_command(name="server_status")
    async def server_status(self, ctx: commands.Context):
        """
        📊 Voir le statut du serveur
        """
        if not self.lock_manager:
            return
            
        if self.lock_manager.is_locked:
            embed = discord.Embed(
                title="🔒 SERVEUR FERMÉ",
                description=f"**Raison:** {self.lock_manager.lock_reason}\n"
                           f"**Depuis:** <t:{int(datetime.fromisoformat(self.lock_manager.locked_at).timestamp())}:R>\n"
                           f"**Par:** <@{self.lock_manager.locked_by}>",
                color=0xff0000
            )
        else:
            embed = discord.Embed(
                title="🔓 SERVEUR OUVERT",
                description="Le serveur est ouvert et accessible.",
                color=0x00ff00
            )
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="server_kick_all")
    @commands.has_permissions(administrator=True)
    async def server_kick_all(self, ctx: commands.Context, *, reason: str = "Maintenance"):
        """
        👢 Expulse tous les membres non-staff et ferme
        """
        if not self.lock_manager:
            return
            
        confirm_embed = discord.Embed(
            title="⚠️ EXPULSION MASSIVE",
            description=f"Vous allez **EXPULSER TOUS LES MEMBRES** (sauf staff)\n\n"
                       f"**Raison:** {reason}\n\n"
                       f"⚠️ CETTE ACTION EST IRRÉVERSIBLE !\n\n"
                       f"Les membres devront être réinvités un par un.",
            color=0xff0000
        )
        
        view = discord.ui.View()
        
        confirm_btn = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="EXPULSER TOUS ET FERMER"
        )
        
        async def confirm_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return
                
            # D'abord verrouiller
            await self.lock_manager.lock_server(
                ctx.guild,
                reason=reason,
                locked_by=ctx.author.id,
                kick_existing=True
            )
            
            await interaction.response.send_message(
                "🔒👢 **SERVEUR VIDÉ ET FERMÉ**\n\n"
                "Tous les membres non-staff ont été expulsés.",
                ephemeral=True
            )
            
        confirm_btn.callback = confirm_callback
        view.add_item(confirm_btn)
        
        cancel_btn = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Annuler"
        )
        cancel_btn.callback = lambda i: i.response.send_message("❌ Annulé", ephemeral=True)
        view.add_item(cancel_btn)
        
        await ctx.send(embed=confirm_embed, view=view, ephemeral=True)


class ServerLockEvents(commands.Cog):
    """Événements pour le verrouillage serveur"""
    
    def __init__(self, bot, lock_manager: ServerLockManager):
        self.bot = bot
        self.lock_manager = lock_manager
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Intercepte les nouveaux membres"""
        await self.lock_manager.handle_member_join(member)
        
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Intercepte la création d'invitations"""
        await self.lock_manager.handle_invite_create(invite)
