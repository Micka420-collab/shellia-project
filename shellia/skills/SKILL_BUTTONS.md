# 🔘 SKILL: Button Manager

## Description
Système de création et gestion de boutons Discord stylés, placables depuis Discord ou le site admin.

---

## 🎨 Styles de Boutons

| Style | Couleur | Usage | Emoji Défaut |
|-------|---------|-------|--------------|
| `primary` | 🟢 Bleu-violet | Action principale | - |
| `secondary` | ⚪ Gris | Action secondaire | - |
| `success` | 🟢 Vert | Confirmation, succès | ✅ |
| `danger` | 🔴 Rouge | Danger, annuler, supprimer | 🗑️ |
| `premium` | 🟡 Or | Premium, spécial, giveaway | ⭐ |
| `blurple` | 💜 Violet | Branding Discord | 💎 |

---

## 📦 Types de Boutons

| Type | Description | Action au clic |
|------|-------------|----------------|
| `ticket_create` | Ouvrir ticket support | Modal création ticket |
| `shop_access` | Accès boutique | Message éphemeral boutique |
| `plan_upgrade` | Upgrade compte | Lien vers plans |
| `support_faq` | FAQ & Aide | Embed FAQ |
| `giveaway_join` | Participer giveaway | Inscription giveaway |
| `feedback` | Donner avis | Modal feedback |
| `report` | Signaler | Modal signalement |
| `custom_link` | Lien personnalisé | Ouvrir URL |
| `custom_action` | Action custom | Webhook/action spéciale |

---

## 📡 API Endpoints

### Créer un Bouton
```http
POST http://localhost:8080/api/buttons/create
Content-Type: application/json

{
  "type": "ticket_create",
  "style": "primary",
  "label": "Créer un ticket",
  "emoji": "🎫",
  "channel_id": 123456789,
  "custom_data": {
    "category": "general",
    "priority": "medium"
  },
  "created_by": 999999999
}
```

**Réponse:**
```json
{
  "button_id": "btn_a1b2c3d4",
  "type": "ticket_create",
  "style": "primary",
  "label": "Créer un ticket",
  "emoji": "🎫",
  "channel_id": 123456789,
  "created_at": "2024-01-20T10:30:00Z",
  "status": "created"
}
```

### Placer un Bouton
```http
POST http://localhost:8080/api/buttons/{BUTTON_ID}/place

{
  "message_content": "Besoin d'aide ? Cliquez ci-dessous !",
  "position": "bottom"
}
```

### Créer une Toolbar (plusieurs boutons)
```http
POST http://localhost:8080/api/buttons/toolbar/create

{
  "channel_id": 123456789,
  "layout": "horizontal",  // horizontal, vertical, grid
  "message_content": "**Actions disponibles:**",
  "buttons": [
    {"type": "ticket_create", "style": "primary", "label": "Support"},
    {"type": "shop_access", "style": "success", "label": "Boutique"},
    {"type": "support_faq", "style": "secondary", "label": "FAQ"}
  ]
}
```

### Lister les Boutons Actifs
```http
GET http://localhost:8080/api/buttons?channel_id=123456789&active=true

{
  "buttons": [
    {
      "id": "btn_001",
      "type": "ticket_create",
      "label": "Créer un ticket",
      "emoji": "🎫",
      "channel_id": 123456789,
      "message_id": 987654321,
      "clicks_30d": 45,
      "unique_users_30d": 32
    }
  ]
}
```

### Mettre à jour un Bouton
```http
PATCH http://localhost:8080/api/buttons/{BUTTON_ID}

{
  "label": "Nouveau texte",
  "emoji": "✨",
  "style": "premium"
}
```

### Supprimer un Bouton
```http
DELETE http://localhost:8080/api/buttons/{BUTTON_ID}

{
  "reason": "Remplacé par nouveau design",
  "deleted_by": 999999999
}
```

### Stats d'un Bouton
```http
GET http://localhost:8080/api/buttons/{BUTTON_ID}/stats

{
  "total_clicks": 234,
  "unique_users": 189,
  "clicks_today": 12,
  "clicks_this_week": 67,
  "last_click": "2024-01-20T15:30:00Z",
  "conversion_rate": 15.2
}
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Bouton Ticket Auto
```
[Quand un nouveau channel support est créé]

Shellia: "Nouveau channel #support détecté. Je vais y placer un bouton de création de ticket."

→ Crée bouton: ticket_create, primary, 🎫
→ Place sur le channel
→ Confirme: "✅ Bouton placé sur #support"
```

### Scénario 2: Toolbar Boutique
```
Shellia: "Configuration de la toolbar boutique..."

Crée toolbar sur #boutique:
[🛍️ Voir la Boutique] [⭐ Passer Pro] [❓ FAQ]

→ Message: "Bienvenue dans la boutique !"
```

### Scénario 3: Modification rapide
```
Admin: "Shellia, change le bouton ticket pour mettre l'emoji 🆘"

Shellia: "✅ Bouton btn_001 mis à jour:
- Emoji: 🎫 → 🆘
- Style: primary (inchangé)
- Label: Créer un ticket (inchangé)

Le changement est visible immédiatement sur Discord."
```

---

## 🎯 Bonnes Pratiques

### Placement
```yaml
DO:
  - Placer les boutons importants en haut du channel
  - Utiliser des couleurs cohérentes (vert = positif, rouge = danger)
  - Limiter à 5 boutons par message
  - Grouper les actions liées dans une toolbar

DON'T:
  - Ne pas surcharger les channels de boutons
  - Éviter les couleurs qui ne correspondent pas à l'action
  - Ne pas créer de boutons redondants
```

### Accessibilité
```yaml
accessibility:
  - Toujours inclure un emoji pertinent
  - Garder les labels courts (< 30 caractères)
  - Utiliser des verbes d'action clairs
  - Tester sur mobile
```

### Tracking
```yaml
analytics:
  - Tracker tous les clics
  - Identifier les boutons sous-performants
  - A/B tester différents labels/styles
  - Review mensuelle des stats
```

---

## 🔄 Templates Prédéfinis

```python
BUTTON_TEMPLATES = {
    "support": {
        "type": "ticket_create",
        "style": "primary",
        "label": "Créer un ticket",
        "emoji": "🎫",
        "recommended_channels": ["#support", "#aide"]
    },
    "shop": {
        "type": "shop_access",
        "style": "success",
        "label": "Boutique",
        "emoji": "🛍️",
        "recommended_channels": ["#boutique", "#shop"]
    },
    "upgrade": {
        "type": "plan_upgrade",
        "style": "premium",
        "label": "Passer Pro",
        "emoji": "⭐",
        "recommended_channels": ["#general", "#announcements"]
    },
    "faq": {
        "type": "support_faq",
        "style": "secondary",
        "label": "FAQ",
        "emoji": "❓",
        "recommended_channels": ["#support", "#faq"]
    },
    "giveaway": {
        "type": "giveaway_join",
        "style": "premium",
        "label": "Participer",
        "emoji": "🎁",
        "recommended_channels": ["#giveaways", "#events"]
    }
}
```

---

## 📊 Analytics & Optimisation

### KPIs à surveiller
```yaml
button_performance:
  - ctr > 5%: 🟢 | 2-5%: 🟡 | < 2%: 🔴
  - unique_rate > 70%: 🟢 | 50-70%: 🟡 | < 50%: 🔴
  - conversion > 10%: 🟢 | 5-10%: 🟡 | < 5%: 🔴
```

### Rapport Automatique
```
Shellia: "📊 Button Analytics - Janvier 2024

Top Performers:
🥇 Bouton Support: 234 clics, 8.5% CTR
🥈 Bouton Shop: 189 clics, 6.2% CTR  
🥉 Bouton Pro: 156 clics, 12% conversion

À Optimiser:
⚠️ Bouton FAQ (#general): 0.8% CTR → Déplacer vers #support ?"
```

---

## 🔗 Intégration Discord

### Commandes
```
!button_create <type> <channel> [style] [label] [emoji]
!button_remove <button_id>
!button_list [channel]
!button_update <button_id> [label] [emoji] [style]
!button_stats <button_id>
!button_templates
!button_place <button_id> [message]
!button_toolbar <channel> <buttons_json>
```

### Exemples
```
!button_create ticket_create #support primary "Besoin d'aide ?" 🆘
!button_create shop_access #boutique success
!button_remove btn_a1b2c3
!button_update btn_x1y2z3 label:"Acheter maintenant" style:premium
```

---

## 🎨 Interface Admin

L'interface web admin est disponible sur:  
**https://shellia.ai/admin/buttons**

Features:
- 🎨 Preview en temps réel du rendu Discord
- 📋 Templates prédéfinis (drag & drop)
- 📊 Stats de clics par bouton
- 🔄 Édition sans recréer le bouton
- 🗑️ Suppression en un clic
- 📱 Liste des boutons actifs par channel
