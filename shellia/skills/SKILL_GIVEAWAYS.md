# 🎁 SKILL: Système de Giveaways

## Description
Gestion automatique des giveaways avec déclenchement par paliers de membres et système de récompenses Winner.

---

## 🎯 Déclenchement Automatique

### Palier de Membres
```python
GIVEAWAY_TIERS = {
    50: {"prize": "Pro 1 mois", "winners": 1, "duration_hours": 48},
    100: {"prize": "Pro 3 mois", "winners": 2, "duration_hours": 72},
    250: {"prize": "Ultra 1 mois", "winners": 3, "duration_hours": 96},
    500: {"prize": "Ultra 3 mois", "winners": 5, "duration_hours": 120},
    1000: {"prize": "Founder Lifetime", "winners": 1, "duration_hours": 168},
    2500: {"prize": "Founder Lifetime x3", "winners": 3, "duration_hours": 168},
    5000: {"prize": "€500 cash + Founder", "winners": 5, "duration_hours": 168}
}
```

### Logique de détection
```python
async def on_member_join(member):
    count = guild.member_count
    
    # Vérifier si on atteint un palier
    for tier, config in GIVEAWAY_TIERS.items():
        if count == tier:
            await create_giveaway(tier, config)
            await announce_milestone(tier)
```

---

## 📡 API Endpoints

### Créer un Giveaway
```http
POST http://localhost:8080/api/giveaways/create
Content-Type: application/json

{
  "prize": "Pro 3 mois",
  "description": "🎉 Merci pour les 100 membres !",
  "winners_count": 2,
  "duration_hours": 72,
  "milestone": 100,  // ou null si manuel
  "requirements": {
    "min_account_age_days": 7,
    "roles_required": [],
    "boost_only": false
  }
}
```

**Réponse:**
```json
{
  "giveaway_id": "GWY001",
  "message_id": "123456789",
  "channel_id": "987654321",
  "ends_at": "2024-01-23T18:00:00Z",
  "participants_count": 0
}
```

### Tirer les Gagnants
```http
POST http://localhost:8080/api/giveaways/{ID}/draw
```

**Réponse:**
```json
{
  "winners": [
    {"user_id": 111, "username": "Alice", "plan_upgraded": true},
    {"user_id": 222, "username": "Bob", "plan_upgraded": true}
  ],
  "backup_winners": [333, 444, 555]  // Si un gagnant ne répond pas
}
```

### Liste des Giveaways
```http
GET http://localhost:8080/api/giveaways?status=active|ended|all
```

### Stats d'un Giveaway
```http
GET http://localhost:8080/api/giveaways/{ID}/stats

{
  "participants": 89,
  "unique_participants": 85,
  "conversion_rate": 12.5,
  "new_members_during": 23,
  "engagement_score": 8.7
}
```

---

## 🏆 Système Winner

### Grade Winner (3 jours Pro)
```python
WINNER_PERKS = {
    "role": "🏆 Winner",
    "duration": "3 days",
    "permissions": [
        "access_pro_channels",
        "priority_support",
        "exclusive_commands"
    ],
    "color": 0xFFD700  // Or
}
```

### Attribution automatique
```python
async def on_giveaway_end(giveaway_id):
    winners = await draw_winners(giveaway_id)
    
    for winner in winners:
        # Attribuer grade Winner
        await assign_role(winner.user_id, "Winner", duration=timedelta(days=3))
        
        # Upgrade plan si pas déjà Pro+
        if winner.current_plan == "free":
            await upgrade_plan(winner.user_id, "pro", duration=timedelta(days=3))
        
        # Notifier
        await send_dm(winner.user_id, """
        🎉 Félicitations ! Vous avez gagné le giveaway !
        
        🏆 Grade Winner pendant 3 jours
        ⭐ Accès Pro pendant 3 jours
        
        Profitez de vos avantages !
        """)
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Palier atteint
```
[100ème membre rejoint]

Shellia: "🎉🎉🎉 **100 MEMBRES !** 🎉🎉🎉

Merci à tous pour cette incroyable croissance !
Pour fêter ça, un giveaway automatique a été lancé !

🎁 **À gagner: 2x Pro 3 mois**
⏰ **Fin:** Dans 72h
👥 **Participants:** 0

Réagissez 🎉 pour participer !

[Bouton: Participer au Giveaway]"
```

### Scénario 2: Rappel avant fin
```
Shellia: "⏰ **Giveaway se termine dans 2h !**

🎁 Pro 3 mois à gagner
👥 89 participants
🎲 2 gagnants

Dernière chance pour participer !"
```

### Scénario 3: Annonce gagnants
```
Shellia: "🎊 **Gagnants du Giveaway 100 membres !** 🎊

Félicitations à:
🥇 @Alice
🥇 @Bob

Vous remportez chacun **Pro 3 mois** + **Grade Winner 3j** !

🏆 Grade Winner: Accès channels exclusifs
⭐ Pro 3 mois: Toutes les fonctionnalités premium

Vos récompenses sont déjà actives !

📊 Stats du giveaway:
• 89 participants
• 85 participants uniques
• 23 nouveaux membres pendant l'event

Merci à tous ! Prochain palier: 250 membres 🚀"
```

---

## 🎨 Types de Giveaways

### 1. Milestone (Automatique)
```python
# Déclenché par nombre de membres
auto_create_on_milestone = True
```

### 2. Manuel (Admin)
```http
POST /api/giveaways/create
{
  "prize": "Nitro 1 mois",
  "winners_count": 1,
  "duration_hours": 24,
  "milestone": null  # Manuel
}
```

### 3. Conditionnel
```python
# Ex: Seulement pour les Boosters
giveaway = {
    "prize": "Founder Lifetime",
    "requirements": {
        "boost_only": True,
        "min_boost_level": 1
    }
}
```

### 4. Récurent
```python
# Giveaway hebdomadaire automatique
SCHEDULED_GIVEAWAYS = {
    "weekly": {
        "day": "friday",
        "time": "18:00",
        "prize": "Pro 1 mois",
        "winners": 1
    }
}
```

---

## 📊 Analytics

### Dashboard Giveaways
```
Shellia: "📊 **Giveaway Analytics**

🏆 Giveaways terminés: 5
🎁 Total prizes distribués: €2,340
👥 Participants totaux: 456
✅ Taux de conversion: 15.2%

📈 Meilleurs giveaways:
1. 100 membres - 89 participants
2. 50 membres - 67 participants
3. Noël 2025 - 134 participants

💡 Insights:
• Les giveaways weekend = +40% participation
• Pro 3 mois = plus attractif que Ultra 1 mois
• Mentionner @everyone = +25% reach"
```

---

## 🔗 Intégration Discord

### Commandes
```
!giveaway create "Prix" winners duration [requirements]
!giveaway end <giveaway_id>
!giveaway reroll <giveaway_id>
!giveaway list [status]
!giveaway stats <giveaway_id>
!giveaway delete <giveaway_id>
```

### Boutons
```python
# Bouton participation
await button_manager.create_button(
    type=ButtonType.GIVEAWAY_JOIN,
    channel_id=giveaway_channel_id,
    style=ButtonStyle.PREMIUM,
    label="Participer au Giveaway",
    emoji="🎁",
    custom_data={"giveaway_id": "GWY001"}
)
```

---

## 🎯 Prochains Palier Messages

```python
MILESTONE_MESSAGES = {
    50: "🌱 Nos premiers 50 membres ! Merci de croire en nous !",
    100: "🚀 100 membres ! La communauté grandit !",
    250: "🔥 250 membres ! Vous êtes incroyables !",
    500: "⚡ 500 membres ! Demi-millennium atteint !",
    1000: "🎆 1000 MEMBRES ! C'est officiellement une grande famille !",
    2500: "💎 2500 membres ! Milestone diamant !",
    5000: "🏆 5000 MEMBRES ! Légendaire !",
    10000: "👑 10000 MEMBRES ! On écrit l'histoire ensemble !"
}
```
