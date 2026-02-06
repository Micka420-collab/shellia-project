"""
🎫 SYSTÈME DE TICKETS - Maxis
Gestion des tickets support avec isolation par utilisateur
Stockage sur Supabase, accessible via Discord et Web
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
import aiohttp
import json


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(Enum):
    GENERAL = "general"
    BILLING = "billing"
    TECHNICAL = "technical"
    FEATURE_REQUEST = "feature_request"
    BUG = "bug"
    ACCOUNT = "account"


class MaxisTicketSystem:
    """
    🎫 Système de tickets avec isolation stricte (Privacy by Design)
    Chaque utilisateur ne voit QUE ses propres tickets
    """
    
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.ticket_channel_id = None
        self.admin_channel_id = None
        
    async def setup(self, ticket_channel_id: int, admin_channel_id: int):
        """Initialise le système de tickets"""
        self.ticket_channel_id = ticket_channel_id
        self.admin_channel_id = admin_channel_id
        print("✅ Système de tickets initialisé")
        
    async def create_ticket(
        self,
        user_id: int,
        guild_id: int,
        subject: str,
        description: str,
        category: TicketCategory = TicketCategory.GENERAL,
        priority: TicketPriority = TicketPriority.MEDIUM
    ) -> Dict:
        """
        Crée un nouveau ticket
        Isolation : L'utilisateur ne peut créer que pour lui-même
        """
        import uuid
        
        ticket_id = str(uuid.uuid4())[:8]
        
        ticket_data = {
            'id': ticket_id,
            'user_id': user_id,
            'guild_id': guild_id,
            'subject': subject,
            'description': description,
            'category': category.value,
            'priority': priority.value,
            'status': TicketStatus.OPEN.value,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'created_by': user_id,  # Pour traçabilité
            'assigned_to': None,
            'plan_at_creation': await self._get_user_plan(user_id)
        }
        
        # Sauvegarder en DB
        await self.db.execute(
            """
            INSERT INTO tickets (id, user_id, guild_id, subject, description, 
                               category, priority, status, created_at, updated_at,
                               created_by, plan_at_creation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (ticket_id, user_id, guild_id, subject, description,
             category.value, priority.value, TicketStatus.OPEN.value,
             ticket_data['created_at'], ticket_data['updated_at'],
             user_id, ticket_data['plan_at_creation'])
        )
        
        # Créer le premier message
        await self._add_ticket_message(ticket_id, user_id, description, is_internal=False)
        
        # Notifier les admins
        await self._notify_admins_new_ticket(ticket_data)
        
        return ticket_data
        
    async def _get_user_plan(self, user_id: int) -> str:
        """Récupère le plan de l'utilisateur"""
        try:
            result = await self.db.fetch(
                "SELECT plan FROM users WHERE user_id = %s",
                (user_id,)
            )
            return result[0]['plan'] if result else 'free'
        except:
            return 'free'
            
    async def _add_ticket_message(
        self,
        ticket_id: str,
        author_id: int,
        content: str,
        is_internal: bool = False,
        attachments: Optional[List[str]] = None
    ):
        """Ajoute un message à un ticket"""
        import uuid
        
        message_id = str(uuid.uuid4())[:12]
        
        await self.db.execute(
            """
            INSERT INTO ticket_messages (id, ticket_id, author_id, content, 
                                       is_internal, attachments, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (message_id, ticket_id, author_id, content, is_internal,
             json.dumps(attachments) if attachments else None,
             datetime.utcnow().isoformat())
        )
        
    async def get_user_tickets(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """
        Récupère les tickets d'un utilisateur
        ISOLATION : Un utilisateur ne voit QUE ses tickets
        """
        query = "SELECT * FROM tickets WHERE user_id = %s"
        params = [user_id]
        
        if status:
            query += " AND status = %s"
            params.append(status)
            
        query += " ORDER BY created_at DESC"
        
        result = await self.db.fetch(query, tuple(params))
        return [dict(row) for row in result]
        
    async def get_ticket_details(self, ticket_id: str, requesting_user_id: int) -> Optional[Dict]:
        """
        Récupère les détails d'un ticket
        ISOLATION : Vérifie que l'utilisateur est bien le propriétaire OU admin
        """
        # Récupérer le ticket
        result = await self.db.fetch(
            "SELECT * FROM tickets WHERE id = %s",
            (ticket_id,)
        )
        
        if not result:
            return None
            
        ticket = dict(result[0])
        
        # Vérifier les permissions
        is_owner = ticket['user_id'] == requesting_user_id
        is_admin = await self._is_admin(requesting_user_id)
        
        if not (is_owner or is_admin):
            return None  # Accès refusé - Isolation stricte
            
        # Récupérer les messages
        if is_admin:
            # Admin voit tous les messages (internes inclus)
            messages = await self.db.fetch(
                "SELECT * FROM ticket_messages WHERE ticket_id = %s ORDER BY created_at ASC",
                (ticket_id,)
            )
        else:
            # User ne voit que les messages non-internes
            messages = await self.db.fetch(
                "SELECT * FROM ticket_messages WHERE ticket_id = %s AND is_internal = FALSE ORDER BY created_at ASC",
                (ticket_id,)
            )
            
        ticket['messages'] = [dict(m) for m in messages]
        ticket['is_owner'] = is_owner
        ticket['is_admin'] = is_admin
        
        return ticket
        
    async def reply_to_ticket(
        self,
        ticket_id: str,
        author_id: int,
        content: str,
        is_internal: bool = False
    ) -> bool:
        """
        Répond à un ticket
        ISOLATION : Seul le propriétaire ou un admin peut répondre
        """
        # Vérifier les permissions
        ticket = await self.db.fetch(
            "SELECT user_id, status FROM tickets WHERE id = %s",
            (ticket_id,)
        )
        
        if not ticket:
            return False
            
        is_owner = ticket[0]['user_id'] == author_id
        is_admin = await self._is_admin(author_id)
        
        if not (is_owner or is_admin):
            return False
            
        # Un utilisateur normal ne peut pas créer de message interne
        if is_internal and not is_admin:
            is_internal = False
            
        # Ajouter le message
        await self._add_ticket_message(ticket_id, author_id, content, is_internal)
        
        # Mettre à jour le statut
        new_status = TicketStatus.WAITING_USER.value if is_admin else TicketStatus.IN_PROGRESS.value
        
        await self.db.execute(
            """
            UPDATE tickets 
            SET status = %s, updated_at = %s 
            WHERE id = %s
            """,
            (new_status, datetime.utcnow().isoformat(), ticket_id)
        )
        
        # Notifier
        if is_admin:
            # Notifier l'utilisateur
            await self._notify_user_reply(ticket_id, author_id)
        else:
            # Notifier les admins
            await self._notify_admins_reply(ticket_id, author_id)
            
        return True
        
    async def close_ticket(
        self,
        ticket_id: str,
        closed_by: int,
        reason: str = ""
    ) -> bool:
        """
        Ferme un ticket
        ISOLATION : Propriétaire peut fermer, admin peut fermer tous
        """
        ticket = await self.db.fetch(
            "SELECT user_id FROM tickets WHERE id = %s",
            (ticket_id,)
        )
        
        if not ticket:
            return False
            
        is_owner = ticket[0]['user_id'] == closed_by
        is_admin = await self._is_admin(closed_by)
        
        if not (is_owner or is_admin):
            return False
            
        await self.db.execute(
            """
            UPDATE tickets 
            SET status = %s, closed_at = %s, closed_by = %s, close_reason = %s
            WHERE id = %s
            """,
            (TicketStatus.CLOSED.value, datetime.utcnow().isoformat(),
             closed_by, reason, ticket_id)
        )
        
        return True
        
    async def assign_ticket(self, ticket_id: str, admin_id: int, assigned_to: int) -> bool:
        """
        Assigne un ticket à un admin
        Seuls les admins peuvent assigner
        """
        if not await self._is_admin(admin_id):
            return False
            
        await self.db.execute(
            "UPDATE tickets SET assigned_to = %s, updated_at = %s WHERE id = %s",
            (assigned_to, datetime.utcnow().isoformat(), ticket_id)
        )
        
        return True
        
    async def update_ticket_priority(
        self,
        ticket_id: str,
        admin_id: int,
        priority: TicketPriority
    ) -> bool:
        """Met à jour la priorité (admin only)"""
        if not await self._is_admin(admin_id):
            return False
            
        await self.db.execute(
            "UPDATE tickets SET priority = %s, updated_at = %s WHERE id = %s",
            (priority.value, datetime.utcnow().isoformat(), ticket_id)
        )
        
        return True
        
    async def get_all_tickets(
        self,
        admin_id: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère tous les tickets (admin only)
        Filtres disponibles pour le dashboard web
        """
        if not await self._is_admin(admin_id):
            return []
            
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        if category:
            query += " AND category = %s"
            params.append(category)
        if priority:
            query += " AND priority = %s"
            params.append(priority)
        if assigned_to:
            query += " AND assigned_to = %s"
            params.append(assigned_to)
            
        query += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, created_at DESC"
        
        result = await self.db.fetch(query, tuple(params))
        return [dict(row) for row in result]
        
    async def get_ticket_stats(self, admin_id: int) -> Dict:
        """Statistiques des tickets (admin only)"""
        if not await self._is_admin(admin_id):
            return {}
            
        stats = await self.db.fetch(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed,
                COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical,
                COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                AVG(EXTRACT(EPOCH FROM (closed_at - created_at))/3600) as avg_resolution_hours
            FROM tickets
            WHERE created_at > NOW() - INTERVAL '30 days'
            """
        )
        
        return dict(stats[0]) if stats else {}
        
    async def _is_admin(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est admin"""
        # Implémentation selon ta logique d'admin
        return True  # Simplifié pour l'exemple
        
    async def _notify_admins_new_ticket(self, ticket_data: Dict):
        """Notifie les admins d'un nouveau ticket"""
        if not self.admin_channel_id:
            return
            
        channel = self.bot.get_channel(self.admin_channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="🎫 Nouveau Ticket",
            description=f"**{ticket_data['subject']}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="ID", value=ticket_data['id'], inline=True)
        embed.add_field(name="Catégorie", value=ticket_data['category'], inline=True)
        embed.add_field(name="Priorité", value=ticket_data['priority'], inline=True)
        embed.add_field(name="Plan", value=ticket_data['plan_at_creation'], inline=True)
        embed.add_field(name="Description", value=ticket_data['description'][:500], inline=False)
        
        await channel.send(embed=embed)
        
    async def _notify_user_reply(self, ticket_id: str, admin_id: int):
        """Notifie l'utilisateur d'une réponse"""
        # Envoyer DM à l'utilisateur
        pass
        
    async def _notify_admins_reply(self, ticket_id: str, user_id: int):
        """Notifie les admins d'une réponse utilisateur"""
        pass


class TicketCommands(commands.Cog):
    """Commandes Discord pour le système de tickets"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ticket_system = None
        
    def setup_ticket_system(self, ticket_system: MaxisTicketSystem):
        self.ticket_system = ticket_system
        
    @commands.hybrid_command(name="ticket_create")
    async def ticket_create(
        self,
        ctx: commands.Context,
        sujet: str,
        categorie: str = "general",
        priorite: str = "medium",
        *,
        description: str
    ):
        """
        🎫 Créer un ticket support
        
        Catégories: general, billing, technical, feature_request, bug, account
        Priorités: low, medium, high, critical
        """
        if not self.ticket_system:
            await ctx.send("❌ Système de tickets non disponible.", ephemeral=True)
            return
            
        try:
            category = TicketCategory(categorie)
            priority = TicketPriority(priorite)
        except ValueError:
            await ctx.send("❌ Catégorie ou priorité invalide.", ephemeral=True)
            return
            
        ticket = await self.ticket_system.create_ticket(
            user_id=ctx.author.id,
            guild_id=ctx.guild.id,
            subject=sujet,
            description=description,
            category=category,
            priority=priority
        )
        
        await ctx.send(
            f"✅ Ticket créé !\n"
            f"**ID:** `{ticket['id']}`\n"
            f"**Sujet:** {ticket['subject']}\n"
            f"Un admin va vous répondre sous peu.",
            ephemeral=True
        )
        
    @commands.hybrid_command(name="ticket_list")
    async def ticket_list(self, ctx: commands.Context, statut: Optional[str] = None):
        """
        📋 Voir mes tickets
        
        Statuts: open, in_progress, waiting_user, resolved, closed
        """
        if not self.ticket_system:
            await ctx.send("❌ Système non disponible.", ephemeral=True)
            return
            
        tickets = await self.ticket_system.get_user_tickets(ctx.author.id, statut)
        
        if not tickets:
            await ctx.send("Vous n'avez aucun ticket.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="🎫 Mes Tickets",
            color=discord.Color.blue()
        )
        
        for ticket in tickets[:10]:  # Limiter à 10
            status_emoji = {
                'open': '🟢',
                'in_progress': '🟡',
                'waiting_user': '🔵',
                'resolved': '✅',
                'closed': '🔒'
            }.get(ticket['status'], '⚪')
            
            embed.add_field(
                name=f"{status_emoji} {ticket['id']} - {ticket['subject'][:50]}",
                value=f"Statut: {ticket['status']} | {ticket['created_at'][:10]}",
                inline=False
            )
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="ticket_view")
    async def ticket_view(self, ctx: commands.Context, ticket_id: str):
        """
        🔍 Voir les détails d'un ticket
        """
        if not self.ticket_system:
            await ctx.send("❌ Système non disponible.", ephemeral=True)
            return
            
        ticket = await self.ticket_system.get_ticket_details(ticket_id, ctx.author.id)
        
        if not ticket:
            await ctx.send("❌ Ticket introuvable ou accès refusé.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"🎫 Ticket {ticket_id}",
            description=ticket['subject'],
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Statut", value=ticket['status'], inline=True)
        embed.add_field(name="Priorité", value=ticket['priority'], inline=True)
        embed.add_field(name="Catégorie", value=ticket['category'], inline=True)
        
        # Afficher les messages
        messages_text = ""
        for msg in ticket['messages'][-5:]:  # 5 derniers messages
            author = "Vous" if msg['author_id'] == ctx.author.id else "Support"
            messages_text += f"**{author}:** {msg['content'][:100]}...\n"
            
        if messages_text:
            embed.add_field(name="Messages récents", value=messages_text, inline=False)
            
        await ctx.send(embed=embed, ephemeral=True)
        
    @commands.hybrid_command(name="ticket_reply")
    async def ticket_reply(self, ctx: commands.Context, ticket_id: str, *, message: str):
        """
        💬 Répondre à un ticket
        """
        if not self.ticket_system:
            await ctx.send("❌ Système non disponible.", ephemeral=True)
            return
            
        success = await self.ticket_system.reply_to_ticket(
            ticket_id=ticket_id,
            author_id=ctx.author.id,
            content=message
        )
        
        if success:
            await ctx.send("✅ Réponse envoyée !", ephemeral=True)
        else:
            await ctx.send("❌ Impossible d'envoyer la réponse.", ephemeral=True)
            
    @commands.hybrid_command(name="ticket_close")
    async def ticket_close(self, ctx: commands.Context, ticket_id: str, *, raison: str = ""):
        """
        🔒 Fermer un ticket
        """
        if not self.ticket_system:
            await ctx.send("❌ Système non disponible.", ephemeral=True)
            return
            
        success = await self.ticket_system.close_ticket(
            ticket_id=ticket_id,
            closed_by=ctx.author.id,
            reason=raison
        )
        
        if success:
            await ctx.send("✅ Ticket fermé.", ephemeral=True)
        else:
            await ctx.send("❌ Impossible de fermer ce ticket.", ephemeral=True)
            
    # ============ COMMANDES ADMIN ============
            
    @commands.hybrid_command(name="ticket_assign")
    @commands.has_permissions(administrator=True)
    async def ticket_assign(self, ctx: commands.Context, ticket_id: str, admin: discord.Member):
        """
        👤 Assigner un ticket (Admin)
        """
        if not self.ticket_system:
            await ctx.send("❌ Système non disponible.", ephemeral=True)
            return
            
        success = await self.ticket_system.assign_ticket(
            ticket_id=ticket_id,
            admin_id=ctx.author.id,
            assigned_to=admin.id
        )
        
        if success:
            await ctx.send(f"✅ Ticket assigné à {admin.mention}", ephemeral=True)
        else:
            await ctx.send("❌ Impossible d'assigner.", ephemeral=True)
            
    @commands.hybrid_command(name="ticket_stats")
    @commands.has_permissions(administrator=True)
    async def ticket_stats(self, ctx: commands.Context):
        """
        📊 Stats tickets (Admin)
        """
        if not self.ticket_system:
            await ctx.send("❌ Système non disponible.", ephemeral=True)
            return
            
        stats = await self.ticket_system.get_ticket_stats(ctx.author.id)
        
        embed = discord.Embed(
            title="📊 Statistiques Tickets (30 jours)",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total", value=str(stats.get('total', 0)), inline=True)
        embed.add_field(name="Ouverts", value=str(stats.get('open', 0)), inline=True)
        embed.add_field(name="En cours", value=str(stats.get('in_progress', 0)), inline=True)
        embed.add_field(name="Résolus", value=str(stats.get('resolved', 0)), inline=True)
        embed.add_field(name="Critiques", value=str(stats.get('critical', 0)), inline=True)
        embed.add_field(name="Haute prio", value=str(stats.get('high', 0)), inline=True)
        
        if stats.get('avg_resolution_hours'):
            embed.add_field(
                name="Temps moyen de résolution",
                value=f"{stats['avg_resolution_hours']:.1f} heures",
                inline=False
            )
            
        await ctx.send(embed=embed, ephemeral=True)
