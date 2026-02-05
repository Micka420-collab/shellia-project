"""
STRIPE HANDLER - Shellia AI Bot
Gestion des paiements et webhooks Stripe
"""

import stripe
from datetime import datetime, timedelta
from typing import Dict, Optional

from config import EnvConfig, PLANS


class StripeHandler:
    """Gestionnaire de paiements Stripe"""
    
    def __init__(self, db):
        self.db = db
        stripe.api_key = EnvConfig.STRIPE_SECRET_KEY
        self.webhook_secret = EnvConfig.STRIPE_WEBHOOK_SECRET
        
        # Mapping plans -> Stripe Price IDs (à configurer)
        self.PRICE_IDS = {
            'basic': 'price_basic_monthly',
            'basic_yearly': 'price_basic_yearly',
            'pro': 'price_pro_monthly',
            'pro_yearly': 'price_pro_yearly',
            'ultra': 'price_ultra_monthly',
            'ultra_yearly': 'price_ultra_yearly',
            'founder': 'price_founder_monthly',
            'founder_yearly': 'price_founder_yearly',
        }
    
    def create_checkout_session(self, user_id: int, plan: str, yearly: bool = False) -> Dict:
        """Crée une session de paiement Stripe"""
        
        price_key = f"{plan}_yearly" if yearly else plan
        price_id = self.PRICE_IDS.get(price_key)
        
        if not price_id:
            return {'success': False, 'error': 'Plan invalide'}
        
        plan_config = PLANS.get(plan)
        if not plan_config:
            return {'success': False, 'error': 'Plan non trouvé'}
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'https://your-domain.com/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url='https://your-domain.com/cancel',
                metadata={
                    'user_id': str(user_id),
                    'plan': plan,
                    'yearly': str(yearly)
                }
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'url': session.url
            }
            
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Gère les webhooks Stripe"""
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError:
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError:
            return {'success': False, 'error': 'Invalid signature'}
        
        event_type = event['type']
        data = event['data']['object']
        
        handlers = {
            'checkout.session.completed': self._handle_checkout_completed,
            'invoice.payment_succeeded': self._handle_payment_succeeded,
            'invoice.payment_failed': self._handle_payment_failed,
            'customer.subscription.deleted': self._handle_subscription_deleted,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(data)
        
        return {'success': True, 'message': f'Event {event_type} ignored'}
    
    def _handle_checkout_completed(self, session: Dict) -> Dict:
        """Gère un paiement réussi"""
        
        user_id = int(session['metadata']['user_id'])
        plan = session['metadata']['plan']
        yearly = session['metadata'].get('yearly') == 'True'
        
        duration_days = 365 if yearly else 30
        
        # Mettre à jour l'utilisateur
        self.db.set_user_plan(user_id, plan, duration_days)
        
        # Logger le paiement
        self.db.client.table('payments').insert({
            'user_id': user_id,
            'stripe_payment_id': session['payment_intent'],
            'stripe_subscription_id': session['subscription'],
            'plan': plan,
            'amount': session['amount_total'] / 100,  # Convertir centimes -> euros
            'currency': session['currency'].upper(),
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }).execute()
        
        return {'success': True, 'message': f'Plan {plan} activated for user {user_id}'}
    
    def _handle_payment_succeeded(self, invoice: Dict) -> Dict:
        """Gère un paiement récurrent réussi"""
        
        subscription_id = invoice['subscription']
        
        # Trouver l'utilisateur par subscription
        result = self.db.client.table('payments')\
            .select('user_id, plan')\
            .eq('stripe_subscription_id', subscription_id)\
            .execute()
        
        if not result.data:
            return {'success': False, 'error': 'Subscription not found'}
        
        payment = result.data[0]
        user_id = payment['user_id']
        plan = payment['plan']
        
        # Prolonger le plan
        self.db.set_user_plan(user_id, plan, 30)
        
        return {'success': True, 'message': f'Plan renewed for user {user_id}'}
    
    def _handle_payment_failed(self, invoice: Dict) -> Dict:
        """Gère un échec de paiement"""
        
        subscription_id = invoice['subscription']
        
        # Logger l'échec
        self.db.client.table('payments').insert({
            'stripe_subscription_id': subscription_id,
            'status': 'failed',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return {'success': True, 'message': 'Payment failure logged'}
    
    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Gère la suppression d'un abonnement"""
        
        subscription_id = subscription['id']
        
        # Trouver l'utilisateur
        result = self.db.client.table('payments')\
            .select('user_id')\
            .eq('stripe_subscription_id', subscription_id)\
            .execute()
        
        if not result.data:
            return {'success': False, 'error': 'Subscription not found'}
        
        user_id = result.data[0]['user_id']
        
        # Downgrader vers free
        self.db.set_user_plan(user_id, 'free', 36500)  # "Permanent"
        
        return {'success': True, 'message': f'User {user_id} downgraded to free'}
    
    def cancel_subscription(self, user_id: int) -> Dict:
        """Annule l'abonnement d'un utilisateur"""
        
        # Trouver la subscription
        result = self.db.client.table('payments')\
            .select('stripe_subscription_id')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data or not result.data[0].get('stripe_subscription_id'):
            return {'success': False, 'error': 'No active subscription found'}
        
        subscription_id = result.data[0]['stripe_subscription_id']
        
        try:
            stripe.Subscription.delete(subscription_id)
            return {'success': True, 'message': 'Subscription cancelled'}
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
    
    def get_customer_portal(self, user_id: int) -> Dict:
        """Génère un lien vers le portail client Stripe"""
        
        # Trouver le customer_id (à stocker dans users)
        result = self.db.client.table('users')\
            .select('stripe_customer_id')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data or not result.data[0].get('stripe_customer_id'):
            return {'success': False, 'error': 'No customer found'}
        
        customer_id = result.data[0]['stripe_customer_id']
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url='https://your-domain.com/account'
            )
            
            return {'success': True, 'url': session.url}
        except stripe.error.StripeError as e:
            return {'success': False, 'error': str(e)}
