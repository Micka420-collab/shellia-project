# 🦀 OpenClaw Integration - Gestion Business Automatisée

## 📖 Vue d'ensemble

**OpenClaw** est le cerveau business de Shellia AI. Il gère automatiquement :
- 💰 **Rentabilité** : MRR, ARPU, conversion, churn
- 🎁 **Giveaways intelligents** : ROI-tracked, optimisés
- 🎉 **Promotions auto** : Welcome, winback, upsell
- 🏆 **Grade Winner** : Récompenses pour gagnants
- 🎯 **Événements** : Célébrations automatiques

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    🦀 OPENCLOW MANAGER                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Analytics   │  │  Promotions  │  │  Giveaways   │     │
│  │   Engine     │  │    Engine    │  │    Engine    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                 │                 │              │
│         ▼                 ▼                 ▼              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Business Intelligence                   │  │
│  │  • Rentabilité (MRR, LTV, CAC)                      │  │
│  │  • Prédictions de croissance                        │  │
│  │  • Optimisations automatiques                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │ Discord │    │   DB    │    │   VM    │
        │   Bot   │    │Supabase │    │OpenClaw │
        └─────────┘    └─────────┘    └─────────┘
```

---

## 🎯 Fonctionnalités

### 1. Analytics & Rentabilité

**Métriques trackées automatiquement :**
- **MRR** (Monthly Recurring Revenue)
- **ARPU** (Average Revenue Per User)
- **Conversion Rate** (% free → paid)
- **Churn Rate** (% de désabonnement)
- **LTV** (Lifetime Value)
- **CAC** (Customer Acquisition Cost)

**Commandes:**
```
!openclaw          → Dashboard complet
!oc_metrics 7      → Métriques sur 7 jours
!oc_giveaway_roi   → ROI des giveaways
```

### 2. Giveaways Intelligents

**Différence avec les giveaways basiques :**
- ✅ **ROI tracking** : Chaque giveaway est analysé
- ✅ **Optimisation** : Calcul du budget optimal
- ✅ **Grade Winner** : Les gagnants reçoivent un grade spécial
- ✅ **Intégration business** : Lié aux objectifs de croissance

**Grade Winner (🏆)** :
- Accès **Pro** pendant 3 jours (configurable)
- Badge exclusif
- Rôle Discord doré
- Accès salon privé #🏆│winners

**Commandes:**
```
!oc_giveaway_analyze 100 150  → Analyse rentabilité
!oc_winner_cleanup           → Nettoyer grades expirés
```

### 3. Promotions Automatiques

**Types de promotions:**

| Type | Déclencheur | Réduction |
|------|-------------|-----------|
| **Welcome** | Nouveau membre (<24h) | 20% |
| **Winback** | Inactif 7+ jours | 40% |
| **Upsell** | Pro depuis 30j + actif | 25% |
| **Abandoned Cart** | Panier abandonné | 15% |
| **Loyalty** | Fidélité | Variable |

**Fonctionnement:**
- Détection automatique toutes les 30 minutes
- Code promo unique par utilisateur
- Durée limitée (24-72h)
- Tracking des conversions

**Commandes:**
```
!oc_promos                    → Liste promotions actives
!oc_promo_create @user 20 48 "Message"  → Créer manuellement
!oc_promo_disable             → Désactiver auto
!oc_promo_enable              → Réactiver auto
!my_promo                     → Voir mes promos
```

### 4. Winback (Récupération Clients)

**Détection automatique des utilisateurs à risque:**
- Inactifs depuis 7+ jours
- Étaient payants (Pro/Ultra)
- Grosse réduction (40%) pour les récupérer

**Process:**
1. Détection quotidienne
2. Envoi code promo personnalisé
3. Tracking de la reconversion
4. Stats de récupération

### 5. Événements Automatiques

**Célébrations déclenchées automatiquement:**
- Objectif MRR atteint
- Record de conversion
- Palier de membres
- Anniversaire serveur

**Récompenses:**
- Giveaway spécial
- Message de félicitations
- Badge temporaire

**Commande:**
```
!oc_event_trigger mrr_target 5000  → Déclencher manuellement
```

---

## ⚙️ Configuration

### Objectifs Business

```bash
!oc_config_set target_mrr 10000           # Objectif MRR (€)
!oc_config_set target_conversion 0.08     # Objectif conversion (8%)
!oc_config_set max_cac 60                 # CAC max acceptable (€)
```

### Promotions

```bash
!oc_config_set max_discount_percent 35    # Réduction max auto
!oc_config_set promotion_cooldown_days 5  # Délai entre promos
!oc_config_set winback_discount 50        # Réduction winback
```

### Giveaways

```bash
!oc_config_set giveaway_roi_target 2.5    # ROI minimum
!oc_config_set max_giveaway_budget_percent 0.15  # 15% du MRR
```

### Grade Winner

```bash
!oc_config_set winner_plan_duration_days 7    # Durée Pro offert
!oc_config_set winner_plan_type ultra         # Plan offert
```

---

## 💰 Modèle Économique

### Rentabilité des Giveaways

**Calcul du ROI:**
```
ROI = Revenu généré / Coût du giveaway
```

**Revenu généré estimé:**
```
Nouveaux membres × 5% (conversion) × ARPU
```

**Stratégie:**
- Si ROI < 2x → Réduire les récompenses
- Si ROI > 3x → Augmenter les giveaways
- Budget max = 10% du MRR

### Fidélisation

**Coût de fidélisation vs Acquisition:**
- **Winback** : 40% de réduction = coût ~€4-8
- **Nouveau client** : CAC ~€20-50
- **Conclusion** : Winback 3-5x moins cher !

---

## 🗄️ Base de Données

### Tables créées

```sql
business_metrics          → Métriques quotidiennes
openclaw_config           → Configuration
user_journeys            → Parcours utilisateurs
user_promotions          → Promotions actives
winner_rewards           → Grades Winner
giveaway_roi_analysis    → ROI des giveaways
milestone_events         → Événements célébrés
abandoned_carts          → Paniers abandonnés
user_subscriptions       → Abonnements complets
```

### Installation

```bash
psql -U user -d db -f deployment/openclaw_schema.sql
psql -U user -d db -f deployment/giveaway_schema.sql
```

---

## 📊 Dashboard OpenClaw

### Vue d'ensemble (`!openclaw`)

```
📊 Rapport Business OpenClaw
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 MRR: €3,250.50 / €5,000
📈 Conversion: 4.2% / 5%
👥 Utilisateurs: 850 actifs / 42 payants
💵 ARPU: €77.39
🔄 Churn: 2.1%
🎁 Promotions: 12 actives

💡 Recommandations:
📉 Augmenter les promotions de conversion
🚀 Lancer une campagne de growth
```

### KPIs trackés

| KPI | Actuel | Objectif | Tendance |
|-----|--------|----------|----------|
| MRR | €3,250 | €5,000 | 📈 +12% |
| Conversion | 4.2% | 5% | 📉 -0.5% |
| Churn | 2.1% | <3% | ✅ Bon |
| ARPU | €77 | >€50 | ✅ Bon |

---

## 🎮 Workflow Automatique

### 1. Nouveau membre rejoint

```
1. User join
     ↓
2. Création journey
     ↓
3. Promotion Welcome (20%, 48h)
     ↓
4. Tracking premier message
     ↓
5. Tag "active_user" si engage
```

### 2. Giveaway déclenché

```
1. Palier atteint (ex: 100 membres)
     ↓
2. Analyse ROI par OpenClaw
     ↓
3. Giveaway lancé si rentable
     ↓
4. Participants → Tracking
     ↓
5. Tirage au sort
     ↓
6. Gagnants → Grade Winner + Pro 3j
     ↓
7. ROI calculé et stocké
```

### 3. Utilisateur inactif

```
1. Détection inactivité 7+ jours
     ↓
2. Marquage "churn_risk"
     ↓
3. Promotion Winback (40%, 72h)
     ↓
4. Envoi MP personnel
     ↓
5. Tracking reconversion
     ↓
6. Stats de récupération
```

---

## 🔧 Intégration VM OpenClaw

### Déploiement

```bash
# Sur la VM OpenClaw
git clone https://github.com/votre-repo/shellia-ai.git
cd shellia-ai

# Configuration
nano .env
# Ajouter:
# OPENCLOW_MODE=full
# OPENCLOW_VM_ID=votre_vm_id

# Installation
docker-compose up -d

# Vérification
docker logs shellia-bot
```

### Monitoring

```bash
# Logs business
docker logs shellia-bot | grep "OpenClaw"

# Métriques
!openclaw

# Alertes automatiques si:
# - MRR en baisse >10%
# - Churn >5%
# - ROI giveaways <2x
```

---

## 📈 Optimisations Automatiques

### Ajustements dynamiques

OpenClaw ajuste automatiquement :

| Condition | Action |
|-----------|--------|
| Conversion < 3% | Augmenter promotions welcome |
| Churn > 5% | Renforcer winback |
| ROI giveaways < 2x | Réduire budget giveaways |
| MRR en baisse | Lancer campagne growth |

---

## 🎓 Bonnes Pratiques

### 1. Surveiller les métriques
```
!openclaw quotidiennement
!oc_metrics hebdomadairement
```

### 2. Ajuster les objectifs
```
# Si objectifs atteints → Augmenter
!oc_config_set target_mrr 7500

# Si trop difficiles → Réduire temporairement
!oc_config_set target_conversion 0.04
```

### 3. Analyser les promotions
```
!oc_promos
# Vérifier quels types convertissent le mieux
# Ajuster les réductions en conséquence
```

### 4. Nettoyer régulièrement
```
!oc_winner_cleanup  # Retirer grades expirés
```

---

## 🐛 Dépannage

### Problème: Promotions ne s'envoient pas
**Solutions:**
1. Vérifier `!oc_config` → enable_auto_promotions
2. Vérifier logs : `docker logs shellia-bot | grep promotion`
3. Vérifier tables SQL

### Problème: Grade Winner pas assigné
**Solutions:**
1. Vérifier que le rôle "🏆 Winner" existe
2. Vérifier permissions du bot
3. `!oc_winner_cleanup` pour reset

### Problème: Métriques à 0
**Solutions:**
1. Vérifier connexion DB
2. Exécuter `openclaw_schema.sql`
3. Attendre 1h (premier calcul)

---

## 📞 Support

En cas de problème :
1. Consulter les logs: `docker logs shellia-bot`
2. Vérifier la config: `!oc_config`
3. Vérifier la DB: tables `business_metrics`, `user_journeys`
4. Contacter l'admin OpenClaw

---

## 🎯 Roadmap OpenClaw

### v2.2 (Prochain)
- [ ] Prédictions ML de churn
- [ ] A/B testing des promotions
- [ ] Intégration email marketing
- [ ] Dashboard web temps réel

### v2.3 (Futur)
- [ ] Automatisation complète (0 intervention)
- [ ] IA pour optimiser les prix
- [ ] Prédictions de revenus
- [ ] Alertes intelligentes

---

**🦀 OpenClaw fait tourner votre business en mode automatique !**

*Version: 2.1-OPENCLOW*
