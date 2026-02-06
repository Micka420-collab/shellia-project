"""
🔘 BUTTON MANAGER - Système de boutons Discord stylés
Génère et place des boutons sur les channels Discord
Contrôlable depuis Discord ET le site admin
"""

import discord
from discord.ext import commands
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from datetime import datetime


class ButtonStyle(Enum):
    """Styles de boutons disponibles"""
    PRIMARY = "primary"      # 🟢 Vert - Action principale
    SECONDARY = "secondary"  # 🔵 Gris - Action secondaire
    SUCCESS = "success"      # 🟢 Vert clair - Succès/Confirmation
    DANGER = "danger"        # 🔴 Rouge - Danger/Annuler
    PREMIUM = "premium"      # 🟣 Or/Violet - Premium/Spécial
    BLURPLE = "blurple"      # 💜 Violet Discord - Branding


class ButtonType(Enum):
    """Types de boutons avec actions prédéfinies"""
    TICKET_CREATE = "ticket_create"
    SHOP_ACCESS = "shop_access"
    PLAN_UPGRADE = "plan_upgrade"
    SUPPORT_FAQ = "support_faq"
    GIVEAWAY_JOIN = "giveaway_join"
    FEEDBACK = "feedback"
    REPORT = "report"
    CUSTOM_LINK = "custom_link"
    CUSTOM_ACTION = "custom_action"


@dataclass
class ButtonConfig:
    """Configuration d'un bouton"""
    id: str
    type: ButtonType
    style: ButtonStyle
    label: str
    emoji: str
    channel_id: int
    message_id: Optional[int] = None
    custom_data: Dict[str, Any] = None
    created_by: int = 0
    created_at: str = ""
    position: str = "bottom"  # top, bottom, inline
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'style': self.style.value,
            'label': self.label,
            'emoji': self.emoji,
            'channel_id': self.channel_id,
            'message_id': self.message_id,
            'custom_data': self.custom_data,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'position': self.position
        }


class StyledButton(discord.ui.Button):
    """Bouton stylé avec style personnalisé"""
    
    STYLE_MAP = {
        ButtonStyle.PRIMARY: discord.ButtonStyle.primary,
        ButtonStyle.SECONDARY: discord.ButtonStyle.secondary,
        ButtonStyle.SUCCESS: discord.ButtonStyle.success,
        ButtonStyle.DANGER: discord.ButtonStyle.danger,
        ButtonStyle.PREMIUM: discord.ButtonStyle.primary,  # Fallback
        ButtonStyle.BLURPLE: discord.ButtonStyle.primary
    }
    
    def __init__(self, config: ButtonConfig, callback_func):
        style = self.STYLE_MAP.get(config.style, discord.ButtonStyle.primary)
        
        super().__init__(
            style=style,
            label=config.label,
            emoji=config.emoji,
            custom_id=f"btn_{config.id}"
        )
        
        self.config = config
        self.callback_func = callback_func
        
        # Personnalisation visuelle supplémentaire
        if config.style == ButtonStyle.PREMIUM:
            # Pour les boutons premium, on peut ajouter une couleur dorée
            # Note: Discord limite les styles, mais on peut simuler avec l'emoji
            if not config.emoji:
                self.emoji = "⭐"
        
    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.config)


class ButtonManager:
    """
    🔘 Gestionnaire de boutons Discord stylés
    """
    
    # Templates prédéfinis
    TEMPLATES = {
        ButtonType.TICKET_CREATE: {
            'label': 'Créer un ticket',
            'emoji': '🎫',
            'style': ButtonStyle.PRIMARY,
            'description': 'Ouvre un ticket de support'
        },
        ButtonType.SHOP_ACCESS: {
            'label': 'Boutique',
            'emoji': '🛍️',
            'style': ButtonStyle.SUCCESS,
            'description': 'Accès rapide à la boutique'
        },
        ButtonType.PLAN_UPGRADE: {
            'label': 'Upgrade mon compte',
            'emoji': '⭐',
            'style': ButtonStyle.PREMIUM,
            'description': 'Passez au plan supérieur'
        },
        ButtonType.SUPPORT_FAQ: {
            'label': 'FAQ & Aide',
            'emoji': '❓',
            'style': ButtonStyle.SECONDARY,
            'description': 'Questions fréquentes'
        },
        ButtonType.GIVEAWAY_JOIN: {
            'label': 'Participer au giveaway',
            'emoji': '🎁',
            'style': ButtonStyle.PREMIUM,
            'description': 'Rejoindre le giveaway en cours'
        },
        ButtonType.FEEDBACK: {
            'label': 'Donner mon avis',
            'emoji': '💬',
            'style': ButtonStyle.SECONDARY,
            'description': 'Feedback sur le service'
        },
        ButtonType.REPORT: {
            'label': 'Signaler',
            'emoji': '🚨',
            'style': ButtonStyle.DANGER,
            'description': 'Signaler un problème urgent'
        }
    }
    
    def __init__(self, bot: commands.Bot, db=None):
        self.bot = bot
        self.db = db
        self.active_buttons: Dict[str, ButtonConfig] = {}
        self.views: Dict[int, discord.ui.View] = {}  # channel_id -> view
        
    async def setup(self):
        """Initialise le gestionnaire de boutons"""
        # Charger les boutons actifs depuis la DB
        if self.db:
            await self._load_buttons_from_db()
        print("✅ ButtonManager initialisé")
        
    async def _load_buttons_from_db(self):
        """Charge les boutons persistants"""
        try:
            result = await self.db.fetch(
                "SELECT * FROM discord_buttons WHERE active = TRUE"
            )
            for row in result:
                config = ButtonConfig(
                    id=row['id'],
                    type=ButtonType(row['type']),
                    style=ButtonStyle(row['style']),
                    label=row['label'],
                    emoji=row['emoji'],
                    channel_id=row['channel_id'],
                    message_id=row['message_id'],
                    custom_data=row.get('custom_data', {}),
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    position=row.get('position', 'bottom')
                )
                self.active_buttons[config.id] = config
        except Exception as e:
            print(f"⚠️ Erreur chargement boutons: {e}")
            
    async def create_button(
        self,
        button_type: ButtonType,
        channel_id: int,
        style: Optional[ButtonStyle] = None,
        label: Optional[str] = None,
        emoji: Optional[str] = None,
        custom_data: Optional[Dict] = None,
        created_by: int = 0
    ) -> ButtonConfig:
        """
        Crée un nouveau bouton
        """
        # Utiliser le template si disponible
        template = self.TEMPLATES.get(button_type, {})
        
        config = ButtonConfig(
            id=str(uuid.uuid4())[:8],
            type=button_type,
            style=style or template.get('style', ButtonStyle.PRIMARY),
            label=label or template.get('label', 'Bouton'),
            emoji=emoji or template.get('emoji', '🔘'),
            channel_id=channel_id,
            custom_data=custom_data or {},
            created_by=created_by,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Sauvegarder en DB
        if self.db:
            await self.db.execute(
                """
                INSERT INTO discord_buttons 
                (id, type, style, label, emoji, channel_id, custom_data, created_by, created_at, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                (config.id, config.type.value, config.style.value, config.label,
                 config.emoji, config.channel_id, json.dumps(config.custom_data),
                 config.created_by, config.created_at)
            )
            
        self.active_buttons[config.id] = config
        return config
        
    async def place_button(
        self,
        button_id: str,
        message_content: Optional[str] = None,
        position: str = "bottom"
    ) -> bool:
        """
        Place un bouton sur un channel Discord
        """
        config = self.active_buttons.get(button_id)
        if not config:
            return False
            
        channel = self.bot.get_channel(config.channel_id)
        if not channel:
            print(f"❌ Channel {config.channel_id} introuvable")
            return False
            
        # Créer la vue avec le bouton
        view = discord.ui.View(timeout=None)
        button = StyledButton(config, self._handle_button_click)
        view.add_item(button)
        
        # Message par défaut selon le type
        if not message_content:
            message_content = self._get_default_message(config.type)
            
        try:
            # Envoyer ou éditer le message
            if config.message_id:
                # Mettre à jour un message existant
                message = await channel.fetch_message(config.message_id)
                await message.edit(content=message_content, view=view)
            else:
                # Nouveau message
                message = await channel.send(content=message_content, view=view)
                config.message_id = message.id
                
                # Mettre à jour la DB
                if self.db:
                    await self.db.execute(
                        "UPDATE discord_buttons SET message_id = %s WHERE id = %s",
                        (message.id, button_id)
                    )
                    
            print(f"✅ Bouton {button_id} placé sur {channel.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur placement bouton: {e}")
            return False
            
    async def place_multiple_buttons(
        self,
        channel_id: int,
        button_configs: List[Dict],
        layout: str = "horizontal",  # horizontal, vertical, grid
        message_content: str = ""
    ) -> str:
        """
        Place plusieurs boutons ensemble (toolbar)
        """
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return ""
            
        view = discord.ui.View(timeout=None)
        created_buttons = []
        
        for btn_conf in button_configs:
            config = await self.create_button(
                button_type=ButtonType(btn_conf['type']),
                channel_id=channel_id,
                style=ButtonStyle(btn_conf.get('style', 'primary')),
                label=btn_conf.get('label'),
                emoji=btn_conf.get('emoji'),
                custom_data=btn_conf.get('custom_data', {})
            )
            
            button = StyledButton(config, self._handle_button_click)
            view.add_item(button)
            created_buttons.append(config.id)
            
        try:
            message = await channel.send(
                content=message_content or "**Actions disponibles:**",
                view=view
            )
            
            # Mettre à jour les message_ids
            for btn_id in created_buttons:
                if self.db:
                    await self.db.execute(
                        "UPDATE discord_buttons SET message_id = %s WHERE id = %s",
                        (message.id, btn_id)
                    )
                    
            return message.id
            
        except Exception as e:
            print(f"❌ Erreur placement toolbar: {e}")
            return ""
            
    async def remove_button(self, button_id: str) -> bool:
        """
        Supprime un bouton
        """
        config = self.active_buttons.get(button_id)
        if not config:
            return False
            
        try:
            # Supprimer le message Discord si existe
            if config.message_id:
                channel = self.bot.get_channel(config.channel_id)
                if channel:
                    message = await channel.fetch_message(config.message_id)
                    await message.delete()
                    
            # Marquer comme inactif en DB
            if self.db:
                await self.db.execute(
                    "UPDATE discord_buttons SET active = FALSE WHERE id = %s",
                    (button_id,)
                )
                
            del self.active_buttons[button_id]
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression bouton: {e}")
            return False
            
    async def update_button(
        self,
        button_id: str,
        label: Optional[str] = None,
        emoji: Optional[str] = None,
        style: Optional[ButtonStyle] = None
    ) -> bool:
        """
        Met à jour un bouton existant
        """
        config = self.active_buttons.get(button_id)
        if not config:
            return False
            
        if label:
            config.label = label
        if emoji:
            config.emoji = emoji
        if style:
            config.style = style
            
        # Mettre à jour la DB
        if self.db:
            await self.db.execute(
                """
                UPDATE discord_buttons 
                SET label = %s, emoji = %s, style = %s 
                WHERE id = %s
                """,
                (config.label, config.emoji, config.style.value, button_id)
            )
            
        # Re-placer le bouton pour appliquer les changements
        await self.place_button(button_id)
        return True
        
    async def _handle_button_click(self, interaction: discord.Interaction, config: ButtonConfig):
        """
        Gère les clics sur les boutons
        """
        user_id = interaction.user.id
        
        # Log l'interaction
        await self._log_button_click(config.id, user_id)
        
        # Traiter selon le type
        if config.type == ButtonType.TICKET_CREATE:
            await self._handle_ticket_button(interaction, config)
        elif config.type == ButtonType.SHOP_ACCESS:
            await self._handle_shop_button(interaction, config)
        elif config.type == ButtonType.PLAN_UPGRADE:
            await self._handle_upgrade_button(interaction, config)
        elif config.type == ButtonType.SUPPORT_FAQ:
            await self._handle_faq_button(interaction, config)
        elif config.type == ButtonType.GIVEAWAY_JOIN:
            await self._handle_giveaway_button(interaction, config)
        elif config.type == ButtonType.CUSTOM_ACTION:
            await self._handle_custom_action(interaction, config)
        else:
            await interaction.response.send_message(
                f"🔄 Action en cours: {config.label}",
                ephemeral=True
            )
            
    async def _handle_ticket_button(self, interaction: discord.Interaction, config: ButtonConfig):
        """Gère le bouton création de ticket"""
        # Ouvrir un modal pour créer le ticket
        modal = TicketCreateModal()
        await interaction.response.send_modal(modal)
        
    async def _handle_shop_button(self, interaction: discord.Interaction, config: ButtonConfig):
        """Gère le bouton boutique"""
        await interaction.response.send_message(
            "🛍️ **Bienvenue dans la boutique !**\n\n"
            "Consultez nos produits avec `/shop`",
            ephemeral=True
        )
        
    async def _handle_upgrade_button(self, interaction: discord.Interaction, config: ButtonConfig):
        """Gère le bouton upgrade"""
        await interaction.response.send_message(
            "⭐ **Passez au niveau supérieur !**\n\n"
            "Découvrez nos plans avec `/plans`",
            ephemeral=True
        )
        
    async def _handle_faq_button(self, interaction: discord.Interaction, config: ButtonConfig):
        """Gère le bouton FAQ"""
        faq_embed = discord.Embed(
            title="❓ FAQ - Questions Fréquentes",
            description="Voici les réponses aux questions les plus courantes:",
            color=discord.Color.blue()
        )
        
        faq_embed.add_field(
            name="Comment créer un ticket ?",
            value="Utilisez le bouton 🎫 ou la commande `!ticket_create`",
            inline=False
        )
        
        faq_embed.add_field(
            name="Comment upgrader mon compte ?",
            value="Utilisez `/plans` pour voir les options disponibles",
            inline=False
        )
        
        await interaction.response.send_message(embed=faq_embed, ephemeral=True)
        
    async def _handle_giveaway_button(self, interaction: discord.Interaction, config: ButtonConfig):
        """Gère le bouton giveaway"""
        await interaction.response.send_message(
            "🎁 **Giveaway en cours !**\n\n"
            "Utilisez `/giveaway` pour voir les giveaways actifs",
            ephemeral=True
        )
        
    async def _handle_custom_action(self, interaction: discord.Interaction, config: ButtonConfig):
        """Gère les actions personnalisées"""
        custom_action = config.custom_data.get('action', 'default')
        await interaction.response.send_message(
            f"🔘 Action personnalisée: {custom_action}",
            ephemeral=True
        )
        
    async def _log_button_click(self, button_id: str, user_id: int):
        """Log les interactions avec les boutons"""
        if self.db:
            await self.db.execute(
                """
                INSERT INTO button_analytics (button_id, user_id, clicked_at)
                VALUES (%s, %s, %s)
                """,
                (button_id, user_id, datetime.utcnow().isoformat())
            )
            
    def _get_default_message(self, button_type: ButtonType) -> str:
        """Retourne le message par défaut selon le type"""
        messages = {
            ButtonType.TICKET_CREATE: "🎫 **Besoin d'aide ?**\nCliquez ci-dessous pour créer un ticket",
            ButtonType.SHOP_ACCESS: "🛍️ **Notre Boutique**\nDécouvrez nos produits",
            ButtonType.PLAN_UPGRADE: "⭐ **Améliorez votre expérience**\nPassez à un plan supérieur",
            ButtonType.SUPPORT_FAQ: "❓ **Questions ?**\nConsultez notre FAQ",
            ButtonType.GIVEAWAY_JOIN: "🎁 **Giveaway en cours !**\nParticipez maintenant",
            ButtonType.FEEDBACK: "💬 **Votre avis compte**\nDonnez-nous votre feedback",
            ButtonType.REPORT: "🚨 **Signalement**\nSignalez un problème urgent"
        }
        return messages.get(button_type, "🔘 **Action disponible**")
        
    def get_all_templates(self) -> Dict:
        """Retourne tous les templates disponibles"""
        return {
            btn_type.value: {
                'label': template['label'],
                'emoji': template['emoji'],
                'style': template['style'].value,
                'description': template['description']
            }
            for btn_type, template in self.TEMPLATES.items()
        }
        
    async def get_button_stats(self, button_id: Optional[str] = None) -> Dict:
        """Récupère les statistiques d'utilisation des boutons"""
        if not self.db:
            return {}
            
        if button_id:
            # Stats pour un bouton spécifique
            result = await self.db.fetch(
                """
                SELECT 
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT user_id) as unique_users,
                    MAX(clicked_at) as last_click
                FROM button_analytics 
                WHERE button_id = %s
                """,
                (button_id,)
            )
        else:
            # Stats globales
            result = await self.db.fetch(
                """
                SELECT 
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT button_id) as active_buttons
                FROM button_analytics 
                WHERE clicked_at > NOW() - INTERVAL '30 days'
                """
            )
            
        return dict(result[0]) if result else {}


class TicketCreateModal(discord.ui.Modal, title="Créer un ticket"):
    """Modal pour créer un ticket via bouton"""
    
    subject = discord.ui.TextInput(
        label="Sujet",
        placeholder="Décrivez brièvement votre problème",
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label="Description détaillée",
        style=discord.TextStyle.paragraph,
        placeholder="Expliquez votre problème en détail...",
        max_length=1000
    )
    
    category = discord.ui.TextInput(
        label="Catégorie",
        placeholder="general, billing, technical, bug...",
        default="general",
        max_length=20
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Ticket créé !\nSujet: {self.subject}\nDescription: {self.description[:100]}...",
            ephemeral=True
        )


class ButtonCommands(commands.Cog):
    """Commandes Discord pour gérer les boutons"""
    
    def __init__(self, bot):
        self.bot = bot
        self.button_manager = None
        
    def setup_manager(self, manager: ButtonManager):
        self.button_manager = manager
        
    @commands.hybrid_command(name="button_create")
    @commands.has_permissions(administrator=True)
    async def button_create(
        self,
        ctx: commands.Context,
        type: str,
        channel: discord.TextChannel,
        style: str = "primary",
        label: Optional[str] = None,
        emoji: Optional[str] = None
    ):
        """
        🔘 Crée et place un bouton stylé
        
        Types: ticket_create, shop_access, plan_upgrade, support_faq, giveaway_join, feedback, report
        Styles: primary, secondary, success, danger, premium, blurple
        """
        if not self.button_manager:
            await ctx.send("❌ ButtonManager non disponible", ephemeral=True)
            return
            
        try:
            btn_type = ButtonType(type)
            btn_style = ButtonStyle(style)
        except ValueError:
            await ctx.send("❌ Type ou style invalide", ephemeral=True)
            return
            
        config = await self.button_manager.create_button(
            button_type=btn_type,
            channel_id=channel.id,
            style=btn_style,
            label=label,
            emoji=emoji,
            created_by=ctx.author.id
        )
        
        success = await self.button_manager.place_button(config.id)
        
        if success:
            await ctx.send(
                f"✅ Bouton créé et placé !\n"
                f"ID: `{config.id}`\n"
                f"Channel: {channel.mention}",
                ephemeral=True
            )
        else:
            await ctx.send("❌ Erreur lors du placement", ephemeral=True)
            
    @commands.hybrid_command(name="button_remove")
    @commands.has_permissions(administrator=True)
    async def button_remove(self, ctx: commands.Context, button_id: str):
        """Supprime un bouton"""
        if not self.button_manager:
            return
            
        success = await self.button_manager.remove_button(button_id)
        
        if success:
            await ctx.send(f"✅ Bouton `{button_id}` supprimé", ephemeral=True)
        else:
            await ctx.send("❌ Bouton introuvable", ephemeral=True)
            
    @commands.hybrid_command(name="button_list")
    @commands.has_permissions(administrator=True)
    async def button_list(self, ctx: commands.Context):
        """Liste tous les boutons actifs"""
        if not self.button_manager:
            return
            
        buttons = self.button_manager.active_buttons
        
        if not buttons:
            await ctx.send("Aucun bouton actif", ephemeral=True)
            return
            
        embed = discord.Embed(title="🔘 Boutons Actifs", color=discord.Color.blue())
        
        for btn_id, config in buttons.items():
            channel = self.bot.get_channel(config.channel_id)
            channel_name = channel.name if channel else "Inconnu"
            
            embed.add_field(
                name=f"{config.emoji} {config.label} ({btn_id})",
                value=f"Type: {config.type.value}\nChannel: #{channel_name}",
                inline=True
            )
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="button_templates")
    async def button_templates(self, ctx: commands.Context):
        """Affiche les templates de boutons disponibles"""
        if not self.button_manager:
            return
            
        templates = self.button_manager.get_all_templates()
        
        embed = discord.Embed(
            title="🔘 Templates de Boutons",
            description="Utilisez ces types avec `!button_create`",
            color=discord.Color.blue()
        )
        
        for type_name, template in templates.items():
            embed.add_field(
                name=f"{template['emoji']} {type_name}",
                value=f"{template['label']}\n*{template['description']}*",
                inline=True
            )
            
        await ctx.send(embed=embed, ephemeral=True)
