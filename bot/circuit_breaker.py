"""
CIRCUIT BREAKER - Shellia AI Bot
Protection contre les cascades de défaillance pour les appels API
"""

import time
import asyncio
from enum import Enum
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import random


class CircuitState(Enum):
    """États du circuit breaker"""
    CLOSED = "closed"       # Fonctionnement normal
    OPEN = "open"          # Circuit ouvert - rejette les appels
    HALF_OPEN = "half_open" # Test de récupération


@dataclass
class CircuitBreakerConfig:
    """Configuration du circuit breaker"""
    failure_threshold: int = 5           # Nombre d'échecs avant ouverture
    success_threshold: int = 3           # Nombre de succès pour fermeture
    timeout_seconds: float = 60.0        # Temps avant tentative half-open
    half_open_max_calls: int = 3         # Max appels en half-open
    
    # Retry exponentiel
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    
    # Timeout des appels
    call_timeout: float = 30.0


@dataclass
class CircuitStats:
    """Statistiques du circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: list = field(default_factory=list)


class CircuitBreaker:
    """
    Circuit breaker pour protéger les appels API
    Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_calls = 0
        self._state_changed_at: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    @property
    def current_state(self) -> str:
        return self.state.value
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exécute une fonction protégée par le circuit breaker
        """
        async with self._lock:
            # Vérifier si on peut passer
            if not await self._can_execute():
                self.stats.rejected_calls += 1
                raise CircuitBreakerOpenError(
                    f"Circuit '{self.name}' is OPEN - too many failures"
                )
            
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
        
        # Exécuter avec retry
        return await self._execute_with_retry(func, *args, **kwargs)
    
    async def _can_execute(self) -> bool:
        """Vérifie si l'appel peut être exécuté selon l'état"""
        
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Vérifier si le timeout est écoulé
            if self._state_changed_at:
                elapsed = (datetime.now() - self._state_changed_at).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    await self._transition_to(CircuitState.HALF_OPEN)
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Limiter le nombre d'appels en half-open
            if self._half_open_calls >= self.config.half_open_max_calls:
                return False
            return True
        
        return False
    
    async def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Exécute avec retry exponentiel"""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Timeout sur l'appel
                result = await asyncio.wait_for(
                    self._execute_async(func, *args, **kwargs),
                    timeout=self.config.call_timeout
                )
                
                # Succès
                await self._on_success()
                return result
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Call timed out after {self.config.call_timeout}s")
                await self._on_failure()
                
            except Exception as e:
                last_error = e
                await self._on_failure()
            
            # Calculer le délai avant retry
            if attempt < self.config.max_retries:
                delay = self._calculate_backoff(attempt)
                await asyncio.sleep(delay)
        
        # Tous les retries ont échoué
        raise last_error
    
    async def _execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Exécute la fonction (sync ou async)"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Fonction synchrone - exécuter dans un thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calcule le délai avec jitter"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        # Ajouter du jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return delay + jitter
    
    async def _on_success(self):
        """Appelé lors d'un succès"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.successful_calls += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
    
    async def _on_failure(self):
        """Appelé lors d'un échec"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.failed_calls += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Retour en OPEN immédiatement
                await self._transition_to(CircuitState.OPEN)
            elif self.state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)
    
    async def _transition_to(self, new_state: CircuitState):
        """Transition vers un nouvel état"""
        if self.state == new_state:
            return
        
        old_state = self.state
        self.state = new_state
        self._state_changed_at = datetime.now()
        
        # Reset compteurs
        if new_state == CircuitState.CLOSED:
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self.stats.consecutive_successes = 0
        
        # Logger
        self.stats.state_changes.append({
            'from': old_state.value,
            'to': new_state.value,
            'at': self._state_changed_at.isoformat()
        })
        
        print(f"Circuit '{self.name}': {old_state.value} -> {new_state.value}")
        
        # Callback
        if self.on_state_change:
            try:
                if asyncio.iscoroutinefunction(self.on_state_change):
                    await self.on_state_change(self.name, old_state, new_state)
                else:
                    self.on_state_change(self.name, old_state, new_state)
            except Exception as e:
                print(f"Erreur callback circuit breaker: {e}")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        success_rate = 0
        if self.stats.total_calls > 0:
            success_rate = (self.stats.successful_calls / self.stats.total_calls) * 100
        
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': self.stats.total_calls,
            'successful': self.stats.successful_calls,
            'failed': self.stats.failed_calls,
            'rejected': self.stats.rejected_calls,
            'success_rate': f"{success_rate:.1f}%",
            'consecutive_failures': self.stats.consecutive_failures,
            'state_changed_at': self._state_changed_at.isoformat() if self._state_changed_at else None,
            'state_changes': self.stats.state_changes[-10:]  # 10 derniers changements
        }
    
    def reset(self):
        """Reset le circuit breaker"""
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_calls = 0
        self._state_changed_at = None


class CircuitBreakerOpenError(Exception):
    """Exception levée quand le circuit est ouvert"""
    pass


class CircuitBreakerRegistry:
    """Registre global des circuit breakers"""
    
    _breakers: Dict[str, CircuitBreaker] = {}
    
    @classmethod
    def get_or_create(
        cls,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        **kwargs
    ) -> CircuitBreaker:
        """Récupère ou crée un circuit breaker"""
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name, config, **kwargs)
        return cls._breakers[name]
    
    @classmethod
    def get(cls, name: str) -> Optional[CircuitBreaker]:
        """Récupère un circuit breaker existant"""
        return cls._breakers.get(name)
    
    @classmethod
    def get_all_stats(cls) -> Dict:
        """Statistiques de tous les circuits"""
        return {
            name: breaker.get_stats()
            for name, breaker in cls._breakers.items()
        }
    
    @classmethod
    def reset_all(cls):
        """Reset tous les circuit breakers"""
        for breaker in cls._breakers.values():
            breaker.reset()


# Décorateur pour faciliter l'utilisation
def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    **kwargs
):
    """
    Décorateur pour protéger une fonction avec un circuit breaker
    
    Usage:
        @circuit_breaker("gemini_api")
        async def call_gemini(prompt):
            return await gemini_client.generate(prompt)
    """
    breaker = CircuitBreakerRegistry.get_or_create(name, config, **kwargs)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============ UTILISATION DANS AI ENGINE ============

"""
Exemple d'intégration dans ai_engine.py:

from circuit_breaker import CircuitBreakerRegistry, CircuitBreakerConfig

class AIManager:
    def __init__(self, api_key, db):
        self.db = db
        
        # Configurer le circuit breaker pour Gemini
        self.gemini_breaker = CircuitBreakerRegistry.get_or_create(
            "gemini_api",
            config=CircuitBreakerConfig(
                failure_threshold=3,       # 3 échecs avant ouverture
                success_threshold=2,       # 2 succès pour fermeture
                timeout_seconds=60,        # Attendre 1 min avant retry
                max_retries=2,             # 2 retries avant échec
                base_delay=2.0,            # 2s de délai initial
                call_timeout=30.0          # 30s timeout par appel
            ),
            on_state_change=self._on_circuit_state_change
        )
        
        # Configurer le modèle
        genai.configure(api_key=api_key)
    
    def _on_circuit_state_change(self, name, old_state, new_state):
        # Notifier les admins si le circuit s'ouvre
        if new_state.name == "OPEN":
            print(f"🚨 ALERTE: Circuit Gemini OUVERT - arrêt temporaire")
    
    async def generate_response(self, prompt, user_id):
        try:
            return await self.gemini_breaker.call(
                self._call_gemini_api,
                prompt,
                user_id
            )
        except CircuitBreakerOpenError:
            # Circuit ouvert - retourner message d'erreur graceful
            return "Le service IA est temporairement indisponible. Réessayez dans quelques minutes. 🔄"
    
    def _call_gemini_api(self, prompt, user_id):
        # Appel API Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
"""
