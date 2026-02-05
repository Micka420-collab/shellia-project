# 🎁 Mise à jour - Système de Giveaways Automatiques

**Date:** Février 2026  
**Version:** 2.1-GIVEAWAY  
**Statut:** ✅ FONCTIONNEL

---

## 🆕 Nouvelles Fonctionnalités

### Giveaways Automatiques aux Paliers
Le bot détecte automatiquement quand le serveur atteint certains nombres de membres et lance des giveaways automatiques !

### Paliers configurés:
| Palier | Récompense | Gagnants | Durée |
|--------|-----------|----------|-------|
| 50 | 500 coins | 2 | 48h |
| 100 | 1000 coins | 3 | 72h |
| 250 | 2500 coins + Nitro | 1 | 96h |
| 500 | 5000 coins + Rôle OG | 5 | 120h |
| 1000 | 10000 coins + Nitro | 10 | 168h |
| 2500 | 25000 coins | 15 | 168h |
| 5000 | 50000 coins | 25 | 336h |

---

## 📁 Nouveaux Fichiers

```
shellia-project/
├── bot/
│   ├── auto_giveaway.py          # Système principal
│   ├── giveaway_commands.py      # Commandes Discord
│   └── GIVEAWAY_GUIDE.md         # Documentation complète
├── deployment/
│   └── giveaway_schema.sql       # Tables base de données
└── tests/
    └── test_giveaway.py          # Tests automatisés
```

---

## 🚀 Installation

### 1. Mettre à jour la base de données

```bash
# Exécuter le script SQL
cd shellia-project
psql -U votre_user -d votre_db -f deployment/giveaway_schema.sql

# Ou via Supabase Dashboard
# Copier-coller le contenu de giveaway_schema.sql
```

### 2. Redémarrer le bot

```bash
# Arrêter le bot actuel
# Relancer
python bot/bot_secure.py
```

### 3. Configuration (optionnel)

```bash
# Configurer le canal d'annonces
!giveaway_config #annonces

# Vérifier les paliers
!giveaway_list
```

---

## 📝 Commandes Disponibles

### Utilisateur
```
!giveaway          - Voir les infos giveaways
!balance           - Voir son solde
!leaderboard       - Classement
!giveaway_stats    - Ses statistiques
```

### Admin
```
!giveaway_force <palier> [#canal]    - Forcer un giveaway
!giveaway_cancel <id>                - Annuler
!giveaway_end <id>                   - Terminer
!giveaway_reroll <id> [nombre]       - Retirer au sort
!giveaway_add_milestone ...          - Ajouter palier
!giveaway_remove_milestone <palier>  - Supprimer
!giveaway_list                       - Lister
!giveaway_config [#canal]            - Configurer
```

---

## ⚙️ Fonctionnement

### 1. Détection automatique
- Le bot vérifie toutes les 5 minutes le nombre de membres
- Quand un palier est atteint → Giveaway lancé automatiquement

### 2. Participation
- Les membres cliquent sur 🎉 sur le message
- Une seule participation par personne
- Confirmation en MP

### 3. Tirage au sort
- Automatique à la fin du temps imparti
- Ou manuel avec `!giveaway_end`

### 4. Récompenses
- Distribution automatique des coins
- Attribution des rôles
- MP aux gagnants

---

## 🎨 Personnalisation

### Ajouter un palier personnalisé
```python
# Dans auto_giveaway.py, ajouter à DEFAULT_MILESTONES
150: MilestoneReward(
    member_count=150,
    currency_reward=1500,
    description="Palier bonus 150 !",
    giveaway_duration_hours=48,
    winners_count=2
)
```

### Modifier les récompenses existantes
```python
# Modifier le palier 50
50: MilestoneReward(
    member_count=50,
    currency_reward=1000,  # Au lieu de 500
    description="Message personnalisé",
    giveaway_duration_hours=72,  # Au lieu de 48
    winners_count=3  # Au lieu de 2
)
```

---

## 🛡️ Sécurité

- ✅ Une participation par utilisateur
- ✅ Vérification anti-double compte
- ✅ Logs complets
- ✅ Permissions admin requises pour les commandes sensibles

---

## 📊 Base de Données

### Tables créées:
- `giveaway_milestones` - Configuration des paliers
- `completed_milestones` - Paliers déjà atteints
- `active_giveaways` - Giveaways en cours
- `ended_giveaways` - Giveaways terminés (archive)
- `user_economy` - Solde des utilisateurs
- `economy_transactions` - Historique des transactions
- `giveaway_stats` - Statistiques globales

---

## 🧪 Tests

```bash
# Lancer les tests
cd shellia-project
pytest tests/test_giveaway.py -v

# Couverture
pytest tests/test_giveaway.py --cov=bot --cov-report=html
```

---

## 🎯 Roadmap

### Prochaines fonctionnalités:
- [ ] Daily bonus pour les connexions quotidiennes
- [ ] Boutique avec les coins gagnés
- [ ] Système de niveaux basé sur l'activité
- [ ] Giveaways conditionnels (par rôle, activité...)
- [ ] Intégration Twitch/YouTube

---

## 🐛 Dépannage

### Le giveaway ne se lance pas
1. Vérifier les permissions du bot
2. Vérifier les logs
3. S'assurer que les tables SQL sont créées

### Les réactions ne fonctionnent pas
1. Redémarrer le bot
2. Vérifier que le giveaway est bien actif

---

## 📞 Support

Voir `bot/GIVEAWAY_GUIDE.md` pour la documentation complète.

---

**🎉 Amusez-vous et faites croître votre communauté !**
