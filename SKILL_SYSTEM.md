# 🧠 SHELLIA SKILLS SYSTEM

## Architecture des Skills

Shellia utilise un système de skills modulaires pour comprendre et interagir avec Maxis.

```
Shellia Controller
├── Core Skills
│   ├── Communication (Discord API)
│   ├── Maxis Control (API VM2)
│   └── Analytics (Data Analysis)
├── Business Skills
│   ├── E-commerce (Products, Orders)
│   ├── Billing (Stripe, Invoices)
│   ├── Marketing (Promos, Campaigns)
│   └── Ticketing (Support, FAQ)
└── Advanced Skills
    ├── Predictive Analysis
    ├── Automated Responses
    └── Multi-VM Orchestration
```

## Skill: Ticketing

### Capacités
- ✅ Créer/Consulter/Gérer des tickets
- ✅ Analyser les patterns de support
- ✅ Suggérer des solutions automatiques
- ✅ Escalader aux humains si nécessaire

### Triggers (Déclencheurs)
```python
triggers = [
    "problème", "bug", "aide", "support",
    "je ne peux pas", "ça marche pas", "erreur",
    "question", "demande", "suggestion"
]
```

### Actions
```python
actions = {
    "create_ticket": "Créer un nouveau ticket",
    "view_tickets": "Voir les tickets existants",
    "reply_ticket": "Répondre à un ticket",
    "escalate": "Escalader à un admin humain",
    "suggest_solution": "Proposer une solution automatique"
}
```

## Skill: Button Management

### Capacités
- ✅ Générer des boutons Discord stylés
- ✅ Placer des boutons sur des channels
- ✅ Gérer les interactions bouton
- ✅ Persistance des configurations

### Types de Boutons
```python
button_types = {
    "ticket_create": "🎫 Créer un ticket",
    "shop_access": "🛍️ Boutique",
    "plan_upgrade": "⭐ Upgrade",
    "support_faq": "❓ FAQ",
    "giveaway_join": "🎁 Participer",
    "custom_action": "Action personnalisée"
}
```

### Styles Disponibles
- 🟢 **Primary** (Vert) - Actions principales
- 🔵 **Secondary** (Gris) - Actions secondaires
- 🔴 **Danger** (Rouge) - Actions destructives
- 🟣 **Success** (Vert clair) - Confirmation
- 🟡 **Premium** (Or) - Actions premium

## Context Awareness

Shellia garde en mémoire:
```json
{
  "current_vm": "maxis-vm-01",
  "active_tickets": 12,
  "avg_response_time": "4.2h",
  "user_context": {
    "plan": "pro",
    "tickets_history": 3,
    "last_interaction": "2026-02-04T10:30:00Z"
  }
}
```

## Commandes Maîtres

### Depuis Discord
```
!shellia.skill ticketing enable
!shellia.skill ticketing stats
!shellia.skill button create <type> <channel>
!shellia.skill button list
!shellia.skill button remove <id>
```

### Depuis Interface Web
- Dashboard Skills actifs
- Configuration des boutons (drag & drop)
- Analytics des interactions
- Templates de boutons préconfigurés
