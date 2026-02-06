# 🤖 MAXIS + 🧠 SHELLIA - Architecture Dual-VM

```
┌─────────────────────┐         ┌─────────────────────┐
│   🧠 SHELLIA        │  ←──→   │    🤖 MAXIS         │
│   (Contrôleur IA)   │   API   │  (E-commerce Bot)   │
│                     │         │                     │
│  • Intelligence     │         │  • Shop             │
│  • Stratégie        │         │  • Paiements        │
│  • Décisions        │         │  • Giveaways        │
│  • Contrôle Maxis   │         │  • Tickets Support  │
└─────────────────────┘         └─────────────────────┘
       VM 1                           VM 2
```

## 🎯 Architecture

**Shellia** (VM 1) est l'IA contrôleur qui pilote **Maxis** (VM 2) via une API sécurisée.

### 🎫 Système de Tickets Support (NOUVEAU)
- **Création** : Utilisateurs créent des tickets via Discord (`!ticket_create`)
- **Isolation stricte** : Chaque utilisateur ne voit QUE ses propres tickets (Privacy by Design)
- **Gestion** : Admins gèrent via Discord (`!ticket_list`, `!ticket_assign`) ET Dashboard Web
- **Stockage** : Supabase avec RLS (Row Level Security)
- **Notifications** : Temps réel pour nouveaux tickets et réponses

### Privacy by Design - Isolation des Données
Chaque utilisateur est traité dans sa propre session isolée :
- Jean ne peut PAS voir les tickets de Marie
- Les messages internes (admin) sont invisibles pour les utilisateurs
- Les données sont strictement séparées en base (RLS)

## 🚀 Déploiement Rapide

### Prérequis
- 2 VMs (ou 1 VM avec 2 conteneurs)
- Docker sur chaque VM
- Clés API Discord

### VM 1 - Shellia (Contrôleur)
```bash
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# Configurer
export SHELLIA_DISCORD_TOKEN=votre_token
export MAXIS_API_KEY=cle_secrete

# Lancer
python shellia_controller.py
```

### VM 2 - Maxis (E-commerce)
```bash
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# Configurer
export MAXIS_DISCORD_TOKEN=votre_token
export MAXIS_API_KEY=cle_secrete

# Lancer
docker-compose up -d
```

## 🎮 Commandes

### Contrôler Maxis (via Shellia)
```
!maxis status           → Voir état de Maxis
!maxis analytics        → Statistiques
!maxis promo ...        → Lancer promotion
!maxis giveaway         → Lancer giveaway
```

### Utiliser Maxis (direct)
```
/shop                   → Boutique
/plans                  → Voir les plans
/giveaway               → Participer giveaway

🎫 Tickets Support:
!ticket_create <sujet> <description>  → Créer un ticket
!ticket_list                          → Voir mes tickets
!ticket_view <id>                     → Voir détails ticket
!ticket_reply <id> <message>          → Répondre
!ticket_close <id>                    → Fermer un ticket
```

### Admin (Discord + Web)
```
!ticket_assign <id> @admin     → Assigner ticket
!ticket_stats                  → Stats tickets
```

Dashboard Web : `https://votre-domaine/admin-panel/tickets.html`

## 📁 Structure

```
shellia-project/
├── shellia_controller.py      # VM 1 - Contrôleur
├── maxis_bot.py               # VM 2 - Bot principal
├── maxis_ticket_system.py     # 🎫 Système de tickets
├── ticket_api.py              # API REST tickets
├── ticket_commands.py         # Commandes Discord tickets
├── maxis_api.py               # API de contrôle
├── deployment/
│   ├── tickets_schema.sql     # 🎫 Schéma SQL tickets
│   └── ...
├── admin-panel/
│   ├── tickets.html           # 🎫 Dashboard tickets
│   └── ...
└── ...
```

## 🔧 Configuration

Créer un fichier `.env` sur chaque VM :

### VM 1 (Shellia)
```env
SHELLIA_DISCORD_TOKEN=xxx
MAXIS_API_URL=http://maxis-vm:8080/api
MAXIS_API_KEY=cle_secrete_commune
```

### VM 2 (Maxis)
```env
MAXIS_DISCORD_TOKEN=xxx
MAXIS_API_KEY=cle_secrete_commune
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
STRIPE_SECRET_KEY=xxx
```

## 🎫 Système de Tickets - Fonctionnalités

### Pour les Utilisateurs
| Commande | Description |
|----------|-------------|
| `!ticket_create` | Créer un nouveau ticket |
| `!ticket_list` | Voir mes tickets |
| `!ticket_view <id>` | Voir les détails |
| `!ticket_reply <id>` | Répondre |
| `!ticket_close <id>` | Fermer |

### Pour les Admins (Discord)
| Commande | Description |
|----------|-------------|
| `!ticket_assign <id> @user` | Assigner à un admin |
| `!ticket_stats` | Statistiques |

### Pour les Admins (Web)
- Dashboard complet avec stats
- Liste des tickets avec filtres (statut, priorité, catégorie)
- Vue détaillée avec historique des messages
- Réponse directe (avec option "note interne")
- Assignation et changement de priorité
- Fermeture de tickets

### Catégories de Tickets
- ❓ **Général** - Questions diverses
- 💳 **Facturation** - Problèmes de paiement
- 🔧 **Technique** - Support technique
- 🐛 **Bug** - Signalement de bugs
- 👤 **Compte** - Gestion de compte
- 💡 **Suggestion** - Demandes de fonctionnalités

### Priorités
- 🔴 **Critique** - Résolution sous 12h
- 🟠 **Haute** - Résolution sous 24h
- 🟡 **Moyenne** - Résolution sous 48h
- ⚪ **Basse** - Résolution sous 72h

## 📚 Documentation

- `ARCHITECTURE.md` - Architecture détaillée
- `DEPLOY_DUAL_VM.md` - Guide déploiement complet
- `SHELLIA_INSTRUCTIONS.md` - Instructions pour Shellia

## 🛡️ Sécurité

- Clé API entre VMs
- HTTPS/TLS recommandé
- IP Whitelist possible
- Rate limiting intégré
- **Isolation stricte** des tickets (RLS Supabase)

## 📞 Support

En cas de problème :
1. Vérifier `!maxis status`
2. Voir les logs sur les 2 VMs
3. Vérifier la connexion réseau entre VMs

---

**Maxis** = Bot E-commerce  
**Shellia** = IA Contrôleur  
**Version** : 2.1-DUAL-VM+TICKETS
