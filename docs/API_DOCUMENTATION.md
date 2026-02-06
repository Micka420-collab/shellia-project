# 📡 Documentation API - Shellia AI

Documentation complète de l'API Shellia AI pour les développeurs.

---

## Base URL

```
Production : https://api.shellia.ai/v1
Sandbox : https://sandbox-api.shellia.ai/v1
```

---

## Authentification

Toutes les requêtes nécessitent une clé API dans le header.

```http
Authorization: Bearer YOUR_API_KEY
```

### Obtenir une clé API

1. Connectez-vous sur https://shellia.ai
2. Dashboard > Paramètres > API
3. "Générer une clé"
4. Copiez et sécurisez la clé

---

## Points de terminaison

### 1. Utilisateur

#### GET /user/me

Récupère les informations de l'utilisateur authentifié.

**Réponse :**
```json
{
  "id": "123456789",
  "username": "JohnDoe",
  "avatar": "https://cdn.discordapp.com/...",
  "email": "john@example.com",
  "plan": "pro",
  "quota_daily": 50,
  "quota_daily_used": 12,
  "quota_purchased": 500,
  "quota_purchased_remaining": 340,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2026-02-04T08:15:00Z"
}
```

#### GET /user/quota

Récupère les informations de quota détaillées.

**Réponse :**
```json
{
  "daily": {
    "limit": 50,
    "used": 12,
    "remaining": 38,
    "resets_at": "2026-02-05T00:00:00Z"
  },
  "purchased": {
    "total": 500,
    "remaining": 340,
    "never_expires": true
  },
  "total_available": 378
}
```

---

### 2. Requêtes IA

#### POST /ask

Envoie une requête à l'IA.

**Body :**
```json
{
  "prompt": "Rédige une fiche produit",
  "context": {
    "product_name": "Casque Bluetooth",
    "price": 79.99,
    "target": "jeunes actifs"
  },
  "options": {
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

**Réponse :**
```json
{
  "id": "req_abc123",
  "response": "Découvrez notre casque Bluetooth premium...",
  "tokens_used": 245,
  "cost": 0.002,
  "quota_consumed": 1,
  "quota_source": "daily",
  "created_at": "2026-02-04T14:30:00Z"
}
```

#### GET /requests

Liste l'historique des requêtes.

**Query params :**
- `limit` : Nombre de résultats (max 100)
- `offset` : Pagination
- `from` : Date début (ISO 8601)
- `to` : Date fin (ISO 8601)

**Réponse :**
```json
{
  "data": [
    {
      "id": "req_abc123",
      "prompt": "Rédige une fiche produit",
      "response_preview": "Découvrez notre casque...",
      "tokens_used": 245,
      "created_at": "2026-02-04T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 145,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

### 3. Abonnements

#### GET /subscription

Récupère l'abonnement actuel.

**Réponse :**
```json
{
  "plan": "pro",
  "status": "active",
  "price": 9.99,
  "currency": "EUR",
  "interval": "month",
  "current_period_start": "2026-01-15T10:30:00Z",
  "current_period_end": "2026-02-15T10:30:00Z",
  "cancel_at_period_end": false,
  "payment_method": {
    "type": "card",
    "last4": "4242",
    "brand": "visa"
  }
}
```

#### POST /subscription/upgrade

Change de plan.

**Body :**
```json
{
  "plan": "ultra",
  "proration": true
}
```

#### DELETE /subscription

Annule l'abonnement.

---

### 4. Quota (Achat)

#### GET /quota/pricing

Récupère les tarifs des quotas.

**Réponse :**
```json
{
  "tiers": [
    {
      "id": "starter",
      "name": "Starter",
      "amount": 100,
      "price": 2.99,
      "currency": "EUR"
    },
    {
      "id": "basic",
      "name": "Basic", 
      "amount": 500,
      "price": 9.99,
      "currency": "EUR"
    }
  ]
}
```

#### POST /quota/checkout

Crée une session de paiement pour acheter du quota.

**Body :**
```json
{
  "tier": "basic",
  "success_url": "https://yoursite.com/success",
  "cancel_url": "https://yoursite.com/cancel"
}
```

**Réponse :**
```json
{
  "session_id": "cs_live_...",
  "checkout_url": "https://checkout.stripe.com/..."
}
```

---

### 5. Support (Tickets)

#### POST /tickets

Crée un ticket support.

**Body :**
```json
{
  "subject": "Problème de connexion",
  "message": "Je ne peux plus me connecter depuis ce matin",
  "priority": "normal"
}
```

#### GET /tickets

Liste les tickets.

**Réponse :**
```json
{
  "data": [
    {
      "id": "tik_xyz789",
      "subject": "Problème de connexion",
      "status": "open",
      "priority": "normal",
      "created_at": "2026-02-04T10:00:00Z",
      "last_activity": "2026-02-04T10:30:00Z"
    }
  ]
}
```

---

### 6. Affiliation

#### GET /affiliate

Récupère les infos d'affiliation.

**Réponse :**
```json
{
  "code": "SHELLIA25",
  "tier": "gold",
  "commission_rate": 0.25,
  "total_referred": 12,
  "total_earnings": 234.50,
  "pending_earnings": 45.00,
  "available_for_payout": 189.50,
  "payout_threshold": 50.00
}
```

#### POST /affiliate/payout

Demande un paiement.

**Body :**
```json
{
  "method": "paypal",
  "paypal_email": "your@email.com"
}
```

---

## Codes d'erreur

| Code | Description | Solution |
|------|-------------|----------|
| 200 | Succès | - |
| 400 | Requête invalide | Vérifiez le body |
| 401 | Non authentifié | Vérifiez votre clé API |
| 403 | Forbidden | Plan insuffisant |
| 404 | Ressource non trouvée | Vérifiez l'ID |
| 429 | Trop de requêtes | Attendez et réessayez |
| 500 | Erreur serveur | Contactez le support |

### Format d'erreur

```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "retry_after": 60
  }
}
```

---

## Rate Limiting

- **Standard** : 60 requêtes/minute
- **Pro** : 120 requêtes/minute
- **Ultra** : 300 requêtes/minute
- **Founder** : Illimité

Headers retournés :
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1643980800
```

---

## Webhooks

Configurez des webhooks pour recevoir des événements en temps réel.

### Événements disponibles

- `subscription.created`
- `subscription.cancelled`
- `payment.succeeded`
- `payment.failed`
- `quota.purchased`
- `user.created`

### Format du webhook

```json
{
  "event": "subscription.created",
  "timestamp": "2026-02-04T14:30:00Z",
  "data": {
    "user_id": "123456789",
    "plan": "pro",
    "amount": 9.99
  }
}
```

### Sécurité des webhooks

Vérifiez la signature dans le header :
```http
X-Webhook-Signature: sha256=abcdef123...
```

---

## SDKs officiels

### JavaScript/Node.js

```bash
npm install @shellia/sdk
```

```javascript
const Shellia = require('@shellia/sdk');

const client = new Shellia({ apiKey: 'your_key' });

const response = await client.ask({
  prompt: 'Bonjour Shellia !'
});
```

### Python

```bash
pip install shellia-sdk
```

```python
from shellia import Client

client = Client(api_key='your_key')

response = client.ask(prompt='Bonjour Shellia !')
```

---

## Support développeur

**Email :** api@shellia.ai  
**Documentation :** https://docs.shellia.ai/api  
**Discord (dev) :** https://discord.gg/shellia-dev  
**Changelog :** https://shellia.ai/api/changelog

---

**© 2026 Shellia AI - API v1.0**
