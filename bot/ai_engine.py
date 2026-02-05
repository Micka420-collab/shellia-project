"""
MOTEUR IA - Shellia AI Bot
Gestion des modèles Gemini avec Smart Routing
"""

import re
import json
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

import google.generativeai as genai

from config import ModelConfig


@dataclass
class AIResponse:
    """Réponse de l'IA"""
    content: str
    model_used: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    success: bool
    error: Optional[str] = None


class AIManager:
    """Gestionnaire de modèles IA"""
    
    # Système prompt pour Shellia
    SYSTEM_PROMPT = """Tu es Shellia, une assistante IA amicale et utile pour un serveur Discord.

RÈGLES:
- Réponds de manière concise mais complète
- Utilise du markdown Discord (*italique*, **gras**, `code`)
- Sois chaleureuse mais professionnelle
- Si tu ne sais pas, dis-le honnêtement
- Limite tes réponses à 2000 caractères maximum
- Utilise des emojis appropriés occasionnellement

CONTEXTE:
- Tu es sur un serveur Discord communautaire
- Les utilisateurs ont des quotas de messages selon leur plan
- Tu dois être efficace pour optimiser les coûts API

STYLE:
- Amicale et accessible
- Utile et informative
- Pas trop formelle"""

    def __init__(self, api_key: str, db):
        self.db = db
        genai.configure(api_key=api_key)
        
        # Initialiser les modèles
        self.models = {
            ModelConfig.FLASH_LITE: genai.GenerativeModel(
                ModelConfig.FLASH_LITE,
                system_instruction=self.SYSTEM_PROMPT
            ),
            ModelConfig.FLASH: genai.GenerativeModel(
                ModelConfig.FLASH,
                system_instruction=self.SYSTEM_PROMPT
            ),
            ModelConfig.PRO: genai.GenerativeModel(
                ModelConfig.PRO,
                system_instruction=self.SYSTEM_PROMPT
            )
        }
        
        # Historique des conversations (en mémoire, limité)
        self.conversation_history: Dict[int, List[Dict]] = {}
        self.MAX_HISTORY = 10
    
    async def process_message(
        self,
        user_id: int,
        content: str,
        flash_ratio: float = 0.0,
        pro_ratio: float = 0.0
    ) -> AIResponse:
        """Traite un message avec Smart Routing"""
        
        # Sélectionner le modèle
        model_name = self._select_model(content, flash_ratio, pro_ratio)
        model = self.models[model_name]
        
        # Préparer le contexte
        context = self._get_context(user_id)
        
        try:
            # Générer la réponse
            chat = model.start_chat(history=context)
            response = await chat.send_message_async(content)
            
            # Extraire la réponse
            response_text = response.text
            
            # Estimer les tokens (approximation)
            tokens_in = len(content) // 4
            tokens_out = len(response_text) // 4
            
            # Calculer le coût
            costs = ModelConfig.COSTS[model_name]
            cost_usd = (tokens_in / 1000000 * costs['input']) + (tokens_out / 1000000 * costs['output'])
            
            # Mettre à jour l'historique
            self._update_history(user_id, content, response_text)
            
            return AIResponse(
                content=response_text,
                model_used=model_name,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cost_usd=cost_usd,
                success=True
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model_used=model_name,
                tokens_input=0,
                tokens_output=0,
                cost_usd=0.0,
                success=False,
                error=str(e)
            )
    
    def _select_model(self, content: str, flash_ratio: float, pro_ratio: float) -> str:
        """Sélectionne le meilleur modèle selon la complexité"""
        
        # Complexité du message
        complexity = self._analyze_complexity(content)
        
        # Random pour distribution
        import random
        rand = random.random()
        
        # Pro pour messages très complexes
        if complexity > 0.8 and pro_ratio > 0:
            if rand < pro_ratio:
                return ModelConfig.PRO
        
        # Flash pour messages moyennement complexes
        if complexity > 0.4 and flash_ratio > 0:
            if rand < flash_ratio:
                return ModelConfig.FLASH
        
        # Par défaut: Flash-Lite (le moins cher)
        return ModelConfig.FLASH_LITE
    
    def _analyze_complexity(self, content: str) -> float:
        """Analyse la complexité d'un message (0-1)"""
        score = 0.0
        
        # Longueur
        if len(content) > 500:
            score += 0.2
        if len(content) > 1000:
            score += 0.1
        
        # Code
        if '```' in content or '`' in content:
            score += 0.2
        
        # Questions complexes
        complex_indicators = [
            'explique', 'détaille', 'analyse', 'compare', 'différence',
            'pourquoi', 'comment', 'optimise', 'améliore', 'résous',
            'code', 'programme', 'script', 'fonction', 'algorithme'
        ]
        for indicator in complex_indicators:
            if indicator in content.lower():
                score += 0.1
                break
        
        # Langues multiples
        if any(ord(c) > 127 for c in content):
            score += 0.1
        
        # Mathématiques
        if any(c in content for c in '+=*/^$%#'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_context(self, user_id: int) -> List[Dict]:
        """Récupère le contexte de conversation"""
        history = self.conversation_history.get(user_id, [])
        
        # Convertir au format Gemini
        context = []
        for msg in history[-self.MAX_HISTORY:]:
            context.append({
                'role': 'user',
                'parts': [msg['user']]
            })
            context.append({
                'role': 'model',
                'parts': [msg['assistant']]
            })
        
        return context
    
    def _update_history(self, user_id: int, user_msg: str, assistant_msg: str):
        """Met à jour l'historique"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            'user': user_msg,
            'assistant': assistant_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limiter la taille
        if len(self.conversation_history[user_id]) > self.MAX_HISTORY:
            self.conversation_history[user_id] = self.conversation_history[user_id][-self.MAX_HISTORY:]
    
    def clear_history(self, user_id: int):
        """Efface l'historique d'un utilisateur"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
    
    async def generate_image(self, prompt: str) -> AIResponse:
        """Génère une image (si disponible)"""
        # Pour l'instant, retourner une erreur
        # Intégration avec DALL-E ou autre à ajouter
        return AIResponse(
            content="",
            model_used="image_gen",
            tokens_input=0,
            tokens_output=0,
            cost_usd=0.0,
            success=False,
            error="Génération d'images non configurée"
        )
