"""
BOT PRINCIPAL - Shellia AI Bot avec Supabase
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands

from config import EnvConfig, SecurityConfig, PLANS, ChannelConfig, StreakConfig
from supabase_client import SupabaseDB
from security import SecurityManager
from ai_engine import AIManager


class ShelliaBot(commands.Bot):
    """Bot Discord Shellia AI"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.db = SupabaseDB()
        self.security = SecurityManager(self.db)
        self.ai = AIManager(EnvConfig.GEMINI_API_KEY, self.db)
        
        self.created_roles = {}
    
    async def setup_hook(self):
        """Setup initial"""
        print(f'✅ Bot connecté: {self.user}')
        
        # Sync commandes
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} commandes slash synchronisées")
        except Exception as e:
            print(f"❌ Erreur sync: {e}")
        
        # Démarrer tâches
        self.daily_reset.start()
    
    async def on_ready(self):
        """Bot prêt"""
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="vos messages | /help"
            )
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """Rejoint un serveur"""
        print(f"🆕 Nouveau serveur: {guild.name}")
        await self.setup_guild(guild)
    
    async def setup_guild(self, guild: discord.Guild):
        """Configure automatiquement le serveur"""
        # Créer les rôles
        await self._create_roles(guild)
        
        # Créer les channels
        await self._create_channels(guild)
        
        # Message de bienvenue
        welcome = discord.utils.get(guild.text_channels, name='👋│bienvenue')
        if welcome:
            embed = discord.Embed(
                title="🤖 Shellia AI est en ligne !",
                description="Le serveur a été configuré automatiquement.",
                color=discord.Color.blue()
            )
            await welcome.send(embed=embed)
    
    async def _create_roles(self, guild: discord.Guild):
        """Crée les rôles automatiquement"""
        for role_key, role_config in SecurityConfig.ROLES.items():
            existing = discord.utils.get(guild.roles, name=role_config['name'])
            if existing:
                self.created_roles[role_key] = existing
                continue
            
            try:
                # Permissions
                perms = discord.Permissions()
                for perm_name in role_config.get('permissions', []):
                    setattr(perms, perm_name, True)
                
                role = await guild.create_role(
                    name=role_config['name'],
                    color=discord.Color(role_config['color']),
                    permissions=perms,
                    hoist=role_config['hoist'],
                    mentionable=role_config['mentionable']
                )
                
                self.created_roles[role_key] = role
                print(f"✅ Rôle créé: {role_config['name']}")
                
            except Exception as e:
                print(f"❌ Erreur création rôle {role_config['name']}: {e}")
    
    async def _create_channels(self, guild: discord.Guild):
        """Crée les channels automatiquement"""
        for cat_key, cat_config in ChannelConfig.CATEGORIES.items():
            # Vérifier si catégorie existe
            existing_cat = discord.utils.get(guild.categories, name=cat_config['name'])
            
            if existing_cat:
                category = existing_cat
            else:
                # Permissions pour la catégorie
                overwrites = {}
                
                if cat_key == 'ADMIN':
                    overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                    if 'ADMIN' in self.created_roles:
                        overwrites[self.created_roles['ADMIN']] = discord.PermissionOverwrite(view_channel=True)
                
                elif cat_key == 'VIP':
                    overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                    if 'PREMIUM' in self.created_roles:
                        overwrites[self.created_roles['PREMIUM']] = discord.PermissionOverwrite(view_channel=True)
                    if 'FOUNDER' in self.created_roles:
                        overwrites[self.created_roles['FOUNDER']] = discord.PermissionOverwrite(view_channel=True)
                
                elif cat_key == 'PRIVATE':
                    overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                
                category = await guild.create_category(name=cat_config['name'], overwrites=overwrites)
                print(f"✅ Catégorie créée: {cat_config['name']}")
            
            # Créer les channels
            for channel_config in cat_config.get('channels', []):
                channel_name = channel_config['name']
                existing = discord.utils.get(guild.text_channels, name=channel_name.replace('│', '-'))
                
                if existing:
                    continue
                
                try:
                    await guild.create_text_channel(
                        name=channel_name,
                        category=category,
                        topic=channel_config.get('topic', '')
                    )
                    print(f"✅ Channel créé: {channel_name}")
                except Exception as e:
                    print(f"❌ Erreur création channel {channel_name}: {e}")
    
    async def assign_role(self, member: discord.Member, plan: str):
        """Assigne le rôle selon le plan"""
        plan_config = PLANS.get(plan)
        if not plan_config or not plan_config.discord_role:
            return
        
        role_key = plan_config.discord_role
        if role_key not in self.created_roles:
            return
        
        role = self.created_roles[role_key]
        
        try:
            await member.add_roles(role)
            print(f"✅ Rôle {role.name} assigné à {member.name}")
        except Exception as e:
            print(f"❌ Erreur assignation rôle: {e}")
    
    async def on_member_join(self, member: discord.Member):
        """Nouveau membre"""
        # Créer en base
        self.db.get_or_create_user(
            member.id,
            member.name,
            discriminator=str(member.discriminator) if hasattr(member, 'discriminator') else None,
            avatar_url=str(member.avatar.url) if member.avatar else None
        )
        
        # Assigner rôle USER
        if 'USER' in self.created_roles:
            await member.add_roles(self.created_roles['USER'])
        
        # DM de bienvenue
        try:
            embed = discord.Embed(
                title="🎉 Bienvenue sur Shellia AI !",
                description=f"Bonjour {member.name} !\n\n"
                           f"Je suis **Shellia**, votre assistante IA.\n\n"
                           f"**🚀 Pour commencer :**\n"
                           f"• Envoyez un message dans #💬│général\n"
                           f"• Utilisez `/help` pour les commandes\n"
                           f"• Utilisez `/trial` pour 3 jours Pro gratuits !",
                color=discord.Color.blue()
            )
            await member.send(embed=embed)
        except:
            pass
    
    async def on_message(self, message: discord.Message):
        """Message reçu"""
        if message.author == self.user:
            return
        
        if isinstance(message.channel, discord.DMChannel):
            await self.handle_dm(message)
            return
        
        if message.content.startswith(self.command_prefix):
            await self.process_commands(message)
            return
        
        # Vérifier channel autorisé
        allowed = ['💬│général', '🤖│chat-ia', 'test-bot', 'general']
        if message.channel.name not in allowed:
            if not message.channel.name.startswith(('🚀│bureau', '👑│suite')):
                return
        
        await self.handle_ai_message(message)
    
    async def handle_dm(self, message: discord.Message):
        """Gère les DM"""
        if message.content.startswith(self.command_prefix):
            await self.process_commands(message)
            return
        await self.handle_ai_message(message)
    
    async def handle_ai_message(self, message: discord.Message):
        """Traite un message IA"""
        user_id = message.author.id
        content = message.content
        
        # Vérifier sécurité
        is_admin = message.author.guild_permissions.administrator if hasattr(message.author, 'guild_permissions') else False
        can_proceed, error = await self.security.check_user(user_id, content, is_admin)
        
        if not can_proceed:
            await message.reply(error, delete_after=10)
            return
        
        # Récupérer utilisateur
        user_data = self.db.get_or_create_user(user_id, str(message.author))
        user_plan = user_data['plan']
        plan_config = PLANS.get(user_plan, PLANS['free'])
        
        # Vérifier quota
        quota = self.db.get_daily_quota(user_id)
        quota_limit = quota['messages_limit'] + quota.get('streak_bonus', 0)
        
        if quota['messages_used'] >= quota_limit and not is_admin:
            embed = self._quota_exhausted_embed(user_plan, plan_config)
            await message.reply(embed=embed)
            return
        
        # Mettre à jour streak
        streak_info = self.db.update_streak(user_id)
        if streak_info['is_new_milestone']:
            bonus = StreakConfig.BONUS.get(streak_info['current_streak'], 0)
            self.db.add_streak_bonus(user_id, bonus)
            
            embed = discord.Embed(
                title=f"{streak_info.get('badge', {}).get('emoji', '🔥')} Streak {streak_info['current_streak']} jours !",
                description=f"Bonus: +{bonus} messages aujourd'hui !",
                color=discord.Color.gold()
            )
            await message.reply(embed=embed, delete_after=30)
        
        # Générer réponse
        async with message.channel.typing():
            response = await self.ai.process_message(
                user_id=user_id,
                content=content,
                flash_ratio=plan_config.flash_ratio,
                pro_ratio=plan_config.pro_ratio
            )
        
        # Logger
        self.db.log_security_event(user_id, 'message_processed', {
            'model': response.model_used,
            'cost': response.cost_usd,
            'success': response.success
        })
        
        # Mettre à jour quota
        if response.success:
            self.db.increment_quota_usage(
                user_id=user_id,
                tokens=response.tokens_input + response.tokens_output,
                cost=response.cost_usd
            )
        
        # Envoyer réponse
        if response.success:
            if len(response.content) > 2000:
                for i in range(0, len(response.content), 1900):
                    await message.channel.send(response.content[i:i+1900])
            else:
                await message.reply(response.content)
        else:
            await message.reply(f"❌ {response.error or 'Erreur'}")
        
        # Notification 80%
        if not is_admin:
            new_quota = self.db.get_daily_quota(user_id)
            usage = new_quota['messages_used'] / quota_limit
            if 0.8 <= usage < 1.0:
                remaining = quota_limit - new_quota['messages_used']
                embed = self._quota_80_embed(user_plan, remaining)
                await message.reply(embed=embed, delete_after=60)
    
    def _quota_exhausted_embed(self, plan: str, plan_config) -> discord.Embed:
        """Embed quota épuisé"""
        embed = discord.Embed(
            title="❌ Quota épuisé",
            description=f"Vous avez utilisé vos **{plan_config.daily_quota} messages**.",
            color=discord.Color.red()
        )
        
        next_plans = {
            'free': ('Basic', 50),
            'basic': ('Pro', 150),
            'pro': ('Ultra', 400)
        }
        
        if plan in next_plans:
            name, quota = next_plans[plan]
            embed.add_field(
                name=f"💎 Passez au plan {name}",
                value=f"{quota} messages/jour avec `/upgrade {name.lower()}`",
                inline=False
            )
        
        return embed
    
    def _quota_80_embed(self, plan: str, remaining: int) -> discord.Embed:
        """Embed quota 80%"""
        next_plan = {'free': 'Basic', 'basic': 'Pro', 'pro': 'Ultra'}.get(plan, 'Ultra')
        
        return discord.Embed(
            title="⚠️ Plus que 20% de quota !",
            description=f"Il vous reste **{remaining} messages**.",
            color=discord.Color.orange()
        ).add_field(
            name=f"💎 Passez au plan {next_plan}",
            value=f"`/upgrade {next_plan.lower()}`",
            inline=False
        )
    
    @tasks.loop(hours=24)
    async def daily_reset(self):
        """Réinitialisation quotidienne"""
        print(f"🌙 Reset quotidien: {datetime.now()}")


# ============================================================================
# COMMANDES SLASH
# ============================================================================

bot = ShelliaBot()

@bot.tree.command(name="help", description="Affiche l'aide")
async def slash_help(interaction: discord.Interaction):
    """Aide"""
    embed = discord.Embed(
        title="🤖 Commandes Shellia AI",
        color=discord.Color.purple()
    )
    
    commands_text = """
    `/help` - Cette aide
    `/quota` - Votre quota
    `/plans` - Les plans disponibles
    `/stats` - Vos statistiques
    `/streak` - Votre streak
    `/badges` - Vos badges
    `/parrainage` - Code de parrainage
    `/top [period]` - Classement
    `/trial` - Essai 3j Pro
    """
    
    embed.add_field(name="Commandes", value=commands_text, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="quota", description="Affiche votre quota")
async def slash_quota(interaction: discord.Interaction):
    """Quota"""
    user_id = interaction.user.id
    user_data = bot.db.get_or_create_user(user_id, str(interaction.user))
    user_plan = user_data['plan']
    plan_config = PLANS.get(user_plan, PLANS['free'])
    
    quota = bot.db.get_daily_quota(user_id)
    streak_info = bot.db.get_streak_info(user_id)
    
    total_limit = quota['messages_limit'] + quota.get('streak_bonus', 0)
    remaining = total_limit - quota['messages_used']
    
    embed = discord.Embed(
        title=f"📊 Plan {plan_config.name}",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Quota", value=f"{quota['messages_used']}/{total_limit} ({remaining} restants)", inline=True)
    embed.add_field(name="Limite", value=f"{plan_config.daily_quota} msg/jour", inline=True)
    embed.add_field(name="Prix", value=f"€{plan_config.price_monthly}/mois" if plan_config.price_monthly else "Gratuit", inline=True)
    
    if streak_info['current_streak'] > 0:
        embed.add_field(name=f"🔥 Streak", value=f"{streak_info['current_streak']} jours", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="plans", description="Affiche les plans disponibles")
async def slash_plans(interaction: discord.Interaction):
    """Plans"""
    embed = discord.Embed(
        title="💎 Nos Plans",
        description="Choisissez votre plan",
        color=discord.Color.gold()
    )
    
    for plan_key, plan in PLANS.items():
        if plan_key == 'founder':
            continue
        
        value = f"📩 **{plan.daily_quota}** msg/jour • 💰 **€{plan.price_monthly}**/mois\n"
        if plan.has_private_channel:
            value += "🔒 Channel privé • "
        if plan.can_generate_images:
            value += f"🖼️ {plan.image_quota} images/jour"
        
        embed.add_field(name=f"🏷️ {plan.name}", value=value, inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="streak", description="Affiche votre streak")
async def slash_streak(interaction: discord.Interaction):
    """Streak"""
    streak_info = bot.db.get_streak_info(interaction.user.id)
    
    embed = discord.Embed(
        title=f"{streak_info.get('badge', {}).get('emoji', '🔥')} Votre Streak",
        color=discord.Color.orange()
    )
    
    embed.add_field(name="Actuel", value=f"**{streak_info['current_streak']}** jours", inline=True)
    embed.add_field(name="Record", value=f"**{streak_info['longest_streak']}** jours", inline=True)
    embed.add_field(name="Bonus", value=f"+**{streak_info['bonus_messages']}** msg", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="badges", description="Affiche vos badges")
async def slash_badges(interaction: discord.Interaction):
    """Badges"""
    badges = bot.db.get_user_badges(interaction.user.id)
    
    embed = discord.Embed(
        title="🏅 Vos Badges",
        color=discord.Color.gold()
    )
    
    if badges:
        badges_text = "\n".join([f"{b.get('name', '')}" for b in badges])
        embed.description = badges_text
    else:
        embed.description = "Aucun badge encore. Commencez à chatter !"
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="parrainage", description="Votre code de parrainage")
async def slash_parrainage(interaction: discord.Interaction):
    """Parrainage"""
    user_id = interaction.user.id
    
    code = bot.db.get_or_create_referral_code(user_id)
    stats = bot.db.get_referral_stats(user_id)
    
    embed = discord.Embed(
        title="🤝 Programme de Parrainage",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Votre code", value=f"`{code}`", inline=False)
    embed.add_field(name="Filleuls", value=f"{stats['completed_referrals']}/{stats['total_referrals']}", inline=True)
    embed.add_field(name="Jours gratuits", value=f"{stats['active_rewards_days']}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="top", description="Classement des utilisateurs")
@app_commands.describe(period="Période du classement")
@app_commands.choices(period=[
    app_commands.Choice(name="Aujourd'hui", value="day"),
    app_commands.Choice(name="Cette semaine", value="week"),
    app_commands.Choice(name="Ce mois", value="month"),
    app_commands.Choice(name="Tout", value="all")
])
async def slash_top(interaction: discord.Interaction, period: str = "week"):
    """Leaderboard"""
    top_users = bot.db.get_leaderboard(period, limit=10)
    
    period_names = {'day': "aujourd'hui", 'week': 'cette semaine', 'month': 'ce mois', 'all': 'depuis toujours'}
    
    embed = discord.Embed(
        title=f"🏆 Classement {period_names.get(period, '')}",
        color=discord.Color.purple()
    )
    
    if top_users:
        text = "\n".join([f"**#{u['rank']}** {u['username']} - {u['messages']:,} msg" for u in top_users])
        embed.description = text
    else:
        embed.description = "Aucune donnée"
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="trial", description="Active l'essai gratuit Pro (3 jours)")
async def slash_trial(interaction: discord.Interaction):
    """Trial gratuit"""
    user_id = interaction.user.id
    
    # Vérifier si déjà utilisé
    result = bot.db.client.table('user_trials').select('*').eq('user_id', user_id).execute()
    
    if result.data:
        trial = result.data[0]
        if trial.get('converted_to_paid'):
            await interaction.response.send_message("✅ Vous êtes déjà passé à un plan payant !", ephemeral=True)
        else:
            ends = datetime.fromisoformat(trial['trial_ends_at'].replace('Z', '+00:00'))
            days = (ends - datetime.now()).days
            await interaction.response.send_message(f"⏳ Essai actif, {days} jours restants", ephemeral=True)
        return
    
    # Créer trial
    now = datetime.now()
    ends = now + timedelta(days=3)
    
    bot.db.client.table('user_trials').insert({
        'user_id': user_id,
        'trial_started_at': now.isoformat(),
        'trial_ends_at': ends.isoformat(),
        'messages_used': 0
    }).execute()
    
    bot.db.update_user(user_id, plan='pro')
    
    # Assigner rôle
    if interaction.guild:
        member = interaction.guild.get_member(user_id)
        if member:
            await bot.assign_role(member, 'pro')
    
    embed = discord.Embed(
        title="🎉 Essai Pro activé !",
        description="3 jours avec toutes les fonctionnalités Pro !",
        color=discord.Color.green()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ============================================================================
# COMMANDES ADMIN
# ============================================================================

@bot.tree.command(name="setplan", description="Change le plan d'un utilisateur (Admin)")
@app_commands.describe(member="Membre", plan="Plan", duration="Durée en jours")
@app_commands.checks.has_permissions(administrator=True)
async def slash_setplan(interaction: discord.Interaction, member: discord.Member, plan: str, duration: int = 30):
    """Set plan admin"""
    if plan not in PLANS:
        await interaction.response.send_message("❌ Plan invalide", ephemeral=True)
        return
    
    bot.db.set_user_plan(member.id, plan, duration)
    await bot.assign_role(member, plan)
    
    await interaction.response.send_message(f"✅ {member.mention} → **{PLANS[plan].name}** ({duration} jours)")


@bot.tree.command(name="serverstats", description="Stats du serveur (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_serverstats(interaction: discord.Interaction):
    """Stats serveur"""
    stats = bot.db.get_server_stats()
    
    embed = discord.Embed(title="📊 Stats Serveur", color=discord.Color.red())
    embed.add_field(name="Users", value=stats['total_users'], inline=True)
    embed.add_field(name="Messages aujourd'hui", value=f"{stats['messages_today']:,}", inline=True)
    embed.add_field(name="Coût API", value=f"${stats['cost_today_usd']:.4f}", inline=True)
    
    plan_text = "\n".join([f"{p.upper()}: {c}" for p, c in stats['plan_distribution'].items()])
    embed.add_field(name="Plans", value=plan_text, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="ban", description="Bannit un utilisateur (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str, duration: int = None):
    """Ban admin"""
    bot.db.ban_user(member.id, reason, duration)
    
    try:
        await member.kick(reason=reason)
    except:
        pass
    
    await interaction.response.send_message(f"🚫 {member.mention} banni: {reason}")


# ============================================================================
# DÉMARRAGE
# ============================================================================

if __name__ == "__main__":
    if not all([EnvConfig.DISCORD_TOKEN, EnvConfig.SUPABASE_URL, EnvConfig.SUPABASE_KEY, EnvConfig.GEMINI_API_KEY]):
        print("❌ Variables d'environnement manquantes")
        exit(1)
    
    print("🚀 Démarrage Shellia AI Bot...")
    bot.run(EnvConfig.DISCORD_TOKEN)
