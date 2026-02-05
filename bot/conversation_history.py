"""
HISTORIQUE DE CONVERSATION PERSISTANT - Shellia AI Bot
Stockage persistant de l'historique des conversations
"""

import json
import zlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio


@dataclass
class Message:
    """Un message de la conversation"""
    role: str  # 'user' ou 'model'
    content: str
    timestamp: datetime
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


class ConversationHistoryManager:
    """
    Gestionnaire d'historique de conversation persistant
    Utilise Supabase avec compression optionnelle
    """
    
    def __init__(self, db, max_history: int = 50, compression_threshold: int = 10):
        self.db = db
        self.max_history = max_history
        self.compression_threshold = compression_threshold
        
        # Cache en mémoire pour les conversations actives
        self._cache: Dict[int, List[Message]] = {}
        self._cache_lock = asyncio.Lock()
    
    async def add_message(
        self,
        user_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Ajoute un message à l'historique"""
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Ajouter au cache
        async with self._cache_lock:
            if user_id not in self._cache:
                self._cache[user_id] = []
            self._cache[user_id].append(message)
            
            # Limiter la taille du cache
            if len(self._cache[user_id]) > self.max_history:
                self._cache[user_id] = self._cache[user_id][-self.max_history:]
        
        # Persister en base
        await self._persist_message(user_id, message)
    
    async def get_history(
        self,
        user_id: int,
        limit: int = 20,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """
        Récupère l'historique d'un utilisateur
        
        Args:
            user_id: ID Discord de l'utilisateur
            limit: Nombre maximum de messages
            since: Date de début (None = tout)
        """
        # Vérifier le cache d'abord
        async with self._cache_lock:
            if user_id in self._cache:
                cache = self._cache[user_id]
                if since:
                    cache = [m for m in cache if m.timestamp >= since]
                return cache[-limit:]
        
        # Charger depuis la base
        history = await self._load_history(user_id, limit, since)
        
        # Mettre en cache
        async with self._cache_lock:
            self._cache[user_id] = history
        
        return history
    
    async def get_conversation_context(
        self,
        user_id: int,
        max_tokens: int = 4000
    ) -> List[Dict]:
        """
        Récupère le contexte formaté pour Gemini
        
        Returns:
            Liste de dicts {'role': str, 'content': str}
        """
        history = await self.get_history(user_id, limit=self.max_history)
        
        context = []
        total_chars = 0
        
        for msg in reversed(history):
            msg_dict = {
                'role': msg.role,
                'content': msg.content
            }
            msg_chars = len(msg.content)
            
            # Estimation: ~4 chars/token
            if total_chars + msg_chars > max_tokens * 4:
                break
            
            context.insert(0, msg_dict)
            total_chars += msg_chars
        
        return context
    
    async def clear_history(self, user_id: int):
        """Efface l'historique d'un utilisateur"""
        async with self._cache_lock:
            if user_id in self._cache:
                del self._cache[user_id]
        
        # Supprimer de la base
        try:
            self.db.client.table('conversation_history')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
        except Exception as e:
            print(f"Erreur suppression historique: {e}")
    
    async def _persist_message(self, user_id: int, message: Message):
        """Persiste un message en base"""
        try:
            # Insérer le nouveau message
            self.db.client.table('conversation_history').insert({
                'user_id': user_id,
                'role': message.role,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'metadata': json.dumps(message.metadata) if message.metadata else None
            }).execute()
            
            # Supprimer les vieux messages si dépassement
            count_result = self.db.client.table('conversation_history')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            total = count_result.count
            if total > self.max_history:
                # Supprimer les plus anciens
                to_delete = total - self.max_history
                old_messages = self.db.client.table('conversation_history')\
                    .select('id')\
                    .eq('user_id', user_id)\
                    .order('timestamp', desc=False)\
                    .limit(to_delete)\
                    .execute()
                
                for msg in old_messages.data:
                    self.db.client.table('conversation_history')\
                        .delete()\
                        .eq('id', msg['id'])\
                        .execute()
            
        except Exception as e:
            print(f"Erreur persistance message: {e}")
    
    async def _load_history(
        self,
        user_id: int,
        limit: int,
        since: Optional[datetime]
    ) -> List[Message]:
        """Charge l'historique depuis la base"""
        try:
            query = self.db.client.table('conversation_history')\
                .select('role, content, timestamp, metadata')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=False)\
                .limit(limit)
            
            if since:
                query = query.gte('timestamp', since.isoformat())
            
            result = query.execute()
            
            messages = []
            for row in result.data:
                msg = Message(
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
                messages.append(msg)
            
            return messages
            
        except Exception as e:
            print(f"Erreur chargement historique: {e}")
            return []
    
    async def archive_old_conversations(self, days: int = 30):
        """Archive les conversations inactives depuis X jours"""
        cutoff = datetime.now() - timedelta(days=days)
        
        try:
            # Trouver les utilisateurs inactifs
            result = self.db.client.table('conversation_history')\
                .select('user_id, max(timestamp)')\
                .lt('timestamp', cutoff.isoformat())\
                .group('user_id')\
                .execute()
            
            archived_count = 0
            
            for row in result.data:
                user_id = row['user_id']
                
                # Compresser et archiver
                history = await self._load_history(user_id, limit=10000, since=None)
                
                if history:
                    compressed = self._compress_history(history)
                    
                    # Insérer dans archive
                    self.db.client.table('conversation_archive').insert({
                        'user_id': user_id,
                        'conversation_data': compressed,
                        'message_count': len(history),
                        'archived_at': datetime.now().isoformat(),
                        'date_from': history[0].timestamp.isoformat(),
                        'date_to': history[-1].timestamp.isoformat()
                    }).execute()
                    
                    # Supprimer l'original
                    await self.clear_history(user_id)
                    archived_count += 1
            
            print(f"{archived_count} conversations archivées")
            
        except Exception as e:
            print(f"Erreur archivage: {e}")
    
    def _compress_history(self, messages: List[Message]) -> str:
        """Compresse l'historique pour stockage"""
        data = json.dumps([m.to_dict() for m in messages])
        compressed = zlib.compress(data.encode('utf-8'), level=9)
        return base64.b64encode(compressed).decode('utf-8')
    
    def _decompress_history(self, compressed: str) -> List[Message]:
        """Décompresse l'historique"""
        import base64
        data = zlib.decompress(base64.b64decode(compressed))
        messages_data = json.loads(data.decode('utf-8'))
        return [Message.from_dict(m) for m in messages_data]
    
    async def restore_from_archive(self, user_id: int) -> List[Message]:
        """Restaure une conversation depuis l'archive"""
        try:
            result = self.db.client.table('conversation_archive')\
                .select('conversation_data')\
                .eq('user_id', user_id)\
                .order('archived_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                compressed = result.data[0]['conversation_data']
                messages = self._decompress_history(compressed)
                
                # Restaurer dans la table active
                for msg in messages:
                    await self._persist_message(user_id, msg)
                
                return messages
            
        except Exception as e:
            print(f"Erreur restauration: {e}")
        
        return []
    
    async def get_conversation_stats(self, user_id: int) -> Dict:
        """Stats de conversation pour un utilisateur"""
        try:
            result = self.db.client.table('conversation_history')\
                .select('role', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            total = result.count
            
            user_count = self.db.client.table('conversation_history')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .eq('role', 'user')\
                .execute().count
            
            model_count = total - user_count
            
            # Date du premier et dernier message
            first = self.db.client.table('conversation_history')\
                .select('timestamp')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=False)\
                .limit(1)\
                .execute()
            
            last = self.db.client.table('conversation_history')\
                .select('timestamp')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()
            
            return {
                'total_messages': total,
                'user_messages': user_count,
                'ai_responses': model_count,
                'first_message': first.data[0]['timestamp'] if first.data else None,
                'last_message': last.data[0]['timestamp'] if last.data else None
            }
            
        except Exception as e:
            print(f"Erreur stats: {e}")
            return {}


# SQL pour créer les tables
"""
-- Table principale
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'model')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    -- Compression: null si non compressé, sinon format de compression
    compression VARCHAR(10) DEFAULT NULL
);

CREATE INDEX idx_conversation_user ON conversation_history(user_id);
CREATE INDEX idx_conversation_timestamp ON conversation_history(timestamp);
CREATE INDEX idx_conversation_user_time ON conversation_history(user_id, timestamp DESC);

-- Table d'archive
CREATE TABLE IF NOT EXISTS conversation_archive (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    conversation_data TEXT NOT NULL,  -- JSON compressé
    message_count INTEGER NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    date_from TIMESTAMP WITH TIME ZONE,
    date_to TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_archive_user ON conversation_archive(user_id);
CREATE INDEX idx_archive_date ON conversation_archive(archived_at);

-- Fonction pour nettoyer les vieilles conversations
CREATE OR REPLACE FUNCTION cleanup_old_conversations(
    max_age_days INTEGER DEFAULT 90
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversation_history 
    WHERE timestamp < NOW() - INTERVAL '1 day' * max_age_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
"""
