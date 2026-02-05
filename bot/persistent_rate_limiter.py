"""
RATE LIMITER PERSISTANT - Shellia AI Bot
Rate limiting distribué avec Redis ou fallback Supabase
"""

import time
from typing import Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class RateLimitStatus:
    """Status du rate limit pour un utilisateur"""
    can_proceed: bool
    remaining_minute: int
    remaining_hour: int
    reset_time: datetime
    cooldown_remaining: float
    reason: Optional[str] = None


class PersistentRateLimiter:
    """
    Rate limiter persistant qui utilise Redis si disponible,
    sinon fallback sur Supabase
    """
    
    def __init__(self, db, redis_client=None):
        self.db = db
        self.redis = redis_client
        
        # Configuration
        self.COOLDOWN_SECONDS = 3
        self.MAX_PER_MINUTE = 10
        self.MAX_PER_HOUR = 100
        self.SPAM_THRESHOLD = 5
        
        # Cache local pour réduire les requêtes DB
        self._local_cache: dict = {}
        self._cache_ttl = 5  # 5 secondes
    
    def _get_cache_key(self, user_id: int, key_type: str) -> str:
        """Génère une clé de cache"""
        return f"rate_limit:{user_id}:{key_type}"
    
    def _get_from_cache(self, key: str) -> Optional[any]:
        """Récupère depuis le cache local"""
        if key in self._local_cache:
            value, timestamp = self._local_cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return value
            else:
                del self._local_cache[key]
        return None
    
    def _set_in_cache(self, key: str, value: any):
        """Stocke dans le cache local"""
        self._local_cache[key] = (value, time.time())
    
    def _get_redis_key(self, user_id: int, period: str) -> str:
        """Génère une clé Redis"""
        now = datetime.now()
        if period == 'minute':
            time_bucket = now.strftime('%Y%m%d%H%M')
        elif period == 'hour':
            time_bucket = now.strftime('%Y%m%d%H')
        else:
            time_bucket = now.strftime('%Y%m%d')
        return f"shellia:ratelimit:{user_id}:{period}:{time_bucket}"
    
    def _increment_counter_redis(self, key: str, expire_seconds: int) -> int:
        """Incrémente un compteur Redis avec expiration"""
        if not self.redis:
            return 0
        
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, expire_seconds)
        results = pipe.execute()
        return results[0]
    
    def _increment_counter_db(self, user_id: int, period: str) -> int:
        """Incrémente un compteur en base de données"""
        now = datetime.now()
        
        if period == 'minute':
            window_start = now.replace(second=0, microsecond=0)
            expires_at = window_start + timedelta(minutes=1)
        elif period == 'hour':
            window_start = now.replace(minute=0, second=0, microsecond=0)
            expires_at = window_start + timedelta(hours=1)
        else:
            window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            expires_at = window_start + timedelta(days=1)
        
        # Upsert atomique
        try:
            result = self.db.client.rpc('increment_rate_limit', {
                'p_user_id': user_id,
                'p_period': period,
                'p_window_start': window_start.isoformat(),
                'p_expires_at': expires_at.isoformat()
            }).execute()
            
            if result.data:
                return result.data[0]['count']
        except Exception as e:
            print(f"Erreur DB rate limit: {e}")
        
        return 0
    
    def _get_counters(self, user_id: int) -> Tuple[int, int]:
        """Récupère les compteurs (minute, hour)"""
        cache_key = self._get_cache_key(user_id, "counters")
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        minute_count = 0
        hour_count = 0
        
        if self.redis:
            # Redis
            minute_key = self._get_redis_key(user_id, 'minute')
            hour_key = self._get_redis_key(user_id, 'hour')
            
            minute_count = int(self.redis.get(minute_key) or 0)
            hour_count = int(self.redis.get(hour_key) or 0)
        else:
            # Supabase
            try:
                now = datetime.now()
                minute_start = now.replace(second=0, microsecond=0).isoformat()
                hour_start = now.replace(minute=0, second=0, microsecond=0).isoformat()
                
                result = self.db.client.table('rate_limits')\
                    .select('period, count')\
                    .eq('user_id', user_id)\
                    .gte('window_start', hour_start)\
                    .execute()
                
                for row in result.data:
                    if row['period'] == 'minute' and row['window_start'] == minute_start:
                        minute_count = row['count']
                    if row['period'] == 'hour':
                        hour_count = row['count']
            except Exception as e:
                print(f"Erreur lecture counters: {e}")
        
        result = (minute_count, hour_count)
        self._set_in_cache(cache_key, result)
        return result
    
    def _get_last_message_time(self, user_id: int) -> Optional[datetime]:
        """Récupère l'heure du dernier message"""
        cache_key = self._get_cache_key(user_id, "last_message")
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        last_time = None
        
        if self.redis:
            key = f"shellia:lastmsg:{user_id}"
            timestamp = self.redis.get(key)
            if timestamp:
                last_time = datetime.fromtimestamp(float(timestamp))
        else:
            # Récupérer depuis la DB
            try:
                result = self.db.client.table('users')\
                    .select('last_active_at')\
                    .eq('user_id', user_id)\
                    .execute()
                if result.data and result.data[0]['last_active_at']:
                    last_time = datetime.fromisoformat(result.data[0]['last_active_at'])
            except:
                pass
        
        if last_time:
            self._set_in_cache(cache_key, last_time)
        return last_time
    
    def _update_last_message_time(self, user_id: int):
        """Met à jour l'heure du dernier message"""
        now = datetime.now()
        cache_key = self._get_cache_key(user_id, "last_message")
        self._set_in_cache(cache_key, now)
        
        if self.redis:
            key = f"shellia:lastmsg:{user_id}"
            self.redis.setex(key, 3600, now.timestamp())
        
        # Mettre à jour aussi dans la DB
        try:
            self.db.client.table('users')\
                .update({'last_active_at': now.isoformat()})\
                .eq('user_id', user_id)\
                .execute()
        except:
            pass
    
    def check_rate_limit(self, user_id: int, is_admin: bool = False) -> RateLimitStatus:
        """
        Vérifie le rate limit pour un utilisateur
        """
        if is_admin:
            return RateLimitStatus(
                can_proceed=True,
                remaining_minute=self.MAX_PER_MINUTE,
                remaining_hour=self.MAX_PER_HOUR,
                reset_time=datetime.now() + timedelta(hours=1),
                cooldown_remaining=0
            )
        
        # Vérifier cooldown
        last_time = self._get_last_message_time(user_id)
        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < self.COOLDOWN_SECONDS:
                return RateLimitStatus(
                    can_proceed=False,
                    remaining_minute=0,
                    remaining_hour=0,
                    reset_time=last_time + timedelta(seconds=self.COOLDOWN_SECONDS),
                    cooldown_remaining=self.COOLDOWN_SECONDS - elapsed,
                    reason=f"Cooldown: attente {self.COOLDOWN_SECONDS - elapsed:.1f}s"
                )
        
        # Récupérer compteurs actuels
        minute_count, hour_count = self._get_counters(user_id)
        
        # Vérifier limites
        if hour_count >= self.MAX_PER_HOUR:
            return RateLimitStatus(
                can_proceed=False,
                remaining_minute=0,
                remaining_hour=0,
                reset_time=datetime.now().replace(minute=0, second=0) + timedelta(hours=1),
                cooldown_remaining=0,
                reason=f"Limite horaire atteinte ({self.MAX_PER_HOUR} msg/h)"
            )
        
        if minute_count >= self.MAX_PER_MINUTE:
            return RateLimitStatus(
                can_proceed=False,
                remaining_minute=0,
                remaining_hour=self.MAX_PER_HOUR - hour_count,
                reset_time=datetime.now().replace(second=0) + timedelta(minutes=1),
                cooldown_remaining=0,
                reason=f"Trop rapide ({self.MAX_PER_MINUTE} msg/min max)"
            )
        
        # OK - mettre à jour les compteurs
        self._increment_counters(user_id)
        self._update_last_message_time(user_id)
        
        return RateLimitStatus(
            can_proceed=True,
            remaining_minute=self.MAX_PER_MINUTE - minute_count - 1,
            remaining_hour=self.MAX_PER_HOUR - hour_count - 1,
            reset_time=datetime.now() + timedelta(hours=1),
            cooldown_remaining=0
        )
    
    def _increment_counters(self, user_id: int):
        """Incrémente les compteurs"""
        if self.redis:
            minute_key = self._get_redis_key(user_id, 'minute')
            hour_key = self._get_redis_key(user_id, 'hour')
            
            self._increment_counter_redis(minute_key, 60)
            self._increment_counter_redis(hour_key, 3600)
        else:
            self._increment_counter_db(user_id, 'minute')
            self._increment_counter_db(user_id, 'hour')
        
        # Invalider le cache
        cache_key = self._get_cache_key(user_id, "counters")
        if cache_key in self._local_cache:
            del self._local_cache[cache_key]
    
    def check_spam(self, user_id: int, content: str) -> Tuple[bool, Optional[str]]:
        """
        Détecte le spam par répétition
        """
        cache_key = self._get_cache_key(user_id, "spam_history")
        
        # Récupérer historique
        if self.redis:
            key = f"shellia:spam:{user_id}"
            history = self.redis.lrange(key, 0, -1)
            history = [h.decode() if isinstance(h, bytes) else h for h in history]
        else:
            history = self._get_from_cache(cache_key) or []
        
        # Normaliser
        normalized = content.lower().strip()[:100]  # Limiter pour comparaison
        
        # Ajouter à l'historique
        history.append(normalized)
        history = history[-self.SPAM_THRESHOLD:]
        
        # Mettre à jour
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.lpush(key, normalized)
            pipe.ltrim(key, 0, self.SPAM_THRESHOLD - 1)
            pipe.expire(key, 3600)
            pipe.execute()
        else:
            self._set_in_cache(cache_key, history)
        
        # Vérifier répétition
        if len(history) >= self.SPAM_THRESHOLD:
            if len(set(history)) == 1:
                return False, f"⚠️ Spam détecté! Message répété {self.SPAM_THRESHOLD}x"
        
        return True, None
    
    def reset_user_limits(self, user_id: int):
        """Reset les limites d'un utilisateur (après bannissement, etc.)"""
        if self.redis:
            patterns = [
                f"shellia:ratelimit:{user_id}:*",
                f"shellia:lastmsg:{user_id}",
                f"shellia:spam:{user_id}"
            ]
            for pattern in patterns:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
        
        # Vider le cache local
        for key in list(self._local_cache.keys()):
            if str(user_id) in key:
                del self._local_cache[key]


# SQL pour créer la table rate_limits (fallback si pas de Redis)
"""
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    period VARCHAR(20) NOT NULL, -- 'minute', 'hour', 'day'
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    count INTEGER DEFAULT 1,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, period, window_start)
);

CREATE INDEX idx_rate_limits_user ON rate_limits(user_id);
CREATE INDEX idx_rate_limits_expires ON rate_limits(expires_at);

-- Fonction pour incrémenter
CREATE OR REPLACE FUNCTION increment_rate_limit(
    p_user_id BIGINT,
    p_period VARCHAR,
    p_window_start TIMESTAMP,
    p_expires_at TIMESTAMP
) RETURNS TABLE(count INTEGER) AS $$
BEGIN
    INSERT INTO rate_limits (user_id, period, window_start, expires_at, count)
    VALUES (p_user_id, p_period, p_window_start, p_expires_at, 1)
    ON CONFLICT (user_id, period, window_start)
    DO UPDATE SET count = rate_limits.count + 1, expires_at = p_expires_at
    RETURNING rate_limits.count INTO count;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Nettoyage automatique des entrées expirées
DELETE FROM rate_limits WHERE expires_at < NOW() - INTERVAL '1 day';
"""
