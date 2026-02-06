"""
📦 EMBED MANAGER - Système d'Embeds Discord (Style MEE6)
Création et gestion d'embeds riches avec boutons de paiement intégrés
"""

import discord
from discord.ext import commands
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
import asyncio


class EmbedAction(Enum):
    """Types d'actions pour les boutons d'embeds"""
    LINK = "link"
    PAYMENT = "payment"
    TICKET = "ticket"
    GIVEAWAY = "giveaway"
    CUSTOM = "custom"
    UPGRADE = "upgrade"
    FEEDBACK = "feedback"


@dataclass
class EmbedButton:
    """Configuration d'un bouton dans un embed"""
    label: str
    emoji: str
    style: str  # primary, secondary, success, danger, premium
    action: EmbedAction
    url: Optional[str] = None
    custom_id: Optional[str] = None
    payment_config: Optional[Dict] = None
    
    def to_dict(self) -> dict:
        return {
            'label': self.label,
            'emoji': self.emoji,
            'style': self.style,
            'action': self.action.value,
            'url': self.url,
            'custom_id': self.custom_id,
            'payment_config': self.payment_config
        }


@dataclass
class EmbedField:
    """Field d'un embed Discord"""
    name: str
    value: str
    inline: bool = True
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'inline': self.inline
        }


@dataclass
class EmbedConfig:
    """Configuration complète d'un embed"""
    id: str
    name: str
    channel_id: int
    message_id: Optional[int] = None
    
    # Embed content
    color: int = 0x5865F2
    author: Optional[str] = None
    author_icon: Optional[str] = None
    author_url: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    footer: Optional[str] = None
    footer_icon: Optional[str] = None
    timestamp: Optional[str] = None
    
    # Components
    fields: List[EmbedField] = None
    buttons: List[EmbedButton] = None
    
    # Metadata
    created_by: int = 0
    created_at: str = ""
    updated_at: str = ""
    views: int = 0
    clicks: int = 0
    is_active: bool = True
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.buttons is None:
            self.buttons = []
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'channel_id': self.channel_id,
            'message_id': self.message_id,
            'color': self.color,
            'author': self.author,
            'author_icon': self.author_icon,
            'author_url': self.author_url,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'image': self.image,
            'thumbnail': self.thumbnail,
            'footer': self.footer,
            'footer_icon': self.footer_icon,
            'timestamp': self.timestamp,
            'fields': [f.to_dict() for f in self.fields],
            'buttons': [b.to_dict() for b in self.buttons],
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'views': self.views,
            'clicks': self.clicks,
            'is_active': self.is_active
        }


class EmbedManager:
    """
    📦 Gestionnaire d'Embeds Discord
    Crée des messages riches avec boutons et paiements intégrés
    """
    
    # Templates prédéfinis
    TEMPLATES = {
        "welcome": {
            "name": "👋 Message de Bienvenue",
            "color": 0x10b981,
            "title": "Bienvenue sur {server_name} !",
            "description": "Nous sommes ravis de t'accueillir !\n\n🎁 **Pour commencer:**\n• Lis les règles\n• Présente-toi\n• Découvre nos offres",
            "footer": "Bon séjour parmi nous !"
        },
        "promo": {
            "name": "🏷️ Promotion/Offre",
            "color": 0xf59e0b,
            "title": "🎉 Offre Spéciale -30% !",
            "description": "**Profitez de notre offre exclusive !**\n\n✨ Plan Pro avec **30% de réduction**\n⏰ Offre limitée dans le temps\n💳 Paiement sécurisé Stripe",
            "footer": "Offre valable jusqu'au 31/01"
        },
        "announcement": {
            "name": "📢 Annonce Importante",
            "color": 0x3b82f6,
            "title": "📢 Nouvelle Mise à Jour",
            "description": "Nous avons ajouté de nouvelles fonctionnalités !\n\n🆕 **Nouveautés:**\n• Système de tickets amélioré\n• Nouveaux rôles communautaires\n• Giveaways automatiques",
            "footer": "Équipe Shellia"
        },
        "giveaway": {
            "name": "🎁 Giveaway",
            "color": 0x8b5cf6,
            "title": "🎁 Giveaway Spécial !",
            "description": "**À gagner:** Plan Pro 3 mois !\n\n👥 **Gagnants:** 2\n⏰ **Fin:** Dans 48h\n🎲 **Tirage:** Aléatoire",
            "footer": "Réagissez 🎉 pour participer"
        },
        "rules": {
            "name": "📜 Règlement",
            "color": 0xef4444,
            "title": "📜 Règlement du Serveur",
            "description": "**Merci de respecter ces règles:**\n\n1️⃣ Soyez respectueux\n2️⃣ Pas de spam\n3️⃣ Pas de contenu NSFW\n4️⃣ Utilisez les bons channels\n5️⃣ Pas de pub sans autorisation",
            "footer": "Dernière mise à jour: 01/2024"
        },
        "shop": {
            "name": "🛍️ Boutique",
            "color": 0x10b981,
            "title": "🛍️ Notre Boutique",
            "description": "**Découvrez nos offres premium:**\n\n⭐ **Pro** - €9.99/mois\n💎 **Ultra** - €19.99/mois\n👑 **Founder** - €99 lifetime\n\nPaiement sécurisé via Stripe 🔒",
            "footer": "30 jours garantie satisfait/remboursé"
        }
    }
    
    def __init__(self, bot: commands.Bot, db=None, stripe_manager=None):
        self.bot = bot
        self.db = db
        self.stripe_manager = stripe_manager
        self.embeds: Dict[str, EmbedConfig] = {}
        self.views: Dict[str, discord.ui.View] = {}
        
    async def setup(self):
        """Initialise le gestionnaire d'embeds"""
        if self.db:
            await self._load_embeds_from_db()
        print("✅ EmbedManager initialisé")
        
    async def _load_embeds_from_db(self):
        """Charge les embeds persistants"""
        try:
            result = await self.db.fetch(
                "SELECT * FROM discord_embeds WHERE is_active = TRUE"
            )
            for row in result:
                config = EmbedConfig(
                    id=row['id'],
                    name=row['name'],
                    channel_id=row['channel_id'],
                    message_id=row['message_id'],
                    color=row['color'],
                    author=row.get('author'),
                    author_icon=row.get('author_icon'),
                    author_url=row.get('author_url'),
                    title=row.get('title'),
                    url=row.get('url'),
                    description=row.get('description'),
                    image=row.get('image'),
                    thumbnail=row.get('thumbnail'),
                    footer=row.get('footer'),
                    footer_icon=row.get('footer_icon'),
                    timestamp=row.get('timestamp'),
                    fields=[EmbedField(**f) for f in row.get('fields', [])],
                    buttons=[EmbedButton(**b) for b in row.get('buttons', [])],
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    views=row.get('views', 0),
                    clicks=row.get('clicks', 0),
                    is_active=row.get('is_active', True)
                )
                self.embeds[config.id] = config
        except Exception as e:
            print(f"⚠️ Erreur chargement embeds: {e}")
            
    def create_embed_from_config(self, config: EmbedConfig) -> discord.Embed:
        """Crée un discord.Embed depuis la configuration"""
        embed = discord.Embed(
            title=config.title,
            description=config.description,
            color=config.color,
            url=config.url
        )
        
        # Author
        if config.author:
            embed.set_author(
                name=config.author,
                icon_url=config.author_icon,
                url=config.author_url
            )
        
        # Image & Thumbnail
        if config.image:
            embed.set_image(url=config.image)
        if config.thumbnail:
            embed.set_thumbnail(url=config.thumbnail)
        
        # Footer
        if config.footer:
            embed.set_footer(
                text=config.footer,
                icon_url=config.footer_icon
            )
        
        # Timestamp
        if config.timestamp:
            if config.timestamp == "current":
                embed.timestamp = datetime.utcnow()
            else:
                try:
                    embed.timestamp = datetime.fromisoformat(config.timestamp)
                except:
                    pass
        
        # Fields
        for field in config.fields:
            embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )
            
        return embed
    
    def create_view_from_config(self, config: EmbedConfig) -> discord.ui.View:
        """Crée une View avec les boutons de l'embed"""
        view = discord.ui.View(timeout=None)
        
        for button_config in config.buttons:
            style_map = {
                'primary': discord.ButtonStyle.primary,
                'secondary': discord.ButtonStyle.secondary,
                'success': discord.ButtonStyle.success,
                'danger': discord.ButtonStyle.danger,
                'premium': discord.ButtonStyle.primary
            }
            
            style = style_map.get(button_config.style, discord.ButtonStyle.primary)
            
            if button_config.action == EmbedAction.LINK and button_config.url:
                button = discord.ui.Button(
                    style=style,
                    label=button_config.label,
                    emoji=button_config.emoji if button_config.emoji else None,
                    url=button_config.url
                )
            else:
                custom_id = f"embed_{config.id}_{button_config.custom_id or uuid.uuid4().hex[:8]}"
                button = discord.ui.Button(
                    style=style,
                    label=button_config.label,
                    emoji=button_config.emoji if button_config.emoji else None,
                    custom_id=custom_id
                )
                # Store callback
                button.callback = self._create_button_callback(config.id, button_config)
                
            view.add_item(button)
            
        return view
    
    def _create_button_callback(self, embed_id: str, button_config: EmbedButton):
        """Crée un callback pour un bouton"""
        async def callback(interaction: discord.Interaction):
            await self._handle_button_click(interaction, embed_id, button_config)
        return callback
    
    async def _handle_button_click(self, interaction: discord.Interaction, embed_id: str, button_config: EmbedButton):
        """Gère les clics sur les boutons d'embed"""
        user_id = interaction.user.id
        
        # Log le click
        await self._log_embed_click(embed_id, button_config.custom_id, user_id)
        
        # Traiter selon l'action
        if button_config.action == EmbedAction.PAYMENT:
            await self._handle_payment_button(interaction, button_config)
        elif button_config.action == EmbedAction.TICKET:
            await self._handle_ticket_button(interaction, button_config)
        elif button_config.action == EmbedAction.UPGRADE:
            await self._handle_upgrade_button(interaction, button_config)
        elif button_config.action == EmbedAction.GIVEAWAY:
            await self._handle_giveaway_button(interaction, button_config)
        elif button_config.action == EmbedAction.FEEDBACK:
            await self._handle_feedback_button(interaction, button_config)
        elif button_config.action == EmbedAction.CUSTOM:
            await self._handle_custom_button(interaction, button_config)
        else:
            await interaction.response.send_message(
                f"🔄 Action: {button_config.label}",
                ephemeral=True
            )
            
    async def _handle_payment_button(self, interaction: discord.Interaction, button_config: EmbedButton):
        """Gère les boutons de paiement"""
        if not button_config.payment_config:
            await interaction.response.send_message("❌ Configuration de paiement invalide", ephemeral=True)
            return
            
        product_id = button_config.payment_config.get('product_id')
        display_price = button_config.payment_config.get('display_price', '€9.99')
        
        # Créer une session Stripe Checkout
        if self.stripe_manager:
            try:
                session = await self.stripe_manager.create_checkout_session(
                    user_id=interaction.user.id,
                    price_id=product_id,
                    success_url="https://shellia.ai/success",
                    cancel_url="https://shellia.ai/cancel"
                )
                
                # Envoyer le lien en DM ou ephemeral
                await interaction.response.send_message(
                    f"💳 **Paiement sécurisé**\n\n"
                    f"Montant: {display_price}\n\n"
                    f"Cliquez sur le lien ci-dessous pour finaliser votre achat:\n"
                    f"🔗 {session['checkout_url']}",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Erreur lors de la création du paiement: {str(e)}",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "💳 Système de paiement temporairement indisponible",
                ephemeral=True
            )
            
    async def _handle_ticket_button(self, interaction: discord.Interaction, button_config: EmbedButton):
        """Ouvre un modal pour créer un ticket"""
        modal = TicketCreateModal()
        await interaction.response.send_modal(modal)
        
    async def _handle_upgrade_button(self, interaction: discord.Interaction, button_config: EmbedButton):
        """Affiche les options d'upgrade"""
        embed = discord.Embed(
            title="⭐ Passez au niveau supérieur !",
            description="Découvrez nos plans premium:",
            color=0xffd700
        )
        embed.add_field(name="Pro", value="€9.99/mois\n✨ Toutes les fonctionnalités", inline=True)
        embed.add_field(name="Ultra", value="€19.99/mois\n💎 Support VIP", inline=True)
        embed.add_field(name="Founder", value="€99 une fois\n👀 Accès à vie", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    async def _handle_giveaway_button(self, interaction: discord.Interaction, button_config: EmbedButton):
        """Inscrit l'utilisateur au giveaway"""
        await interaction.response.send_message(
            "🎁 **Inscription au giveaway !**\n\n"
            "Vous êtes maintenant inscrit.\n"
            "Bonne chance ! 🍀",
            ephemeral=True
        )
        
    async def _handle_feedback_button(self, interaction: discord.Interaction, button_config: EmbedButton):
        """Ouvre un modal de feedback"""
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)
        
    async def _handle_custom_button(self, interaction: discord.Interaction, button_config: EmbedButton):
        """Gère les actions personnalisées"""
        custom_action = button_config.payment_config.get('custom_action', 'default') if button_config.payment_config else 'default'
        await interaction.response.send_message(
            f"🔧 Action personnalisée: {custom_action}",
            ephemeral=True
        )
        
    async def create_embed(self, config_data: dict) -> EmbedConfig:
        """Crée un nouvel embed"""
        config = EmbedConfig(
            id=str(uuid.uuid4())[:8],
            name=config_data.get('name', 'Unnamed Embed'),
            channel_id=config_data['channel_id'],
            color=int(config_data.get('color', '#5865F2').replace('#', ''), 16),
            author=config_data.get('author'),
            author_icon=config_data.get('author_icon'),
            author_url=config_data.get('author_url'),
            title=config_data.get('title'),
            url=config_data.get('url'),
            description=config_data.get('description'),
            image=config_data.get('image'),
            thumbnail=config_data.get('thumbnail'),
            footer=config_data.get('footer'),
            footer_icon=config_data.get('footer_icon'),
            timestamp=config_data.get('timestamp'),
            fields=[EmbedField(**f) for f in config_data.get('fields', [])],
            buttons=[EmbedButton(
                label=b['label'],
                emoji=b.get('emoji', ''),
                style=b.get('style', 'primary'),
                action=EmbedAction(b.get('action', 'link')),
                url=b.get('url'),
                custom_id=b.get('custom_id'),
                payment_config=b.get('payment_config')
            ) for b in config_data.get('buttons', [])],
            created_by=config_data.get('created_by', 0),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Sauvegarder en DB
        if self.db:
            await self.db.execute(
                """
                INSERT INTO discord_embeds 
                (id, name, channel_id, color, author, author_icon, author_url, title, url, description,
                 image, thumbnail, footer, footer_icon, timestamp, fields, buttons, created_by, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                """,
                config.id, config.name, config.channel_id, config.color, config.author,
                config.author_icon, config.author_url, config.title, config.url, config.description,
                config.image, config.thumbnail, config.footer, config.footer_icon, config.timestamp,
                json.dumps([f.to_dict() for f in config.fields]),
                json.dumps([b.to_dict() for b in config.buttons]),
                config.created_by, config.created_at
            )
            
        self.embeds[config.id] = config
        return config
        
    async def send_embed(self, embed_id: str) -> bool:
        """Envoie l'embed sur Discord"""
        config = self.embeds.get(embed_id)
        if not config:
            return False
            
        channel = self.bot.get_channel(config.channel_id)
        if not channel:
            print(f"❌ Channel {config.channel_id} introuvable")
            return False
            
        try:
            # Créer l'embed et la view
            embed = self.create_embed_from_config(config)
            view = self.create_view_from_config(config)
            
            # Envoyer
            message = await channel.send(embed=embed, view=view)
            config.message_id = message.id
            
            # Mettre à jour la DB
            if self.db:
                await self.db.execute(
                    "UPDATE discord_embeds SET message_id = $1 WHERE id = $2",
                    message.id, embed_id
                )
                
            print(f"✅ Embed {embed_id} envoyé sur {channel.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi embed: {e}")
            return False
            
    async def update_embed(self, embed_id: str, updates: dict) -> bool:
        """Met à jour un embed existant"""
        config = self.embeds.get(embed_id)
        if not config:
            return False
            
        # Mettre à jour les champs
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
        config.updated_at = datetime.utcnow().isoformat()
        
        # Mettre à jour sur Discord si message existe
        if config.message_id:
            channel = self.bot.get_channel(config.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(config.message_id)
                    embed = self.create_embed_from_config(config)
                    view = self.create_view_from_config(config)
                    await message.edit(embed=embed, view=view)
                except Exception as e:
                    print(f"⚠️ Erreur mise à jour message: {e}")
                    
        # Mettre à jour la DB
        if self.db:
            await self.db.execute(
                """
                UPDATE discord_embeds 
                SET name = $1, color = $2, author = $3, author_icon = $4, title = $5,
                    description = $6, image = $7, thumbnail = $8, footer = $9, 
                    fields = $10, buttons = $11, updated_at = $12
                WHERE id = $13
                """,
                config.name, config.color, config.author, config.author_icon, config.title,
                config.description, config.image, config.thumbnail, config.footer,
                json.dumps([f.to_dict() for f in config.fields]),
                json.dumps([b.to_dict() for b in config.buttons]),
                config.updated_at, embed_id
            )
            
        return True
        
    async def delete_embed(self, embed_id: str) -> bool:
        """Supprime un embed"""
        config = self.embeds.get(embed_id)
        if not config:
            return False
            
        try:
            # Supprimer le message Discord
            if config.message_id:
                channel = self.bot.get_channel(config.channel_id)
                if channel:
                    message = await channel.fetch_message(config.message_id)
                    await message.delete()
                    
            # Marquer comme inactif en DB
            if self.db:
                await self.db.execute(
                    "UPDATE discord_embeds SET is_active = FALSE WHERE id = $1",
                    embed_id
                )
                
            del self.embeds[embed_id]
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression embed: {e}")
            return False
            
    async def _log_embed_click(self, embed_id: str, button_id: Optional[str], user_id: int):
        """Log les clics sur les embeds"""
        if self.db:
            await self.db.execute(
                """
                INSERT INTO embed_analytics (embed_id, button_id, user_id, clicked_at)
                VALUES ($1, $2, $3, $4)
                """,
                embed_id, button_id, user_id, datetime.utcnow().isoformat()
            )
            
        # Incrémenter le compteur
        if embed_id in self.embeds:
            self.embeds[embed_id].clicks += 1
            
    async def get_embed_stats(self, embed_id: Optional[str] = None) -> Dict:
        """Récupère les statistiques d'utilisation"""
        if not self.db:
            return {}
            
        if embed_id:
            result = await self.db.fetch(
                """
                SELECT 
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT user_id) as unique_users,
                    MAX(clicked_at) as last_click
                FROM embed_analytics 
                WHERE embed_id = $1
                """,
                embed_id
            )
            return dict(result[0]) if result else {}
        else:
            result = await self.db.fetch(
                """
                SELECT 
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT embed_id) as active_embeds
                FROM embed_analytics 
                WHERE clicked_at > NOW() - INTERVAL '30 days'
                """
            )
            return dict(result[0]) if result else {}
            
    def get_all_templates(self) -> Dict:
        """Retourne tous les templates disponibles"""
        return self.TEMPLATES
        
    def apply_template(self, template_name: str, server_name: str = "Server") -> Dict:
        """Applique un template et retourne la config"""
        template = self.TEMPLATES.get(template_name, {})
        config = {
            'name': template.get('name', 'Unnamed'),
            'color': template.get('color', 0x5865F2),
            'title': template.get('title', '').replace('{server_name}', server_name),
            'description': template.get('description', ''),
            'footer': template.get('footer', '')
        }
        
        # Ajouter des boutons par défaut selon le template
        if template_name in ['promo', 'shop']:
            config['buttons'] = [{
                'label': 'Acheter maintenant',
                'emoji': '💳',
                'style': 'premium',
                'action': 'payment',
                'payment_config': {'product_id': 'price_pro_monthly'}
            }]
        elif template_name == 'giveaway':
            config['buttons'] = [{
                'label': 'Participer',
                'emoji': '🎉',
                'style': 'success',
                'action': 'giveaway'
            }]
            
        return config


class TicketCreateModal(discord.ui.Modal, title="Créer un ticket"):
    """Modal pour créer un ticket via embed"""
    
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
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Ticket créé !\nSujet: {self.subject}\nUn agent vous répondra sous peu.",
            ephemeral=True
        )


class FeedbackModal(discord.ui.Modal, title="Votre avis"):
    """Modal pour donner son avis"""
    
    rating = discord.ui.TextInput(
        label="Note (1-5)",
        placeholder="5",
        max_length=1
    )
    
    comment = discord.ui.TextInput(
        label="Commentaire",
        style=discord.TextStyle.paragraph,
        placeholder="Dites-nous ce que vous pensez...",
        max_length=1000,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"⭐ Merci pour votre note de {self.rating}/5 !",
            ephemeral=True
        )


class EmbedCommands(commands.Cog):
    """Commandes Discord pour gérer les embeds"""
    
    def __init__(self, bot):
        self.bot = bot
        self.embed_manager = None
        
    def setup_manager(self, manager: EmbedManager):
        self.embed_manager = manager
        
    @commands.hybrid_command(name="embed_send")
    @commands.has_permissions(administrator=True)
    async def embed_send(self, ctx: commands.Context, embed_id: str):
        """📦 Envoie un embed sur son channel"""
        if not self.embed_manager:
            await ctx.send("❌ EmbedManager non disponible", ephemeral=True)
            return
            
        success = await self.embed_manager.send_embed(embed_id)
        
        if success:
            await ctx.send(f"✅ Embed `{embed_id}` envoyé !", ephemeral=True)
        else:
            await ctx.send("❌ Erreur lors de l'envoi", ephemeral=True)
            
    @commands.hybrid_command(name="embed_list")
    @commands.has_permissions(administrator=True)
    async def embed_list(self, ctx: commands.Context):
        """📦 Liste tous les embeds"""
        if not self.embed_manager:
            return
            
        embeds = self.embed_manager.embeds
        
        if not embeds:
            await ctx.send("Aucun embed actif", ephemeral=True)
            return
            
        embed = discord.Embed(title="📦 Embeds Actifs", color=discord.Color.blue())
        
        for emb_id, config in embeds.items():
            channel = self.bot.get_channel(config.channel_id)
            channel_name = channel.name if channel else "Inconnu"
            
            embed.add_field(
                name=f"{config.name} ({emb_id})",
                value=f"Channel: #{channel_name}\nClicks: {config.clicks}",
                inline=True
            )
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="embed_stats")
    @commands.has_permissions(administrator=True)
    async def embed_stats(self, ctx: commands.Context, embed_id: str):
        """📊 Stats d'un embed"""
        if not self.embed_manager:
            return
            
        stats = await self.embed_manager.get_embed_stats(embed_id)
        
        embed = discord.Embed(
            title=f"📊 Stats Embed {embed_id}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Clicks", value=stats.get('total_clicks', 0), inline=True)
        embed.add_field(name="Utilisateurs uniques", value=stats.get('unique_users', 0), inline=True)
        
        await ctx.send(embed=embed, ephemeral=True)
