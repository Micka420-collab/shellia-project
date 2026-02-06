# 🤝 SKILL: Système d'Affiliation

## Description
Gestion complète du programme d'affiliation avec tiers croissants, codes promo, commissions automatiques et paiements.

---

## 🏆 Système de Tiers

| Tier | Emoji | Conversions | Commission | Couleur |
|------|-------|-------------|------------|---------|
| **Bronze** | 🥉 | 0-9 | 15% | Marron |
| **Silver** | 🥈 | 10-49 | 20% | Argent |
| **Gold** | 🥇 | 50-99 | 25% | Or |
| **Platinum** | 💎 | 100-499 | 30% | Platine |
| **Diamond** | 👑 | 500+ | 35% | Diamant |

---

## 📡 API Endpoints

### Créer un Affilié
```http
POST http://localhost:8080/api/affiliates/create
Content-Type: application/json

{
  "user_id": 123456789,
  "username": "Alice",
  "custom_code": "ALICE20",  // Optionnel - auto-généré si vide
  "custom_commission": 20,   // Optionnel - override le tier
  "is_vip": false
}
```

**Réponse:**
```json
{
  "user_id": 123456789,
  "code": "ALICE20",
  "tier": "bronze",
  "commission_percent": 15,
  "referral_url": "https://shellia.ai/?ref=ALICE20"
}
```

### Tracker une Conversion
```http
POST http://localhost:8080/api/affiliates/track
Content-Type: application/json

{
  "code": "ALICE20",
  "customer_id": 987654321,
  "order_id": "ORD-2024-001",
  "amount": 99.99,
  "order_type": "subscription"
}
```

**Réponse:**
```json
{
  "conversion_id": "CONV001",
  "affiliate_id": 123456789,
  "commission": 15.00,
  "status": "pending",
  "validation_date": "2024-02-20T00:00:00Z"
}
```

### Dashboard Affilié
```http
GET http://localhost:8080/api/affiliates/{USER_ID}/dashboard

{
  "affiliate": {
    "user_id": 123456789,
    "code": "ALICE20",
    "tier": "gold",
    "commission_percent": 25
  },
  "stats": {
    "conversions": 67,
    "revenue_generated": 5340.50,
    "commission_earned": 1335.12,
    "commission_paid": 1000.00,
    "commission_pending": 335.12
  },
  "next_tier": {
    "name": "Platinum",
    "progress": 67,
    "needed": 33
  },
  "recent_conversions": [...]
}
```

### Créer une Demande de Paiement
```http
POST http://localhost:8080/api/affiliates/payouts/create

{
  "affiliate_id": 123456789,
  "amount": 335.12,
  "method": "paypal"
}
```

### Traiter un Paiement (Admin)
```http
POST http://localhost:8080/api/affiliates/payouts/{PAYOUT_ID}/process

{
  "transaction_id": "PAYPAL_123456",
  "notes": "Paiement Janvier 2024"
}
```

### Leaderboard
```http
GET http://localhost:8080/api/affiliates/leaderboard?limit=10

{
  "leaderboard": [
    {
      "rank": 1,
      "username": "Alice",
      "tier": "diamond",
      "revenue": 8940.00,
      "conversions": 567
    }
  ]
}
```

### Stats Globales
```http
GET http://localhost:8080/api/affiliates/stats

{
  "total_affiliates": 45,
  "active_affiliates": 38,
  "total_revenue": 45320.00,
  "total_commissions": 9064.00,
  "total_conversions": 892,
  "pending_payouts": 2340.00
}
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Nouvel affilié
```
Utilisateur: "Comment devenir affilié ?"

Shellia: "🤝 **Programme d'Affiliation Shellia**

Gagnez jusqu'à **35% de commission** sur chaque vente !

🎯 **Comment ça marche:**
1. Recevez votre code unique
2. Partagez avec votre audience  
3. Gagnez des commissions
4. Retirez vos gains (min. €50)

💰 **Commissions par Tier:**
🥉 Bronze (0-9): 15%
🥈 Silver (10-49): 20%
🥇 Gold (50-99): 25%
💎 Platinum (100-499): 30%
👑 Diamond (500+): 35%

[Bouton: Devenir Affilié 🚀]"
```

### Scénario 2: Dashboard affilié
```
Utilisateur: !affiliate

Shellia en DM:
"🥇 **Votre Dashboard Affilié**

Tier actuel: **Gold** (25%)

🎫 Votre Code: `ALICE20`
🔗 Votre Lien: https://shellia.ai/?ref=ALICE20

📊 **Stats:**
Conversions: 67
Revenue généré: €5,340.50

💰 **Commissions:**
Gagnées: €1,335.12
Payées: €1,000.00
En attente: €335.12 ✅ (retirable!)

🎯 **Prochain Tier: Platinum**
Progression: 67%
Encore 33 conversions !

[Bouton: Retirer €335.12 💸]"
```

### Scénario 3: Notification conversion
```
Shellia en DM à Alice:

"💰 **Nouvelle Conversion !**

Une nouvelle vente vient d'être réalisée avec votre code !

💵 Montant: €99.99
💸 Commission: €25.00 (25% - Gold)
⏳ Statut: En attente de validation (30j)

📊 Vos Stats:
• Conversions: 68 (+1)
• En attente: €360.12

Continuez comme ça ! 🚀"
```

### Scénario 4: Upgrade de tier
```
Shellia en DM:

"💎 **Félicitations ! Vous passez Platinum !**

Vous avez atteint **100 conversions** !

💰 Nouvelle Commission:
25% → **30%** (+5%)

🎁 Avantages Platinum:
• Badge exclusif 💎
• Support prioritaire
• Bonus mensuel
• Accès early aux nouveautés

Prochain objectif: Diamond (500 conv) 👑"
```

### Scénario 5: Rapport mensuel affiliation
```
Shellia: "📊 **Rapport Affiliation - Janvier 2024**

🏆 **Top Affiliés:**
🥇 @Alice - €2,340 revenue (Diamond)
🥈 @Bob - €1,890 revenue (Platinum)
🥉 @Charlie - €1,230 revenue (Gold)

📈 **Stats Globales:**
• 45 affiliés actifs
• €12,450 revenue généré
• €2,340 commissions payées
• 234 conversions

💡 **Insights:**
• Codes avec '2024' = +23% conversions
• Weekend = +40% performance
• Twitter = meilleur canal

🎉 Félicitations à tous !"
```

---

## 🔄 Cycle de Vie d'une Commission

```
1. CONVERSION
   ↓
   Client utilise code ALICE20
   Achète Pro Plan €99.99
   
2. PENDING (30 jours)
   ↓
   Commission calculée: €25.00
   Statut: En attente
   
3. VALIDATED (après 30j)
   ↓
   Période de remboursement passée
   Commission validée
   
4. AVAILABLE
   ↓
   Ajoutée au solde disponible
   Min. €50 pour retrait
   
5. PAYOUT REQUESTED
   ↓
   Affilié demande un paiement
   
6. PAID (admin traite)
   ↓
   Paiement effectué
   Notification envoyée
```

---

## 🎁 Récompenses Mensuelles

```python
MONTHLY_REWARDS = {
    1: {"prize": "€100 + Badge Or", "description": "Top affilié du mois"},
    2: {"prize": "€50 + Badge Argent", "description": "2ème place"},
    3: {"prize": "€25 + Badge Bronze", "description": "3ème place"},
    "top_10": {"prize": "Pro 1 mois offert", "description": "Top 10"}
}
```

---

## 🔗 Intégration Discord

### Commandes
```
!affiliate                    → Voir son dashboard
!affiliate join              → Devenir affilié
!affiliate stats [@user]     → Stats d'un affilié
!affiliate code              → Voir/Modifier son code
!affiliate payout            → Demander un paiement
!affiliate leaderboard       → Classement
!affiliate link              → Obtenir son lien

!admin_affiliate add @user [code] [commission]
!admin_affiliate remove @user
!admin_affiliate stats
!admin_affiliate payouts
!admin_affiliate process <payout_id>
```

### Exemples
```
!affiliate
!affiliate leaderboard
!affiliate payout 200

!admin_affiliate add @Alice ALICE20 20
!admin_affiliate process PAY001
```

---

## 📊 Analytics Avancés

### Métriques par Affilié
```python
AFFILIATE_METRICS = {
    "conversion_rate": "clicks → ventes",
    "avg_order_value": "panier moyen",
    "ltv": "lifetime value des clients",
    "churn": "taux de désabonnement référés",
    "best_channel": "meilleur canal (Twitter, YouTube, etc)",
    "peak_hours": "heures de conversion optimales"
}
```

### Rapport de Performance
```
Shellia: "📈 **Votre Performance - Détails**

🎯 **Conversion Funnel:**
Clics lien: 1,234
Visites site: 890 (72%)
Inscriptions: 234 (26%)
Achats: 67 (29% des inscrits)

💰 **Revenu par Produit:**
• Pro Monthly: €2,340 (45%)
• Pro Yearly: €1,890 (35%)
• Ultra: €890 (17%)
• Founder: €220 (3%)

📱 **Top Canaux:**
1. Twitter/X: 45%
2. YouTube: 30%
3. Discord: 15%
4. Autres: 10%

⏰ **Meilleurs Horaires:**
18h-21h = +40% conversions
Weekend = +25% conversions"
```

---

## ⚙️ Configuration

```yaml
affiliate_config:
  min_payout: 50  # €
  validation_days: 30
  cookie_days: 30
  auto_approve: true
  self_referral: false  # Interdit
  
  tiers:
    bronze: {conversions: 0, commission: 15}
    silver: {conversions: 10, commission: 20}
    gold: {conversions: 50, commission: 25}
    platinum: {conversions: 100, commission: 30}
    diamond: {conversions: 500, commission: 35}
  
  payout_methods:
    - paypal
    - bank_transfer
    - crypto
```
