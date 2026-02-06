# 🛍️ SKILL: E-commerce & Plans

## Description
Gestion de la boutique, des plans (Free/Pro/Ultra/Founder), du système de précommandes et des paiements Stripe.

---

## 💳 Plans Disponibles

| Plan | Prix | Features | Badge |
|------|------|----------|-------|
| **Free** | €0/mois | Fonctions de base | 🆓 |
| **Pro** | €9.99/mois | +Priorité, -Ads, Early access | ⭐ |
| **Ultra** | €19.99/mois | +Tout illimité, Support VIP | 💎 |
| **Founder** | €99 one-time | Lifetime Ultra + Exclusivités | 👑 |

### Comparaison Détaillée
```yaml
Free:
  - Commands limitées: 50/jour
  - Réponse: Standard
  - Support: Communauté
  
Pro:
  - Commands illimitées
  - Réponse prioritaire
  - Support ticket 24h
  - Accès bêta
  
Ultra:
  - Tout Pro
  - Support VIP 4h
  - Personnalisation avancée
  - API privée
  
Founder:
  - Ultra à vie
  - Channel exclusif
  - Vote roadmap
  - Merch offert
```

---

## 📡 API Endpoints

### Créer un Paiement (Stripe)
```http
POST http://localhost:8080/api/payments/create
Content-Type: application/json

{
  "user_id": 123456789,
  "plan": "pro",  // pro_monthly, pro_yearly, ultra_monthly, ultra_yearly, founder
  "success_url": "https://shellia.ai/success",
  "cancel_url": "https://shellia.ai/cancel"
}
```

**Réponse:**
```json
{
  "session_id": "cs_abc123",
  "checkout_url": "https://checkout.stripe.com/pay/cs_abc123",
  "expires_at": 1705766400
}
```

### Vérifier Statut Paiement
```http
GET http://localhost:8080/api/payments/{SESSION_ID}/status

{
  "status": "completed|pending|failed",
  "plan": "pro",
  "amount_paid": 999,  // cents
  "subscription_id": "sub_xyz789"
}
```

### Créer Précommande
```http
POST http://localhost:8080/api/preorders/create
Content-Type: application/json

{
  "user_id": 123456789,
  "tier": "early_bird",  // early_bird (-30%), founder (-20%), supporter (-10%), regular
  "product": "founder_plan",
  "quantity": 1
}
```

### Appliquer Code Promo
```http
POST http://localhost:8080/api/payments/apply-coupon

{
  "code": "SUMMER2024",
  "plan": "pro_yearly"
}

{
  "valid": true,
  "discount_percent": 20,
  "new_price": 9599,  // cents
  "expires_at": "2024-08-31"
}
```

### Historique Commandes
```http
GET http://localhost:8080/api/orders?user_id=123456789

{
  "orders": [
    {
      "id": "ORD001",
      "plan": "pro",
      "amount": 999,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## 🛒 Système de Précommandes

### Tiers de Réduction
```python
PREORDER_TIERS = {
    "early_bird": {
        "discount": 0.30,
        "limit": 50,  # Nombre de slots
        "description": "-30% pour les plus rapides !"
    },
    "founder": {
        "discount": 0.20,
        "limit": 100,
        "description": "-20% + Badge Founder"
    },
    "supporter": {
        "discount": 0.10,
        "limit": 200,
        "description": "-10% + Remerciement spécial"
    },
    "regular": {
        "discount": 0.00,
        "limit": None,
        "description": "Prix normal"
    }
}
```

### Progression Précommandes
```
Shellia: "🛒 **Précommandes Founder Plan**

Early Bird (-30%): ████████░░ 40/50 vendus ⚡
Founder (-20%): ████░░░░░░ 20/100 vendus
Supporter (-10%): ██░░░░░░░░ 15/200 vendus
Regular: Ouvert après épuisement

⏰ Fin Early Bird: Dans 3j 12h
💰 Prix actuel: €69.30 (au lieu de €99)

[Bouton: Précommander]"
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Upgrade suggéré
```
Utilisateur: "Shellia, pourquoi ma commande est lente ?"

Shellia: "Je vois que vous êtes sur le plan **Free**.
Votre limite est de 50 commandes/jour, et vous en êtes à 48.

💡 **Solution:** Passez **Pro** pour:
• Commandes illimitées
• Réponses 2x plus rapides
• Support prioritaire 24h

⭐ Offre: -20% sur le premier mois avec code START20

[Bouton: Voir les Plans]"
```

### Scénario 2: Précommande rappel
```
Shellia: "⏰ **Rappel Précommande**

@User, votre précommande Early Bird Founder Plan expire dans 24h !

✅ Votre slot: #42/50 est réservée
💰 À payer: €69.30 (au lieu de €99)
⏳ Expire: Demain 23:59

Après expiration, vous passerez automatiquement au tier Founder (-20%).

[Bouton: Compléter le Paiement]"
```

### Scénario 3: Confirmation achat
```
Shellia en DM:

"✅ **Paiement Confirmé !**

Merci pour votre achat @User !

📦 **Détails:**
Plan: Pro (Annuel)
Montant: €95.99 (20% économisé)
Facture: FAC-2024-001

🎁 Vos avantages sont actifs:
⭐ Badge Pro apparu
⚡ Priorité activée
🎫 Support 24h disponible

📅 Prochain renouvellement: 20 Jan 2025
💳 Gérer: https://shellia.ai/billing"
```

### Scénario 4: Renouvellement
```
Shellia: "📅 **Renouvellement dans 3 jours**

Votre abonnement Pro se renouvelle le 23 Janvier.
Montant: €9.99

💳 Carte finissant par 4242

Actions disponibles:
• Modifier méthode de paiement
• Passer à Ultra (€19.99)
• Passer à Annuel (-20%)
• Annuler (garder jusqu'à fin de période)

[Bouton: Gérer Abonnement]"
```

---

## 🎁 Upsells & Cross-sells

### Suggestions Shellia
```python
UPSELL_TRIGGERS = {
    "high_usage": {
        "message": "Vous utilisez 90%+ de votre quota quotidien...",
        "offer": "Upgrade Pro -20%"
    },
    "long_tenure": {
        "message": "6 mois avec nous ! Fidélité récompensée",
        "offer": "Ultra 1 mois offert pour test"
    },
    "support_heavy": {
        "message": "Vous ouvrez beaucoup de tickets...",
        "offer": "Ultra pour support prioritaire"
    }
}
```

---

## 📊 Analytics Commerce

### Rapport Mensuel
```
Shellia: "💰 **Rapport Financier - Janvier 2024**

📈 Revenue: €12,450 (+23% vs Déc)
👥 Nouveaux clients: 45
🔄 Renouvellements: 89% taux
💳 Panier moyen: €14.50

📊 Ventes par plan:
• Pro Mensuel: 45%
• Pro Annuel: 30%
• Ultra: 20%
• Founder: 5%

🎯 Conversion:
• Visites → Essai: 12%
• Essai → Payant: 35%
• Churn: 5% (excellent!)

💡 Opportunités:
• 234 users Free très actifs → cible upsell
• Weekend = +40% conversions"
```

---

## 🏷️ Codes Promo

### Gérer les Codes
```http
POST http://localhost:8080/api/coupons/create

{
  "code": "SUMMER2024",
  "discount_percent": 20,
  "max_uses": 100,
  "applicable_plans": ["pro", "ultra"],
  "valid_from": "2024-06-01",
  "valid_until": "2024-08-31"
}
```

### Types de Codes
```
WELCOME20    → -20% première commande
SUMMER2024   → -20% été
YEARLY30     → -30% si annuel
REFERRAL15   → -15% parrainage
BIRTHDAY     → 1 mois offert anniversaire
STAFF50      → -50% équipe (usage interne)
```

---

## 🔗 Intégration Discord

### Commandes
```
!shop                    → Afficher la boutique
!plans                   → Comparer les plans
!upgrade [plan]          → Initier upgrade
!preorder [tier]         → Précommander Founder
!coupon [code]           → Appliquer code promo
!billing                 → Gérer abonnement
!invoice [id]            → Télécharger facture
!referral                → Obtenir lien de parrainage
```

### Boutons
```python
await button_manager.create_button(
    type=ButtonType.SHOP_ACCESS,
    channel_id=shop_channel_id,
    style=ButtonStyle.SUCCESS,
    label="Voir la Boutique"
)

await button_manager.create_button(
    type=ButtonType.PLAN_UPGRADE,
    channel_id=general_channel_id,
    style=ButtonStyle.PREMIUM,
    label="⭐ Passer Pro"
)
```

---

## ⚡ Webhooks Stripe

```python
@app.route('/webhooks/stripe', methods=['POST'])
def handle_stripe_webhook():
    event = stripe.Webhook.construct_event(...)
    
    if event['type'] == 'checkout.session.completed':
        await activate_plan(user_id, plan)
        await notify_shellia(f"Nouveau client: {user_id}")
        
    elif event['type'] == 'invoice.payment_failed':
        await notify_user(user_id, "Problème de paiement")
        await Shellia.escalate_support(user_id)
        
    elif event['type'] == 'customer.subscription.deleted':
        await downgrade_to_free(user_id)
        await Shellia.winback_campaign(user_id)
```
