# 👑 Guide Administrateur Serveur - Shellia AI

Guide complet pour configurer et gérer Shellia AI sur votre serveur Discord.

---

## Table des matières

1. [Ajouter Shellia à votre serveur](#ajouter-shellia)
2. [Configuration des permissions](#configuration-permissions)
3. [Configuration des channels](#configuration-channels)
4. [Gestion des membres](#gestion-membres)
5. [Fonctionnalités avancées](#fonctionnalites-avancees)
6. [Monitoring et logs](#monitoring)

---

## Ajouter Shellia

### Invitation

1. Rendez-vous sur https://shellia.ai/invite
2. Sélectionnez votre serveur
3. Autorisez les permissions requises
4. Shellia rejoint votre serveur !

### Permissions requises

| Permission | Utilisation |
|------------|-------------|
| Lire messages | Répondre aux commandes |
| Envoyer messages | Répondre aux questions |
| Gérer messages | Modération auto |
| Joindre des salons vocaux | Fonctions vocales (future) |
| Lire historique | Contexte conversations |
| Mentionner everyone | Annonces admin |

---

## Configuration permissions

### Rôles recommandés

```
@Shellia Admin
- Gérer le bot
- Configurer les commandes
- Voir les logs admin

@Shellia Mod
- Modérer l'utilisation
- Voir les stats serveur
- Gérer les tickets

@Shellia User
- Utiliser le bot
- Créer des tickets
- Voir son historique
```

### Commandes admin

| Commande | Description | Permission |
|----------|-------------|------------|
| `/admin config` | Configurer le serveur | Admin |
| `/admin stats` | Voir les statistiques | Admin/Mod |
| `/admin restrict` | Restreindre un channel | Admin |
| `/admin allow` | Autoriser un channel | Admin |
| `/admin lock` | Verrouiller le serveur | Admin |
| `/admin unlock` | Déverrouiller | Admin |

---

## Configuration channels

### Channels spéciaux

**Channel général IA**
```
#shellia-chat
- Tout le monde peut poser des questions
- Shellia répond dans ce channel uniquement
- Logs des conversations
```

**Channel privé**
```
#shellia-private
- Réservé aux rôles spécifiques
- Pas de logs publics
- Parfait pour le staff
```

**Channel tickets**
```
#tickets
- Création automatique des tickets
- Un thread par ticket
- Staff uniquement peut voir
```

### Commande de restriction

```
/admin restrict #general
→ Shellia ne répondra plus dans #general

/admin allow #ia-channel
→ Shellia peut répondre dans #ia-channel
```

---

## Gestion membres

### Voir l'utilisation

```
/admin userstats @utilisateur

Résultat :
- Requêtes aujourd'hui : 15
- Total ce mois : 340
- Abonnement : Pro
- Dernière activité : il y a 2h
```

### Réinitialiser un quota

```
/admin resetquota @utilisateur
→ Réinitialise le quota quotidien de l'utilisateur
(Admin seulement)
```

### Bannir de l'utilisation

```
/admin block @utilisateur [raison]
→ L'utilisateur ne peut plus utiliser Shellia

/admin unblock @utilisateur
→ Débloque l'utilisateur
```

---

## Fonctionnalites avancees

### Verrouillage serveur (Emergency)

En cas de raid ou problème majeur :

```
/admin lock [raison]

Actions automatiques :
- Toutes les invitations révoquées
- Nouveaux membres kickés automatiquement
- Widget Discord désactivé
- Shellia en mode maintenance
```

Pour déverrouiller :
```
/admin unlock
```

### Webhooks personnalisés

```
/admin webhook create #annonces
→ Crée un webhook pour annonces automatisées
```

### Integration avec d'autres bots

Shellia fonctionne bien avec :
- **MEE6** : Pour les niveaux
- **Carl-bot** : Pour les rôles réactions
- **Dyno** : Pour la modération
- **Ticket Tool** : Pour les tickets avancés

---

## Monitoring

### Statistiques serveur

```
/admin stats

Affiche :
- Requêtes totales ce mois
- Utilisateurs actifs
- Moyenne requêtes/jour
- Top utilisateurs
- Abonnements sur le serveur
```

### Logs d'activité

```
/admin logs [date]

Affiche :
- Commandes utilisées
- Erreurs rencontrées
- Modifications de configuration
- Actions admin
```

### Export des données

```
/admin export [mois]
→ Génère un CSV avec toutes les stats
```

---

## Bonnes pratiques

### Configuration idéale

1. **Créez un channel dédié** à Shellia
2. **Limitez l'accès** si nécessaire avec les rôles
3. **Activez les logs** pour la modération
4. **Formez vos modos** sur les commandes admin
5. **Surveillez l'utilisation** pour éviter les abus

### Anti-spam

```
/admin antispam enable

Protection :
- Max 10 requêtes/minute par utilisateur
- Cooldown 5s entre requêtes
- Auto-kick après 5 avertissements
```

---

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Shellia ne répond pas | Vérifiez les permissions |
| Commande inconnue | Vérifiez le préfixe |
| Erreur permission | Promouvez Shellia dans la hiérarchie |
| Lenteur | Vérifiez l'état des serveurs avec `/status` |

---

## Contact admin

**Support technique :** support@shellia.ai  
**Urgences :** +33 1 XX XX XX XX (H24)  
**Documentation :** https://docs.shellia.ai/admin

---

**© 2026 Shellia AI - Administration & Sécurité**
