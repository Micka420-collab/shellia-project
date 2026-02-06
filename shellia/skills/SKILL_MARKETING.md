# 📢 SKILL: Marketing & Rôles Communautaires

## Description
Gestion des rôles marketing (Ambassador, Influencer, Creator, etc.) et des campagnes communautaires.

---

## 🎭 Rôles Marketing Disponibles

| Rôle | Emoji | Permissions | Avantages |
|------|-------|-------------|-----------|
| **Ambassador** | 🌟 | Badge spécial, salon privé | 20% commission affiliés |
| **Influencer** | 📱 | Accès early features | Produits gratuits |
| **Creator** | 🎨 | Ressources branding | Featured sur le site |
| **Helper** | 🆘 | Modération légère | Badge Helper |
| **Event Host** | 🎉 | Créer des événements | Planning prioritaire |
| **Beta Tester** | 🧪 | Accès bêta | Influence roadmap |
| **Partner** | 🤝 | Co-marketing | Revenue share |

---

## 📡 API Endpoints

### Attribuer un Rôle Marketing
```http
POST http://localhost:8080/api/marketing/roles/assign
Content-Type: application/json

{
  "user_id": 123456789,
  "role": "ambassador",
  "assigned_by": 999999999,
  "reason": "Excellente participation communautaire",
  "duration_months": 6
}
```

### Retirer un Rôle
```http
POST http://localhost:8080/api/marketing/roles/remove
Content-Type: application/json

{
  "user_id": 123456789,
  "role": "ambassador",
  "removed_by": 999999999,
  "reason": "Inactivité prolongée"
}
```

### Liste des Membres par Rôle
```http
GET http://localhost:8080/api/marketing/roles/{ROLE}/members
```

### Statistiques d'Influence
```http
GET http://localhost:8080/api/marketing/influencer/{USER_ID}/stats

{
  "referrals": 45,
  "conversions": 12,
  "revenue_generated": 890.50,
  "content_posts": 23,
  "engagement_rate": 8.5
}
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Attribution automatique
```
[Shellia détecte un utilisateur actif avec 50+ invites]

Shellia: "🎉 Félicitations @User !

Vous avez été sélectionné pour devenir **Community Helper** !
Votre aide précieuse dans le serveur a été remarquée.

🆘 Nouveaux pouvoirs:
• Badge Helper exclusif
• Accès au salon #helpers-lounge
• Possibilité de modérer léger

Acceptez-vous ce rôle ? (Réagissez ✅)"
```

### Scénario 2: Dashboard Influencer
```
Shellia en DM à un Influencer:

"📊 Vos stats ce mois:

📱 Posts: 12
👀 Impressions: 45.2K
💰 Commissions: €234.50
🎯 Conversions: 8

Continuez comme ça ! Prochain palier: €500 = Bonus €50"
```

### Scénario 3: Campagne marketing
```
Shellia: "📢 **Nouvelle Campagne: Summer Sale 2026**

@Ambassador @Influencer @Creator

🎯 Objectif: 100 nouveaux utilisateurs
📅 Période: 1-31 Juillet
💰 Récompenses:
   • Top 3: €100 bonus
   • Top 10: Goodie box
   • Tous: +5% commission

Créez du contenu avec #ShelliaSummer et trackez vos résultats ici:
https://shellia.ai/campaigns/summer2026"
```

---

## 🎁 Programmes de Parrainage

### Créer un code affilié
```http
POST http://localhost:8080/api/marketing/affiliate/create

{
  "user_id": 123456789,
  "code": "ALICE20",  // ou auto-generate
  "discount_percent": 20,
  "commission_percent": 15
}
```

### Stats affilié
```http
GET http://localhost:8080/api/marketing/affiliate/{CODE}/stats

{
  "code": "ALICE20",
  "uses": 156,
  "revenue": 2340.00,
  "commission_earned": 351.00,
  "payout_status": "pending",
  "top_referrers": [...]
}
```

---

## 🏆 Gamification

### Points Communautaires
```python
# Actions qui rapportent des points
POINTS_SYSTEM = {
    "message_sent": 1,
    "help_answered": 10,
    "invite_accepted": 50,
    "content_featured": 100,
    "bug_report_valid": 25,
    "review_5_stars": 20
}
```

### Paliers
```
🥉 Bronze: 0-499 pts
🥈 Silver: 500-1999 pts  → Accès #vip-silver
🥇 Gold: 2000-4999 pts   → Accès #vip-gold + badge
💎 Diamond: 5000+ pts    → Accès #vip-diamond + avantages Pro 1 mois
```

---

## 🎉 Événements Communautaires

### Planifier un événement
```http
POST http://localhost:8080/api/events/create

{
  "title": "Tournoi Valorant",
  "type": "tournament|ama|workshop|party",
  "datetime": "2024-02-15T20:00:00Z",
  "description": "Tournoi 5v5 avec prizes !",
  "host_id": 123456789,
  "max_participants": 50,
  "rewards": {
    "winner": "Pro plan 3 mois",
    "participant": "Badge tournoi"
  }
}
```

### Shellia gère l'événement
```
Shellia: "🎮 **Tournoi Valorant - Dans 1h !**

Inscrits: 48/50
Check-in ouvert !
Réagissez ✅ pour confirmer votre présence.

🎁 Prizes:
🥇 1er: Pro 3 mois + €50
🥈 2ème: Pro 1 mois
🥉 3ème: Badge exclusif

Bonne chance à tous ! 🍀"
```

---

## 📈 Analytics Marketing

### Rapport Hebdomadaire
```
Shellia: "📊 **Marketing Weekly Report**

👥 Nouveaux membres: +234 (+12%)
🎭 Nouveaux rôles attribués: 15
💰 Revenue affiliés: €1,234
📱 Posts UGC: 45
⭐ NPS Score: 72

🔥 Top Ambassadeurs:
1. @Alice - €340 revenue
2. @Bob - €280 revenue
3. @Charlie - €195 revenue

💡 Insights:
• Les posts vidéo convertissent 3x mieux
• Meilleur timing: 18h-21h CET"
```

---

## 🔗 Intégration Discord

### Commandes
```
!marketing_role assign @user <role> [durée_mois]
!marketing_role remove @user <role>
!marketing_stats @user
!affiliate create [code_personnalisé]
!affiliate stats
!event create "Titre" date type
!event list
!points @user
!leaderboard
```

### Boutons
```python
# Bouton de candidature
await button_manager.create_button(
    type=ButtonType.CUSTOM_ACTION,
    channel_id=marketing_channel_id,
    style=ButtonStyle.PREMIUM,
    label="Devenir Ambassadeur",
    emoji="🌟",
    custom_data={"action": "apply_ambassador"}
)
```
