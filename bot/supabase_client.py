"""
CLIENT SUPABASE - Shellia AI Bot
"""

from supabase import create_client, Client
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from config import EnvConfig


class SupabaseDB:
    """Client Supabase pour le bot"""
    
    def __init__(self):
        self.client: Client = create_client(EnvConfig.SUPABASE_URL, EnvConfig.SUPABASE_KEY)
    
    # ============================================================================
    # UTILISATEURS
    # ============================================================================
    
    def get_or_create_user(self, user_id: int, username: str, **kwargs) -> Dict:
        """Récupère ou crée un utilisateur"""
        # Vérifier si existe
        result = self.client.table('users').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            return result.data[0]
        
        # Créer
        user_data = {
            'user_id': user_id,
            'username': username,
            'discriminator': kwargs.get('discriminator'),
            'avatar_url': kwargs.get('avatar_url'),
            'plan': 'free',
            'joined_at': datetime.now().isoformat(),
            'last_active_at': datetime.now().isoformat()
        }
        
        self.client.table('users').insert(user_data).execute()
        
        # Créer streak
        self.client.table('user_streaks').insert({
            'user_id': user_id,
            'current_streak': 0,
            'longest_streak': 0,
            'total_days_active': 0
        }).execute()
        
        return user_data
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Récupère un utilisateur"""
        result = self.client.table('users').select('*').eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Met à jour un utilisateur"""
        self.client.table('users').update(kwargs).eq('user_id', user_id).execute()
        return True
    
    def set_user_plan(self, user_id: int, plan: str, duration_days: int = 30) -> bool:
        """Change le plan d'un utilisateur"""
        now = datetime.now()
        expires = now + timedelta(days=duration_days)
        
        self.client.table('users').update({
            'plan': plan,
            'plan_started_at': now.isoformat(),
            'plan_expires_at': expires.isoformat()
        }).eq('user_id', user_id).execute()
        
        # Attribuer badge
        badge_id = f"{plan}_member"
        self.award_badge(user_id, badge_id)
        
        return True
    
    # ============================================================================
    # QUOTAS
    # ============================================================================
    
    def get_daily_quota(self, user_id: int, date: str = None) -> Dict:
        """Récupère le quota journalier"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        result = self.client.table('daily_quotas').select('*')\
            .eq('user_id', user_id).eq('date', date).execute()
        
        if result.data:
            return result.data[0]
        
        # Créer
        from config import PLANS
        user = self.get_user(user_id)
        plan_limit = PLANS.get(user['plan'], PLANS['free']).daily_quota if user else 10
        
        quota_data = {
            'user_id': user_id,
            'date': date,
            'messages_used': 0,
            'messages_limit': plan_limit,
            'tokens_used': 0,
            'cost_usd': 0.0,
            'streak_bonus': 0
        }
        
        self.client.table('daily_quotas').insert(quota_data).execute()
        return quota_data
    
    def increment_quota_usage(self, user_id: int, tokens: int = 0, cost: float = 0.0):
        """Incrémente l'utilisation"""
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Update quota
        self.client.rpc('increment_quota', {
            'p_user_id': user_id,
            'p_date': date,
            'p_tokens': tokens,
            'p_cost': cost
        }).execute()
        
        # Update user stats
        self.client.rpc('increment_user_stats', {
            'p_user_id': user_id,
            'p_tokens': tokens,
            'p_cost': cost
        }).execute()
    
    def add_streak_bonus(self, user_id: int, bonus: int):
        """Ajoute un bonus de streak"""
        date = datetime.now().strftime('%Y-%m-%d')
        
        self.client.rpc('add_streak_bonus', {
            'p_user_id': user_id,
            'p_date': date,
            'p_bonus': bonus
        }).execute()
    
    # ============================================================================
    # STREAKS
    # ============================================================================
    
    def update_streak(self, user_id: int) -> Dict:
        """Met à jour le streak"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        result = self.client.table('user_streaks').select('*').eq('user_id', user_id).execute()
        
        if not result.data:
            # Créer
            self.client.table('user_streaks').insert({
                'user_id': user_id,
                'current_streak': 1,
                'longest_streak': 1,
                'last_active_date': today,
                'total_days_active': 1
            }).execute()
            return {'current_streak': 1, 'longest_streak': 1, 'is_new_milestone': False}
        
        streak = result.data[0]
        last_date = streak.get('last_active_date')
        current = streak['current_streak']
        longest = streak['longest_streak']
        
        if last_date == today:
            return {'current_streak': current, 'longest_streak': longest, 'is_new_milestone': False}
        
        elif last_date == yesterday:
            current += 1
            if current > longest:
                longest = current
            
            self.client.table('user_streaks').update({
                'current_streak': current,
                'longest_streak': longest,
                'last_active_date': today,
                'total_days_active': streak['total_days_active'] + 1
            }).eq('user_id', user_id).execute()
            
            # Logger
            from config import StreakConfig
            bonus = StreakConfig.BONUS.get(min(current, 7), 50)
            self.client.table('streak_history').insert({
                'user_id': user_id,
                'date': today,
                'streak_count': current,
                'bonus_earned': bonus
            }).execute()
            
            is_milestone = current in StreakConfig.BADGES
        else:
            current = 1
            self.client.table('user_streaks').update({
                'current_streak': 1,
                'last_active_date': today,
                'total_days_active': streak['total_days_active'] + 1
            }).eq('user_id', user_id).execute()
            is_milestone = False
        
        return {
            'current_streak': current,
            'longest_streak': longest,
            'is_new_milestone': is_milestone
        }
    
    def get_streak_info(self, user_id: int) -> Dict:
        """Récupère les infos de streak"""
        result = self.client.table('user_streaks').select('*').eq('user_id', user_id).execute()
        
        if not result.data:
            return {'current_streak': 0, 'longest_streak': 0, 'total_days': 0, 'bonus_messages': 0}
        
        streak = result.data[0]
        current = streak['current_streak']
        
        from config import StreakConfig
        bonus = StreakConfig.BONUS.get(min(current, 7), 50) if current > 0 else 0
        
        badge = None
        for days, info in sorted(StreakConfig.BADGES.items(), reverse=True):
            if current >= days:
                badge = info
                break
        
        return {
            'current_streak': current,
            'longest_streak': streak['longest_streak'],
            'total_days': streak['total_days_active'],
            'bonus_messages': bonus,
            'badge': badge
        }
    
    # ============================================================================
    # BADGES
    # ============================================================================
    
    def award_badge(self, user_id: int, badge_id: str) -> bool:
        """Attribue un badge"""
        try:
            self.client.table('user_badges').insert({
                'user_id': user_id,
                'badge_id': badge_id,
                'earned_at': datetime.now().isoformat()
            }).execute()
            return True
        except:
            return False
    
    def get_user_badges(self, user_id: int) -> List[Dict]:
        """Récupère les badges"""
        result = self.client.table('user_badges').select('*').eq('user_id', user_id).execute()
        
        from config import BADGES
        badges = []
        for row in result.data:
            badge_info = BADGES.get(row['badge_id'], {})
            badges.append({
                'id': row['badge_id'],
                'earned_at': row['earned_at'],
                **badge_info
            })
        return badges
    
    # ============================================================================
    # PARRAINAGE
    # ============================================================================
    
    def get_or_create_referral_code(self, user_id: int) -> str:
        """Récupère ou crée un code de parrainage"""
        import hashlib
        
        result = self.client.table('referral_codes').select('code').eq('user_id', user_id).execute()
        
        if result.data:
            return result.data[0]['code']
        
        code = f"SHELL-{hashlib.md5(str(user_id).encode()).hexdigest()[:6].upper()}"
        
        self.client.table('referral_codes').insert({
            'user_id': user_id,
            'code': code,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return code
    
    def apply_referral_code(self, code: str, referred_id: int) -> tuple:
        """Applique un code de parrainage"""
        # Trouver le parrain
        result = self.client.table('referral_codes').select('user_id').eq('code', code.upper()).execute()
        
        if not result.data:
            return False, "Code invalide"
        
        referrer_id = result.data[0]['user_id']
        
        if referrer_id == referred_id:
            return False, "Vous ne pouvez pas vous parrainer"
        
        # Vérifier si déjà parrainé
        existing = self.client.table('referrals').select('*').eq('referred_id', referred_id).execute()
        if existing.data:
            return False, "Vous avez déjà utilisé un code"
        
        # Créer le parrainage
        self.client.table('referrals').insert({
            'referrer_id': referrer_id,
            'referred_id': referred_id,
            'code_used': code,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Récompense au filleul
        expires = (datetime.now() + timedelta(days=3)).isoformat()
        self.client.table('referral_rewards').insert({
            'user_id': referred_id,
            'reward_type': 'pro_days',
            'reward_value': 3,
            'expires_at': expires
        }).execute()
        
        return True, "Code appliqué ! 3 jours Pro gratuits"
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """Stats de parrainage"""
        code_result = self.client.table('referral_codes').select('*').eq('user_id', user_id).execute()
        code = code_result.data[0] if code_result.data else None
        
        total = self.client.table('referrals').select('*', count='exact').eq('referrer_id', user_id).execute()
        completed = self.client.table('referrals').select('*', count='exact')\
            .eq('referrer_id', user_id).eq('status', 'completed').execute()
        
        rewards = self.client.table('referral_rewards').select('*')\
            .eq('user_id', user_id).eq('used', False)\
            .gt('expires_at', datetime.now().isoformat()).execute()
        
        total_days = sum(r['reward_value'] for r in rewards.data) if rewards.data else 0
        
        return {
            'code': code['code'] if code else None,
            'total_referrals': total.count if hasattr(total, 'count') else len(total.data),
            'completed_referrals': completed.count if hasattr(completed, 'count') else len(completed.data),
            'active_rewards_days': total_days
        }
    
    # ============================================================================
    # LEADERBOARD
    # ============================================================================
    
    def get_leaderboard(self, period: str = 'week', limit: int = 10) -> List[Dict]:
        """Récupère le leaderboard"""
        if period == 'all':
            result = self.client.table('users').select('user_id, username, total_messages')\
                .order('total_messages', desc=True).limit(limit).execute()
            
            return [
                {'rank': i+1, 'user_id': r['user_id'], 'username': r['username'], 'messages': r['total_messages']}
                for i, r in enumerate(result.data)
            ]
        
        # Pour day/week/month, utiliser une fonction RPC
        result = self.client.rpc('get_leaderboard', {
            'period': period,
            'limit_count': limit
        }).execute()
        
        return result.data if result.data else []
    
    # ============================================================================
    # STATS SERVEUR
    # ============================================================================
    
    def get_server_stats(self) -> Dict:
        """Stats du serveur"""
        # Total users
        users = self.client.table('users').select('*', count='exact').execute()
        
        # Distribution des plans
        plans = self.client.table('users').select('plan').execute()
        plan_dist = {}
        for p in plans.data:
            plan_dist[p['plan']] = plan_dist.get(p['plan'], 0) + 1
        
        # Messages aujourd'hui
        today = datetime.now().strftime('%Y-%m-%d')
        daily = self.client.table('daily_quotas').select('messages_used, cost_usd').eq('date', today).execute()
        messages_today = sum(d['messages_used'] for d in daily.data) if daily.data else 0
        cost_today = sum(d['cost_usd'] for d in daily.data) if daily.data else 0
        
        return {
            'total_users': users.count if hasattr(users, 'count') else len(users.data),
            'plan_distribution': plan_dist,
            'messages_today': messages_today,
            'cost_today_usd': cost_today
        }
    
    # ============================================================================
    # SÉCURITÉ
    # ============================================================================
    
    def log_security_event(self, user_id: int, event_type: str, event_data: dict = None):
        """Log un événement de sécurité"""
        self.client.table('security_logs').insert({
            'user_id': user_id,
            'event_type': event_type,
            'event_data': json.dumps(event_data) if event_data else None,
            'timestamp': datetime.now().isoformat()
        }).execute()
    
    def add_violation(self, user_id: int, violation_type: str, description: str, action: str):
        """Ajoute une violation"""
        self.client.table('user_violations').insert({
            'user_id': user_id,
            'violation_type': violation_type,
            'description': description,
            'action_taken': action,
            'timestamp': datetime.now().isoformat()
        }).execute()
        
        # Incrémenter warnings
        self.client.rpc('increment_warnings', {'p_user_id': user_id}).execute()
    
    def ban_user(self, user_id: int, reason: str, duration_days: int = None):
        """Bannit un utilisateur"""
        expires = (datetime.now() + timedelta(days=duration_days)).isoformat() if duration_days else None
        
        self.client.table('users').update({
            'is_banned': True,
            'ban_reason': reason,
            'ban_expires_at': expires
        }).eq('user_id', user_id).execute()
    
    def is_user_banned(self, user_id: int) -> tuple:
        """Vérifie si banni"""
        result = self.client.table('users').select('is_banned, ban_reason, ban_expires_at')\
            .eq('user_id', user_id).execute()
        
        if not result.data:
            return False, None
        
        user = result.data[0]
        
        if not user.get('is_banned'):
            return False, None
        
        # Vérifier expiration
        if user.get('ban_expires_at'):
            expires = datetime.fromisoformat(user['ban_expires_at'].replace('Z', '+00:00'))
            if datetime.now() > expires:
                # Débannir
                self.client.table('users').update({
                    'is_banned': False,
                    'ban_reason': None,
                    'ban_expires_at': None
                }).eq('user_id', user_id).execute()
                return False, None
        
        return True, user.get('ban_reason')
