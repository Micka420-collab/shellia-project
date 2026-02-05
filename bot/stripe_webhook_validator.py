"""
VALIDATEUR WEBHOOK STRIPE - Shellia AI Bot
Validation cryptographique des webhooks Stripe
"""

import json
import hmac
import hashlib
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebhookValidationResult:
    """Résultat de validation d'un webhook"""
    is_valid: bool
    event_type: Optional[str] = None
    event_id: Optional[str] = None
    error_message: Optional[str] = None
    payload: Optional[Dict] = None


class StripeWebhookValidator:
    """
    Valide les webhooks Stripe avec signature cryptographique
    """
    
    def __init__(self, webhook_secret: str):
        """
        Args:
            webhook_secret: Le secret du webhook (whsec_...)
        """
        self.webhook_secret = webhook_secret
        self.recent_events: set = set()  # Dédoublonnage
        self.max_event_age_seconds = 300  # 5 minutes max
    
    def validate_webhook(
        self,
        payload: bytes,
        signature_header: str,
        max_age_seconds: int = 300
    ) -> WebhookValidationResult:
        """
        Valide un webhook Stripe entrant
        
        Args:
            payload: Le corps brut de la requête (bytes)
            signature_header: La valeur du header 'Stripe-Signature'
            max_age_seconds: Âge maximum acceptable (défaut: 5 min)
        
        Returns:
            WebhookValidationResult avec is_valid=True si valide
        """
        try:
            # 1. Vérifier que le secret est configuré
            if not self.webhook_secret or not self.webhook_secret.startswith('whsec_'):
                return WebhookValidationResult(
                    is_valid=False,
                    error_message="Configuration webhook invalide"
                )
            
            # 2. Parser le header Stripe-Signature
            signature_data = self._parse_signature_header(signature_header)
            
            if not signature_data or 'v1' not in signature_data:
                return WebhookValidationResult(
                    is_valid=False,
                    error_message="Signature Stripe manquante ou invalide"
                )
            
            # 3. Vérifier le timestamp (anti-replay)
            timestamp = signature_data.get('t')
            if timestamp:
                try:
                    event_time = int(timestamp)
                    current_time = int(time.time())
                    age = current_time - event_time
                    
                    if age > max_age_seconds:
                        return WebhookValidationResult(
                            is_valid=False,
                            error_message=f"Webhook trop ancien ({age}s > {max_age_seconds}s)"
                        )
                    
                    if age < -60:  # Dans le futur de plus de 1 minute
                        return WebhookValidationResult(
                            is_valid=False,
                            error_message="Webhook avec timestamp futur"
                        )
                except ValueError:
                    return WebhookValidationResult(
                        is_valid=False,
                        error_message="Timestamp invalide"
                    )
            
            # 4. Vérifier la signature cryptographique
            expected_signature = self._compute_signature(payload, timestamp)
            provided_signature = signature_data['v1']
            
            if not self._secure_compare(expected_signature, provided_signature):
                return WebhookValidationResult(
                    is_valid=False,
                    error_message="Signature invalide - possible tentative de falsification"
                )
            
            # 5. Parser le payload JSON
            try:
                event = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError:
                return WebhookValidationResult(
                    is_valid=False,
                    error_message="Payload JSON invalide"
                )
            
            # 6. Vérifier que l'événement n'a pas déjà été traité (dédoublonnage)
            event_id = event.get('id')
            if event_id:
                if event_id in self.recent_events:
                    return WebhookValidationResult(
                        is_valid=False,
                        error_message="Événement déjà traité (duplicate)"
                    )
                self.recent_events.add(event_id)
                
                # Nettoyer les vieux events (garder seulement 1000 derniers)
                if len(self.recent_events) > 1000:
                    self.recent_events = set(list(self.recent_events)[-500:])
            
            # 7. Validation OK
            return WebhookValidationResult(
                is_valid=True,
                event_type=event.get('type'),
                event_id=event_id,
                payload=event
            )
            
        except Exception as e:
            return WebhookValidationResult(
                is_valid=False,
                error_message=f"Erreur validation: {str(e)}"
            )
    
    def _parse_signature_header(self, header: str) -> Optional[Dict[str, str]]:
        """
        Parse le header Stripe-Signature
        Format: t=1492774577,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd
        """
        result = {}
        try:
            parts = header.split(',')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    result[key.strip()] = value.strip()
            return result
        except Exception:
            return None
    
    def _compute_signature(self, payload: bytes, timestamp: Optional[str]) -> str:
        """
        Calcule la signature attendue
        Format: HMAC-SHA256(secret, timestamp.payload)
        """
        # Le secret Stripe est déjà en base64
        secret = self.webhook_secret.split('_', 1)[1] if '_' in self.webhook_secret else self.webhook_secret
        
        # Construire le signed payload
        if timestamp:
            signed_payload = f"{timestamp}.".encode('utf-8') + payload
        else:
            signed_payload = payload
        
        # Calculer HMAC-SHA256
        mac = hmac.new(
            secret.encode('utf-8'),
            signed_payload,
            hashlib.sha256
        )
        return mac.hexdigest()
    
    def _secure_compare(self, a: str, b: str) -> bool:
        """
        Comparaison sécurisée en temps constant pour éviter les attaques timing
        """
        if len(a) != len(b):
            return False
        return hmac.compare_digest(a.encode(), b.encode())


class StripeEventHandler:
    """
    Gestionnaire d'événements Stripe sécurisé
    """
    
    def __init__(self, db, validator: StripeWebhookValidator):
        self.db = db
        self.validator = validator
        self.handlers = {
            'checkout.session.completed': self._handle_checkout_completed,
            'invoice.payment_succeeded': self._handle_payment_succeeded,
            'invoice.payment_failed': self._handle_payment_failed,
            'customer.subscription.deleted': self._handle_subscription_cancelled,
            'customer.subscription.updated': self._handle_subscription_updated,
        }
    
    def process_webhook(
        self,
        payload: bytes,
        signature_header: str
    ) -> Tuple[bool, str]:
        """
        Traite un webhook Stripe
        
        Returns:
            (success: bool, message: str)
        """
        # Valider
        validation = self.validator.validate_webhook(payload, signature_header)
        
        if not validation.is_valid:
            # Logger la tentative invalide
            self._log_invalid_attempt(signature_header, validation.error_message)
            return False, validation.error_message
        
        # Traiter l'événement
        event_type = validation.event_type
        handler = self.handlers.get(event_type)
        
        if not handler:
            # Événement non géré mais valide
            return True, f"Événement {event_type} ignoré (pas de handler)"
        
        try:
            result = handler(validation.payload)
            self._log_event_processed(validation.event_id, event_type, result)
            return True, result
        except Exception as e:
            error_msg = f"Erreur traitement {event_type}: {str(e)}"
            self._log_event_error(validation.event_id, event_type, str(e))
            return False, error_msg
    
    def _handle_checkout_completed(self, event: Dict) -> str:
        """Gère checkout.session.completed"""
        session = event.get('data', {}).get('object', {})
        
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        plan = metadata.get('plan')
        
        if not user_id or not plan:
            return "Session sans user_id ou plan"
        
        # Mettre à jour l'utilisateur
        self.db.set_user_plan(int(user_id), plan, duration_days=30)
        
        # Logger le paiement
        self.db.client.table('payments').insert({
            'user_id': int(user_id),
            'stripe_payment_id': session.get('payment_intent'),
            'stripe_subscription_id': subscription_id,
            'plan': plan,
            'amount': session.get('amount_total', 0) / 100,  # Convertir centimes -> euros
            'currency': session.get('currency', 'eur').upper(),
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }).execute()
        
        return f"Paiement complété pour user {user_id}, plan {plan}"
    
    def _handle_payment_succeeded(self, event: Dict) -> str:
        """Gère invoice.payment_succeeded"""
        invoice = event.get('data', {}).get('object', {})
        subscription_id = invoice.get('subscription')
        
        # Trouver l'utilisateur par subscription_id
        result = self.db.client.table('payments')\
            .select('user_id, plan')\
            .eq('stripe_subscription_id', subscription_id)\
            .execute()
        
        if result.data:
            user_id = result.data[0]['user_id']
            plan = result.data[0]['plan']
            
            # Prolonger l'abonnement
            self.db.set_user_plan(user_id, plan, duration_days=30)
            
            return f"Renouvellement pour user {user_id}"
        
        return "Subscription non trouvée"
    
    def _handle_payment_failed(self, event: Dict) -> str:
        """Gère invoice.payment_failed"""
        invoice = event.get('data', {}).get('object', {})
        subscription_id = invoice.get('subscription')
        
        # Trouver l'utilisateur
        result = self.db.client.table('payments')\
            .select('user_id')\
            .eq('stripe_subscription_id', subscription_id)\
            .execute()
        
        if result.data:
            user_id = result.data[0]['user_id']
            
            # Notifier l'utilisateur (passer en plan free si échec persistant)
            # Ici on pourrait envoyer un DM Discord
            
            return f"Échec paiement notifié pour user {user_id}"
        
        return "Subscription non trouvée"
    
    def _handle_subscription_cancelled(self, event: Dict) -> str:
        """Gère customer.subscription.deleted"""
        subscription = event.get('data', {}).get('object', {})
        subscription_id = subscription.get('id')
        
        # Trouver et downgrader l'utilisateur
        result = self.db.client.table('payments')\
            .select('user_id')\
            .eq('stripe_subscription_id', subscription_id)\
            .execute()
        
        if result.data:
            user_id = result.data[0]['user_id']
            
            # Passer en plan free à la fin de la période
            self.db.set_user_plan(user_id, 'free', duration_days=0)
            
            return f"Subscription annulée pour user {user_id}"
        
        return "Subscription non trouvée"
    
    def _handle_subscription_updated(self, event: Dict) -> str:
        """Gère customer.subscription.updated"""
        subscription = event.get('data', {}).get('object', {})
        # Gérer changements de plan si nécessaire
        return "Subscription mise à jour"
    
    def _log_invalid_attempt(self, signature_header: str, error: str):
        """Log une tentative invalide"""
        try:
            # Tronquer le header pour la sécurité
            header_preview = signature_header[:50] + "..." if len(signature_header) > 50 else signature_header
            
            self.db.client.table('security_logs').insert({
                'user_id': 0,  # Système
                'event_type': 'stripe_webhook_invalid',
                'event_data': json.dumps({
                    'error': error,
                    'header_preview': header_preview,
                    'timestamp': datetime.now().isoformat()
                }),
                'timestamp': datetime.now().isoformat()
            }).execute()
        except:
            pass
    
    def _log_event_processed(self, event_id: str, event_type: str, result: str):
        """Log un événement traité"""
        try:
            self.db.client.table('webhook_logs').insert({
                'event_id': event_id,
                'event_type': event_type,
                'status': 'processed',
                'result': result,
                'processed_at': datetime.now().isoformat()
            }).execute()
        except:
            pass
    
    def _log_event_error(self, event_id: str, event_type: str, error: str):
        """Log une erreur de traitement"""
        try:
            self.db.client.table('webhook_logs').insert({
                'event_id': event_id,
                'event_type': event_type,
                'status': 'error',
                'error': error,
                'processed_at': datetime.now().isoformat()
            }).execute()
        except:
            pass


# SQL pour la table webhook_logs
"""
CREATE TABLE IF NOT EXISTS webhook_logs (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100),
    event_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'processed', 'error', 'ignored'
    result TEXT,
    error TEXT,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhook_logs_event ON webhook_logs(event_id);
CREATE INDEX idx_webhook_logs_type ON webhook_logs(event_type);
CREATE INDEX idx_webhook_logs_status ON webhook_logs(status);
"""
