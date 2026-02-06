# 🎫 SKILL: Gestion des Tickets Support

## Description
Shellia peut créer et gérer des tickets de support utilisateur via l'API Maxis.
Les tickets sont STRICTEMENT isolés par utilisateur (Privacy by Design).

---

## 📡 API Endpoints

### Créer un Ticket
```http
POST http://localhost:8080/api/tickets
Content-Type: application/json
Authorization: Bearer {DISCORD_TOKEN}

{
  "user_id": 123456789,
  "category": "general|billing|technical|bug_report|account|suggestion",
  "subject": "Problème de connexion",
  "description": "Je ne peux pas me connecter depuis ce matin...",
  "priority": "low|medium|high|critical"
}
```

**Réponse:**
```json
{
  "ticket_id": "TKTA1B2C3",
  "status": "open",
  "created_at": "2024-01-20T10:30:00Z",
  "url": "https://admin.shellia.ai/tickets/TKTA1B2C3"
}
```

### Lister les Tickets (Admin uniquement)
```http
GET http://localhost:8080/api/tickets?status=open&priority=high
Authorization: Bearer {DISCORD_TOKEN}
```

### Répondre à un Ticket
```http
POST http://localhost:8080/api/tickets/{TICKET_ID}/reply
Content-Type: application/json
Authorization: Bearer {DISCORD_TOKEN}

{
  "message": "Merci pour votre patience...",
  "internal_note": false  // true = note interne (admin uniquement)
}
```

### Fermer un Ticket
```http
POST http://localhost:8080/api/tickets/{TICKET_ID}/close
Authorization: Bearer {DISCORD_TOKEN}

{
  "resolution": "Problème résolu par réinitialisation du mot de passe",
  "notify_user": true
}
```

### Statistiques
```http
GET http://localhost:8080/api/tickets/stats
Authorization: Bearer {DISCORD_TOKEN}
```

---

## 🏷️ Catégories de Tickets

| Catégorie | Description | SLA |
|-----------|-------------|-----|
| `general` | Questions générales | 72h |
| `billing` | Problèmes de paiement | 24h |
| `technical` | Support technique | 48h |
| `bug_report` | Signalement de bugs | 48h |
| `account` | Problèmes de compte | 24h |
| `suggestion` | Suggestions | 72h |

## 🚨 Priorités & SLA

| Priorité | Temps de réponse | Action |
|----------|------------------|--------|
| `critical` | 12h | Mentionner @Support immédiatement |
| `high` | 24h | Notifier l'équipe senior |
| `medium` | 48h | Assigner normalement |
| `low` | 72h | Traiter quand possible |

---

## 💬 Utilisation par Shellia

### Scénario 1: Utilisateur demande de l'aide
```
Utilisateur: "J'ai un problème avec mon paiement"

Shellia: "Je vais créer un ticket pour vous. Pouvez-vous me donner plus de détails sur le problème de paiement ?"

[Après collecte des infos]

Shellia: "✅ Ticket créé !
🎫 **Numéro:** TKT123456
📧 **Sujet:** Problème de paiement Stripe
⏱️ **SLA:** 24h (priorité haute)

Un agent vous répondra sous 24h. Vous pouvez suivre votre ticket sur: https://shellia.ai/ticket/TKT123456"
```

### Scénario 2: Rappel de tickets en attente
```
Shellia: "📊 **Rappel Tickets**
3 tickets en attente depuis +24h:
• TKT001 - Billing (Alice) - 36h ⏰
• TKT002 - Bug (Bob) - 28h ⏰
• TKT003 - General (Charlie) - 25h

N'oubliez pas de répondre !"
```

### Scénario 3: Analyse hebdomadaire
```
Shellia: "📈 **Stats Tickets - Semaine 3**

✅ Résolus: 45 tickets (+12% vs semaine dernière)
⏱️ Temps moyen: 18h (objectif: 24h) ✓
⭐ Satisfaction: 4.8/5

🔥 Top catégories:
1. Billing (40%)
2. Technical (30%)
3. Bug Report (20%)

💡 Recommandation: Créer un article FAQ sur les paiements"
```

---

## 🛡️ Privacy & Sécurité

### Isolation stricte (RLS)
```sql
-- Les users ne VOIENT QUE leurs propres tickets
CREATE POLICY user_ticket_isolation ON tickets
FOR SELECT USING (auth.uid() = user_id);
```

### Notes internes
```python
# Visible uniquement par les admins
await add_internal_note(
    ticket_id="TKT123",
    admin_id=999,
    note="Client difficile, être patient"
)
```

---

## 🔧 Intégration Discord

### Commandes disponibles
```
!ticket_create "Sujet" category priority description
!ticket_list [status]
!ticket_view <ticket_id>
!ticket_reply <ticket_id> <message>
!ticket_close <ticket_id> [resolution]
!ticket_stats
```

### Boutons (utiliser ButtonManager)
```python
# Placer un bouton "Créer un ticket" sur #support
await button_manager.create_button(
    type=ButtonType.TICKET_CREATE,
    channel_id=support_channel_id,
    style=ButtonStyle.PRIMARY
)
```

---

## 📊 KPIs à surveiller

- **Temps de première réponse** < 4h
- **Temps de résolution moyen** < SLA
- **Taux de satisfaction** > 4.5/5
- **Tickets non assignés** = 0
- **Tickets critiques ouverts** = 0

---

## 🎯 Auto-actions Shellia

```yaml
triggers:
  ticket_created:
    - Envoyer confirmation à l'utilisateur
    - Notifier le channel #admin-tickets
    - Si priorité=critical: mentionner @oncall
    
  sla_approaching:
    - Rappel aux agents 6h avant deadline
    - Escalade si dépassé
    
  ticket_closed:
    - Demander feedback (1-5 étoiles)
    - Archiver avec tags
    - Mettre à jour stats
```
