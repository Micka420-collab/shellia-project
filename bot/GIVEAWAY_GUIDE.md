# 🎁 Guide du Système de Giveaways Automatiques

## 📖 Vue d'ensemble

Le système de **Giveaways Automatiques aux Paliers** récompense la communauté à chaque étape importante de croissance du serveur Discord.

### Comment ça marche ?

1. **Détection automatique** : Le bot surveille le nombre de membres
2. **Déclenchement** : Quand un palier est atteint, un giveaway se lance automatiquement
3. **Participation** : Les membres réagissent avec 🎉 pour participer
4. **Tirage au sort** : Les gagnants sont choisis automatiquement à la fin
5. **Récompenses** : Les prix sont distribués automatiquement

---

## 🎯 Paliers par Défaut

| Palier | Récompense | Gagnants | Durée |
|--------|-----------|----------|-------|
| **50** membres | 500 coins | 2 | 48h |
| **100** membres | 1000 coins | 3 | 72h |
| **250** membres | 2500 coins + Nitro | 1 | 96h |
| **500** membres | 5000 coins + Rôle OG | 5 | 120h |
| **1000** membres | 10000 coins + Nitro + Rôle légendaire | 10 | 168h |
| **2500** membres | 25000 coins + Nitro + Récompenses exclusives | 15 | 168h |
| **5000** membres | 50000 coins + Événement spécial | 25 | 336h |

---

## 👤 Commandes Utilisateur

### Voir les informations
```
!giveaway
```
Affiche :
- Le nombre actuel de membres
- Les prochains paliers à atteindre
- Les giveaways en cours

### Voir son solde
```
!balance
!bal
!coins
```
Affiche votre solde de coins.

### Voir le classement
```
!leaderboard
!lb
!top
```
Affiche le top 10 des utilisateurs les plus riches.

### Voir ses statistiques
```
!giveaway_stats [@utilisateur]
```
Affiche vos statistiques de participation aux giveaways.

---

## 🔧 Commandes Admin

### Forcer un giveaway
```
!giveaway_force <palier> [#canal]
```
Lance immédiatement un giveaway pour un palier spécifique.

**Exemples:**
```
!giveaway_force 100
!giveaway_force 50 #annonces
```

### Annuler un giveaway
```
!giveaway_cancel <id>
```
Annule un giveaway actif.

**Exemple:**
```
!giveaway_cancel abc12345
```

### Terminer un giveaway
```
!giveaway_end <id>
```
Termine un giveaway avant la fin et tire les gagnants.

### Retirer au sort de nouveaux gagnants
```
!giveaway_reroll <id> [nombre]
```
Si un gagnant ne réclame pas sa récompense, tire de nouveaux gagnants.

**Exemple:**
```
!giveaway_reroll abc12345 2
```

### Ajouter un palier personnalisé
```
!giveaway_add_milestone <membres> <gagnants> <durée_heures> [coins] <description>
```

**Exemple:**
```
!giveaway_add_milestone 75 2 24 250 "Palier bonus 75 membres !"
```

### Supprimer un palier
```
!giveaway_remove_milestone <membres>
```
Supprime un palier personnalisé (les paliers par défaut ne peuvent pas être supprimés).

### Lister les paliers
```
!giveaway_list
```
Affiche tous les paliers configurés avec leurs récompenses.

### Configurer le système
```
!giveaway_config [#canal_annonces]
```
Configure le canal où les annonces automatiques seront postées.

---

## 💰 Système d'Économie Virtuelle

### Gagner des coins

| Action | Récompense |
|--------|-----------|
| Gagner un giveaway | Variable (selon le palier) |
| Daily bonus | Bientôt disponible |
| Parrainage | Bientôt disponible |

### Utiliser les coins

Les coins pourront être utilisés pour :
- Acheter des rôles exclusifs
- Débloquer des fonctionnalités
- Participer à des giveaways spéciaux
- Échanger contre des avantages

---

## 🛡️ Sécurité

### Anti-triche
- Une participation par utilisateur par giveaway
- Vérification des doubles comptes
- Logs de toutes les actions

### Protection
- Seuls les administrateurs peuvent annuler/modifier
- Historique immuable des giveaways terminés
- Vérification des permissions Discord

---

## 📊 Base de Données

### Tables utilisées

```sql
-- Paliers configurés
giveaway_milestones

-- Paliers atteints
completed_milestones

-- Giveaways actifs
active_giveaways

-- Giveaways terminés
ended_giveaways

-- Économie utilisateurs
user_economy

-- Transactions
economy_transactions

-- Statistiques
giveaway_stats
```

---

## 🔧 Configuration

### Variables d'environnement

Aucune variable requise ! Le système fonctionne automatiquement.

### Configuration via commandes

1. **Configurer le canal d'annonces:**
   ```
   !giveaway_config #annonces
   ```

2. **Ajouter des paliers personnalisés:**
   ```
   !giveaway_add_milestone ...
   ```

3. **Vérifier la configuration:**
   ```
   !giveaway_list
   ```

---

## 📈 Statistiques

### Pour les utilisateurs
- Nombre de giveaways gagnés
- Total de coins gagnés
- Nombre de participations

### Pour les admins
- Total de giveaways organisés
- Nombre total de participants
- Taux d'engagement
- Récompenses distribuées

---

## 🎨 Personnalisation

### Modifier les récompenses par défaut

Éditez le fichier `auto_giveaway.py` :

```python
DEFAULT_MILESTONES = {
    50: MilestoneReward(
        member_count=50,
        currency_reward=1000,  # Modifier ici
        description="Votre message personnalisé",
        giveaway_duration_hours=48,
        winners_count=3  # Modifier ici
    ),
    # ...
}
```

### Ajouter des récompenses de rôle

```python
reward = MilestoneReward(
    member_count=100,
    role_reward=123456789,  # ID du rôle Discord
    description="Rôle spécial 100 membres !"
)
```

### Ajouter Nitro

```python
reward = MilestoneReward(
    member_count=500,
    nitro_reward=True,
    description="Giveaway Nitro !"
)
```

---

## 🐛 Dépannage

### Problème : Le giveaway ne se lance pas

**Solutions:**
1. Vérifier que le bot a les permissions `Manage Messages` et `Add Reactions`
2. Vérifier qu'il peut voir/envoyer des messages dans le canal
3. Vérifier les logs du bot

### Problème : Les réactions ne fonctionnent pas

**Solutions:**
1. Vérifier que le bot n'est pas en mode maintenance
2. Redémarrer le bot
3. Vérifier que le giveaway n'est pas déjà terminé

### Problème : Les récompenses ne sont pas distribuées

**Solutions:**
1. Vérifier la connexion à la base de données
2. Vérifier que les tables existent (exécuter `giveaway_schema.sql`)
3. Vérifier les logs d'erreur

---

## 📞 Support

En cas de problème :
1. Consulter les logs du bot
2. Vérifier la configuration
3. Contacter un administrateur

---

## 📝 Roadmap

### Fonctionnalités futures
- [ ] Système de niveaux basé sur l'activité
- [ ] Boutique avec les coins
- [ ] Giveaways quotidiens/hebdomadaires
- [ ] Intégration Twitch/YouTube
- [ ] Giveaways conditionnels (rôle, activité...)

---

**Amusez-vous et faites croître votre communauté !** 🎉🚀
