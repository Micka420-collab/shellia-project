# 📊 SKILL: Quota Manager

## Description
Gestion des quotas utilisateurs avec possibilité d'achat via Stripe. Système optimisé pour la rentabilité avec prix dégressifs à volume.

---

## 🎯 Quotas par Plan

| Plan | Quota Quotidien | Description |
|------|-----------------|-------------|
| **Free** | 50 requêtes/jour | Gratuit, limité |
| **Pro** | 1,000 requêtes/jour | Illimité pour usage normal |
| **Ultra** | 5,000 requêtes/jour | Usage intensif |
| **Founder** | 10,000 requêtes/jour | Usage professionnel |

---

## 💰 Packages d'Achat (Optimisés Rentabilité)

| Package | Requêtes | Prix | Économie | Coût/req |
|---------|----------|------|----------|----------|
| **Starter** | 100 | €2.99 | - | €0.0299 |
| **Regular** | 500 | €9.99 | - | €0.0200 |
| **Plus** ⭐ | 1,000 | €14.99 | Référence | €0.0150 |
| **Business** | 5,000 | €49.99 | -17% | €0.0100 |
| **Enterprise** | 10,000 | €89.99 | -40% | €0.0090 |
| **Mega** | 50,000 | €349.99 | -53% | €0.0070 |

**💡 Stratégie:** Les packages à volume incitent à l'achat bulk tout en maintenant de bonnes marges.

---

## 📡 API Endpoints

### Voir son Quota
```http
GET http://localhost:8080/api/quota/{USER_ID}

{
  "daily_limit": 1000,
  "daily_used": 450,
  "daily_remaining": 550,
  "purchased_quota": 5000,
  "purchased_used": 1200,
  "purchased_remaining": 3800,
  "total_remaining": 4350,
  "reset_at": "2024-01-21T00:00:00Z"
}
```

### Créer Session d'Achat
```http
POST http://localhost:8080/api/quota/checkout

{
  "user_id": 123456789,
  "package_id": "quota_1000"
}

{
  "session_id": "cs_abc123",
  "checkout_url": "https://checkout.stripe.com/...",
  "amount": 1000,
  "price": "€14.99"
}
```

### Webhook Stripe (Success)
```http
POST http://localhost:8080/webhooks/stripe

{
  "type": "checkout.session.completed",
  "session": {
    "metadata": {
      "type": "quota_purchase",
      "user_id": "123456789",
      "quota_amount": "1000"
    }
  }
}
```

---

## 🔄 Ordre de Consommation

```
1. Quota QUOTIDIEN (reset chaque jour)
   ↓ (si épuisé)
2. Quota ACHETÉ (jamais expire)
   ↓ (si épuisé)
3. BLOQUÉ - Demander upgrade ou acheter
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Quota faible
```
Utilisateur: "Pourquoi ça ne marche plus ?"

Shellia: "📊 **Quota Presque Épuisé !**

Vous avez utilisé **95%** de votre quota quotidien.
• Utilisé: 950 / 1,000 requêtes
• Reset: Dans 3h 24min

**Solutions:**
1. ⏰ Attendre le reset (00h00)
2. 💎 Upgrader vers Ultra (5,000 req/jour)
3. 📊 Acheter du quota (n'expire jamais)

[Bouton: Voir les Options 💰]"
```

### Scénario 2: Achat de quota
```
Utilisateur: !buy_quota

Shellia: "💎 **Acheter du Quota Supplémentaire**

Ajoutez des requêtes à votre compte.
**Le quota acheté n'expire jamais !**

🔥 **Plus Populaire:** 1,000 req - €14.99

💰 Autres Options:
• Starter: 100 req - €2.99
• Regular: 500 req - €9.99
• Business: 5,000 req - €49.99 (-17%)
• Enterprise: 10,000 req - €89.99 (-40%)

[Boutons: Choisir un Package]"
```

### Scénario 3: Confirmation achat
```
Shellia en DM:

"✅ **Quota Ajouté !**

**+1,000 requêtes** ont été ajoutées à votre compte.

📊 **Nouveau Solde:**
• Quota acheté: 5,000 → 6,000
• Disponible: 6,380 requêtes

💡 Ce quota n'expire jamais.
Utilisez-le quand vous en avez besoin !"
```

### Scénario 4: Dashboard quota
```
Utilisateur: !quota

Shellia:
"📊 **Votre Quota**

📅 **Quotidien:**  ████████░░ 800/1000
Reset: <t:timestamp:R>

💎 **Acheté:**     ███░░░░░░░ 1,200/5,000
Jamais expire ✓

📈 **Total dispo:** 4,800 requêtes

💰 Besoin de plus ? `/buy_quota`"
```

---

## 🎯 Stratégie de Rentabilité

```python
# Marges par package
PACKAGES_MARGIN = {
    "starter": {"margin": 0.75},      # 75% marge (volume faible)
    "regular": {"margin": 0.70},      # 70% marge
    "plus": {"margin": 0.65},         # 65% marge (populaire)
    "business": {"margin": 0.60},     # 60% marge (volume)
    "enterprise": {"margin": 0.55},   # 55% marge (bulk)
    "mega": {"margin": 0.50}          # 50% marge (wholesale)
}
```

---

## 🔗 Intégration Discord

### Commandes
```
!quota              → Voir son quota actuel
!buy_quota          → Achat de quota
!quota_history      → Historique des achats
```

### Commandes Admin
```
!admin_quota add @user <amount>
!admin_quota remove @user <amount>
!admin_quota stats
```

---

## 📊 Analytics

### KPIs à suivre
- **Taux de conversion** (view → achat)
- **Panier moyen** par utilisateur
- **Package le plus vendu**
- **Lifetime value** des acheteurs de quota
- **Correlation** quota acheté ↔ rétention
