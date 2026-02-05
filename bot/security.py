"""
SÉCURITÉ - Shellia AI Bot
Gestion des rate limits, anti-spam et validation
"""

import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from config import SecurityConfig


class SecurityManager:
    """Gestionnaire de sécurité"""
    
    def __init__(self, db):
        self.db = db
        self.cooldowns: Dict[int, datetime] = {}
        self.message_history: Dict[int, List[datetime]] = defaultdict(list)
        self.spam_tracking: Dict[int, List[str]] = defaultdict(list)
        self.warning_count: Dict[int, int] = defaultdict(int)
    
    async def check_user(self, user_id: int, content: str, is_admin: bool = False) -> Tuple[bool, str]:
        """Vérifie si l'utilisateur peut envoyer un message"""
        
        # Admins bypass tout
        if is_admin:
            return True, None
        
        # Vérifier bannissement
        is_banned, ban_reason = self.db.is_user_banned(user_id)
        if is_banned:
            return False, f"🚫 Vous êtes banni: {ban_reason or 'Violation des règles'}"
        
        # Vérifier cooldown
        can_proceed, error = self._check_cooldown(user_id)
        if not can_proceed:
            return False, error
        
        # Vérifier rate limit
        can_proceed, error = self._check_rate_limit(user_id)
        if not can_proceed:
            return False, error
        
        # Vérifier spam
        can_proceed, error = self._check_spam(user_id, content)
        if not can_proceed:
            return False, error
        
        # Vérifier contenu
        can_proceed, error = self._validate_content(content)
        if not can_proceed:
            return False, error
        
        return True, None
    
    def _check_cooldown(self, user_id: int) -> Tuple[bool, str]:
        """Vérifie le cooldown entre messages"""
        now = datetime.now()
        last_message = self.cooldowns.get(user_id)
        
        if last_message:
            elapsed = (now - last_message).total_seconds()
            if elapsed < SecurityConfig.COOLDOWN_SECONDS:
                remaining = SecurityConfig.COOLDOWN_SECONDS - elapsed
                return False, f"⏱️ Attendez {remaining:.1f}s avant le prochain message"
        
        self.cooldowns[user_id] = now
        return True, None
    
    def _check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """Vérifie le rate limit (messages/min et messages/hour)"""
        now = datetime.now()
        history = self.message_history[user_id]
        
        # Nettoyer l'historique ancien
        one_hour_ago = now - timedelta(hours=1)
        history = [t for t in history if t > one_hour_ago]
        self.message_history[user_id] = history
        
        # Vérifier limite horaire
        if len(history) >= SecurityConfig.MAX_MESSAGES_PER_HOUR:
            return False, f"⏱️ Limite horaire atteinte ({SecurityConfig.MAX_MESSAGES_PER_HOUR} msg/h)"
        
        # Vérifier limite minute
        one_minute_ago = now - timedelta(minutes=1)
        recent = [t for t in history if t > one_minute_ago]
        if len(recent) >= SecurityConfig.MAX_MESSAGES_PER_MINUTE:
            return False, f"⏱️ Trop rapide ! ({SecurityConfig.MAX_MESSAGES_PER_MINUTE} msg/min max)"
        
        history.append(now)
        return True, None
    
    def _check_spam(self, user_id: int, content: str) -> Tuple[bool, str]:
        """Détecte et gère le spam"""
        # Normaliser le contenu
        normalized = content.lower().strip()
        
        # Ajouter à l'historique
        self.spam_tracking[user_id].append(normalized)
        
        # Garder seulement les 10 derniers messages
        if len(self.spam_tracking[user_id]) > 10:
            self.spam_tracking[user_id] = self.spam_tracking[user_id][-10:]
        
        # Vérifier répétition
        recent = self.spam_tracking[user_id][-SecurityConfig.SPAM_THRESHOLD:]
        if len(recent) >= SecurityConfig.SPAM_THRESHOLD:
            # Vérifier si tous les messages sont identiques
            if len(set(recent)) == 1:
                self.warning_count[user_id] += 1
                
                if self.warning_count[user_id] >= SecurityConfig.AUTO_BAN_WARNINGS:
                    self.db.ban_user(user_id, "Spam automatique détecté", duration=1)
                    self.db.add_violation(user_id, "spam", "Messages répétés identiques", "ban_1d")
                    return False, "🚫 Spam détecté ! Bannissement 24h."
                
                return False, f"⚠️ Spam détecté ! Avertissement {self.warning_count[user_id]}/{SecurityConfig.AUTO_BAN_WARNINGS}"
        
        return True, None
    
    def _validate_content(self, content: str) -> Tuple[bool, str]:
        """Valide le contenu du message"""
        # Longueur maximale
        if len(content) > SecurityConfig.MAX_MESSAGE_LENGTH:
            return False, f"❌ Message trop long ({len(content)}/{SecurityConfig.MAX_MESSAGE_LENGTH} caractères)"
        
        # Vérifier contenu vide
        if not content.strip():
            return False, "❌ Message vide"
        
        # Vérifier caractères spéciaux excessifs (potentiellement malveillant)
        special_chars = sum(1 for c in content if ord(c) > 127)
        if special_chars > len(content) * 0.8:
            return False, "❌ Contenu non valide"
        
        # Patterns interdits (tentatives d'injection, etc.)
        forbidden_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+=',
            r'data:text/html',
            r'\.exe',
            r'\.bat',
            r'\.sh\s',
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, "❌ Contenu non autorisé"
        
        return True, None
    
    def reset_warnings(self, user_id: int):
        """Réinitialise les avertissements"""
        self.warning_count[user_id] = 0
        self.spam_tracking[user_id] = []


class ContentFilter:
    """Filtre de contenu"""
    
    # Mots à filtrer (modéré)
    FILTERED_WORDS = [
        'spam', 'arnaque', 'escroquerie', 'virus', 'malware',
    ]
    
    # Patterns de phishing
    PHISHING_PATTERNS = [
        r'free\s*nitro',
        r'free\s*discord',
        r'\$\$+.*\$\$+',
        r'click.*here.*win',
        r'gift.*discord',
    ]
    
    @classmethod
    def check_content(cls, content: str) -> Tuple[bool, str]:
        """Vérifie le contenu"""
        lower = content.lower()
        
        # Vérifier mots filtrés
        for word in cls.FILTERED_WORDS:
            if word in lower:
                return False, f"⚠️ Mot interdits détecté"
        
        # Vérifier phishing
        for pattern in cls.PHISHING_PATTERNS:
            if re.search(pattern, lower):
                return False, "🚫 Tentative de phishing détectée"
        
        return True, None
