# 📦 SKILL: Embed Builder (Humbles)

## Description
Création et gestion d'embeds Discord riches avec boutons, paiements intégrés et templates (style MEE6).

---

## 🎨 Structure d'un Embed

```yaml
embed:
  # Métadonnées
  name: "Nom interne"
  channel_id: 123456789
  
  # Contenu
  color: "#5865F2"        # Couleur de la barre latérale
  author:                # En-tête
    name: "Auteur"
    icon_url: "https://..."
    url: "https://..."
  title: "Titre"         # Titre principal (lien cliquable)
  url: "https://..."     # URL du titre
  description: "Texte"   # Description (supporte markdown)
  
  # Médias
  image: "https://..."   # Image large
  thumbnail: "https://..." # Miniature (coin droit)
  
  # Fields (max 25)
  fields:
    - name: "Titre"
      value: "Contenu"
      inline: true/false
  
  # Pied de page
  footer:
    text: "Texte"
    icon_url: "https://..."
  timestamp: "current" | "ISO date" | null
  
  # Boutons (max 5 par ligne, 5 lignes max)
  buttons:
    - label: "Texte"
      emoji: "🎉"
      style: "primary|secondary|success|danger|premium"
      action: "link|payment|ticket|giveaway|custom"
      url: "https://..."           # Si action = link
      payment_config: {...}        # Si action = payment
```

---

## 📡 API Endpoints

### Créer un Embed
```http
POST http://localhost:8080/api/embeds/create
Content-Type: application/json

{
  "name": "Promo Janvier 2024",
  "channel_id": 123456789,
  "color": "#f59e0b",
  "title": "🎉 Offre Spéciale -30% !",
  "description": "Profitez de **30% de réduction** sur le plan Pro !",
  "image": "https://shellia.ai/promo-banner.png",
  "footer": "Offre limitée",
  "timestamp": "current",
  "fields": [
    {"name": "💰 Prix", "value": "€6.99/mois", "inline": true},
    {"name": "⏰ Durée", "value": "Limitée", "inline": true}
  ],
  "buttons": [
    {
      "label": "Acheter maintenant",
      "emoji": "💳",
      "style": "premium",
      "action": "payment",
      "payment_config": {
        "product_id": "price_pro_monthly",
        "display_price": "€6.99"
      }
    },
    {
      "label": "Plus d'infos",
      "emoji": "ℹ️",
      "style": "secondary",
      "action": "link",
      "url": "https://shellia.ai/plans"
    }
  ]
}
```

**Réponse:**
```json
{
  "embed_id": "EMB001",
  "status": "created",
  "preview_url": "https://shellia.ai/admin/embeds/EMB001/preview"
}
```

### Envoyer un Embed sur Discord
```http
POST http://localhost:8080/api/embeds/{EMBED_ID}/send

{
  "channel_id": 123456789  // Optionnel - override le channel par défaut
}
```

### Mettre à jour un Embed
```http
PATCH http://localhost:8080/api/embeds/{EMBED_ID}

{
  "title": "Nouveau titre",
  "description": "Nouvelle description"
}
```

### Dupliquer un Embed
```http
POST http://localhost:8080/api/embeds/{EMBED_ID}/duplicate

{
  "new_name": "Promo Février 2024"
}
```

### Supprimer un Embed
```http
DELETE http://localhost:8080/api/embeds/{EMBED_ID}
```

### Lister les Embeds
```http
GET http://localhost:8080/api/embeds?channel_id=123&active=true

{
  "embeds": [
    {
      "id": "EMB001",
      "name": "Promo Janvier",
      "channel_id": 123456789,
      "clicks": 234,
      "views": 567,
      "conversion_rate": 12.5,
      "is_active": true
    }
  ]
}
```

### Stats d'un Embed
```http
GET http://localhost:8080/api/embeds/{EMBED_ID}/stats

{
  "total_clicks": 234,
  "unique_users": 189,
  "clicks_by_button": {
    "btn_1": 156,
    "btn_2": 78
  },
  "conversion_rate": 12.5,
  "revenue_generated": 1234.50,
  "peak_hours": ["18:00", "20:00", "21:00"]
}
```

---

## 🎨 Templates Disponibles

| Template | Usage | Boutons par défaut |
|----------|-------|-------------------|
| **welcome** | Message de bienvenue | - |
| **promo** | Offre promotionnelle | Paiement |
| **announcement** | Annonce importante | - |
| **giveaway** | Concours/giveaway | Participer |
| **rules** | Règlement serveur | - |
| **shop** | Showcase boutique | Paiement, Détails |

### Appliquer un Template
```http
POST http://localhost:8080/api/embeds/templates/{TEMPLATE_NAME}/apply

{
  "channel_id": 123456789,
  "variables": {
    "server_name": "Shellia Community"
  }
}
```

---

## 💳 Boutons de Paiement

```json
{
  "label": "Acheter Pro",
  "emoji": "💳",
  "style": "premium",
  "action": "payment",
  "payment_config": {
    "product_id": "price_xxx",        // Stripe Price ID
    "display_price": "€9.99",
    "success_url": "https://shellia.ai/success",
    "cancel_url": "https://shellia.ai/cancel",
    "affiliate_code": null            // Auto-track si présent
  }
}
```

### Flux de Paiement
```
1. User clique bouton "Acheter"
   ↓
2. Modal/ ephemeral message avec lien Stripe
   ↓
3. Redirection checkout Stripe
   ↓
4. Paiement complet
   ↓
5. Webhook → Activation plan
   ↓
6. Commission affilié (si code utilisé)
   ↓
7. Notification user
```

---

## 💬 Utilisation par Shellia

### Scénario 1: Créer un embed promo
```
Admin: "Shellia, crée un embed pour la promo de -30%"

Shellia: "Je vais créer l'embed de promotion. Voici l'aperçu:

[Preview Discord de l'embed]

📦 **Promo Janvier 2024**
🎉 Offre Spéciale -30% !
Profitez de **30% de réduction** sur le plan Pro !

[Bouton: 💳 Acheter maintenant]
[Bouton: ℹ️ Plus d'infos]

Confirmez-vous l'envoi sur #boutique ?"

Admin: "Oui envoie"

Shellia: "✅ Embed envoyé sur #boutique !"
```

### Scénario 2: Modification rapide
```
Admin: "Modifie l'embed EMB001 pour mettre -40% au lieu de -30%"

Shellia: "✅ Embed EMB001 mis à jour:
- Title: -30% → -40%
- Prix affiché: €6.99 → €5.99

Le message Discord a été édité automatiquement."
```

### Scénario 3: Stats embed
```
Admin: "Stats de l'embed promo ?"

Shellia: "📊 **Stats Embed Promo Janvier**

👀 Vues: 567
👆 Clicks: 234 (41.3% CTR)
💳 Achats: 29 (12.4% conversion)
💰 Revenue: €289.71

📈 **Performance:**
• Bouton 'Acheter': 156 clicks
• Bouton 'Infos': 78 clicks

⏰ **Meilleurs horaires:**
18h-21h: +45% d'activité

💡 Recommandation: Relancer ce soir à 19h"
```

### Scénario 4: Welcome message automatique
```
[Nouveau membre rejoint]

Shellia: "👋 Bienvenue @NewUser !

[Embed stylé avec règles, liens utiles, bouton rôles]

Bienvenue sur Shellia Community ! 🎉"
```

---

## 🎯 Types de Boutons & Actions

| Action | Description | Configuration requise |
|--------|-------------|----------------------|
| **link** | Ouvre un lien | `url` |
| **payment** | Paiement Stripe | `payment_config.product_id` |
| **ticket** | Crée un ticket | - |
| **giveaway** | Inscrit au giveaway | - |
| **upgrade** | Affiche plans | - |
| **feedback** | Modal feedback | - |
| **custom** | Action webhook | `custom_action` |

---

## 📊 Analytics & Tracking

### Événements Trackés
```python
EMBED_EVENTS = {
    "view": "Embed affiché à l'utilisateur",
    "click": "Bouton cliqué",
    "conversion": "Paiement effectué",
    "hover": "Survol du bouton (optionnel)"
}
```

### Heatmap
```
Shellia: "🔥 **Heatmap Embed Shop**

Zones les plus cliquées:
1. Bouton 'Acheter Pro' - 67%
2. Bouton 'Compare Plans' - 23%
3. Lien 'FAQ' - 10%

💡 Recommandation: Déplacer FAQ en bouton plus visible"
```

---

## 🔗 Intégration Discord

### Commandes
```
!embed create <channel> [template]
!embed list [channel]
!embed edit <embed_id>
!embed send <embed_id> [channel]
!embed duplicate <embed_id>
!embed delete <embed_id>
!embed stats <embed_id>
!embed templates
```

### Exemples
```
!embed create #boutique promo
!embed list
!embed edit EMB001
!embed send EMB001 #general
!embed stats EMB001
```

---

## 🛠️ Interface Admin

L'interface web complète est disponible sur:  
**https://shellia.ai/admin/embeds**

### Features
- 🎨 **Builder visuel** drag & drop
- 👁️ **Preview temps réel** Discord
- 📋 **Templates** prédéfinis
- 💳 **Intégration Stripe** native
- 📊 **Analytics** détaillés
- 🔄 **Édition live** (update sans resend)
- ⏰ **Programmation** d'envoi
- 📱 **Responsive** (mobile-friendly)

---

## 📝 Markdown Supporté

```markdown
**gras**
*italique*
__souligné__
`code`
~~barré~~

# Titre (via fields)
- Liste à puces
1. Liste numérotée

[Lien](URL)

> Citation
```

---

## ⚡ Webhooks

### Recevoir les événements
```http
POST https://votre-webhook.com/embed-events

{
  "event": "embed.click",
  "embed_id": "EMB001",
  "button_id": "btn_1",
  "user_id": 123456789,
  "timestamp": "2024-01-20T14:30:00Z"
}
```

Événements disponibles:
- `embed.created`
- `embed.sent`
- `embed.click`
- `embed.payment.completed`
- `embed.edited`
- `embed.deleted`
