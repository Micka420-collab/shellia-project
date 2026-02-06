# 📚 Shellia AI - Skills Index

**Version:** 1.0.0  
**Dernière mise à jour:** 2026-02-06

Ce document est l'index central de toutes les compétences (skills) de Shellia AI. Chaque skill est documentée dans un fichier séparé et contient les informations nécessaires pour que Shellia puisse utiliser efficacement chaque système.

---

## 🗺️ Skills Disponibles

| Skill | Description | Fichier | Priorité |
|-------|-------------|---------|----------|
| 🎫 **Ticketing** | Gestion des tickets support avec isolation utilisateur | `SKILL_TICKETING.md` | Haute |
| 📢 **Marketing** | Rôles communautaires, affiliés, événements | `SKILL_MARKETING.md` | Haute |
| 🎁 **Giveaways** | Système de giveaways automatiques par paliers | `SKILL_GIVEAWAYS.md` | Moyenne |
| 🛍️ **E-commerce** | Boutique, plans, paiements, précommandes | `SKILL_ECOMMERCE.md` | Haute |
| 📅 **Weekly Recap** | Rapports hebdomadaires automatisés | `SKILL_WEEKLY_RECAP.md` | Moyenne |
| 🔘 **Button Manager** | Création de boutons Discord stylés | `SKILL_BUTTONS.md` | Moyenne |
| 📦 **Embeds** | Builder d'embeds avec paiement intégré (style MEE6) | `SKILL_EMBEDS.md` | Haute |
| 🤝 **Affiliation** | Programme d'affiliation complet | `SKILL_AFFILIATION.md` | Haute |
| 📊 **Quota** | Gestion des quotas avec achat Stripe | `SKILL_QUOTA.md` | Haute |
| 🔒 **Server Lock** | Verrouillage complet du serveur | `SKILL_SERVER_LOCK.md` | Haute |

---

## 🔌 Architecture API

Toutes les skills communiquent avec Maxis (le bot Discord) via l'API interne:

```
┌─────────────┐     HTTP/REST      ┌─────────────┐
│   Shellia   │ ◄────────────────► │    Maxis    │
│  (Controller│    Port 8080       │  (Executor) │
│    AI)      │                    │   Discord   │
└─────────────┘                    └─────────────┘
       │                                  │
       │       ┌──────────────┐           │
       └──────►│   Supabase   │◄──────────┘
               │  PostgreSQL  │
               └──────────────┘
```

### Base URL
```
http://localhost:8080/api/
```

### Authentification
```
Authorization: Bearer {DISCORD_BOT_TOKEN}
X-API-Key: {SHELLIA_API_KEY}
```

---

## 🎯 Quick Reference - Actions Shellia

### Actions Quotidiennes Automatiques
```yaml
morning_check:
  - Vérifier tickets en attente > 24h
  - Vérifier giveaways qui se terminent aujourd'hui
  - Vérifier précommandes expirantes
  - Post daily recap si activé

afternoon_check:
  - Analyser métriques support
  - Identifier upsell opportunities
  - Répondre aux tickets automatiques

evening_check:
  - Générer rapports journaliers
  - Backup logs importants
  - Planifier actions lendemain
```

### Actions Hebdomadaires (Lundi 9h)
```yaml
weekly_recap:
  - Collecter métriques semaine
  - Analyser avec Gemini
  - Post recap channel admin
  - Identifier objectifs semaine
```

### Actions Mensuelles
```yaml
monthly_report:
  - Rapport financier complet
  - Analyse cohortes utilisateurs
  - Review churn & retention
  - Recommandations stratégiques
```

---

## 🚨 Alertes Automatiques

Shellia doit immédiatement alerter quand:

| Condition | Action | Canal |
|-----------|--------|-------|
| Ticket Critical ouvert > 6h | Mention @Support + DM Lead | #admin-alerts |
| Giveaway erreur lors du tirage | Créer ticket + Notifier | #admin-alerts |
| Paiement Stripe échoué | DM user + Flag account | DM + #billing |
| SLA support dépassé > 50% | Rapport quotidien | #admin |
| Churn > 10% sur 7j | Alerte + Analyse | #admin-alerts |
| Erreur API > 100/h | Alerte technique | #dev-alerts |
| Member milestone atteint | Annonce giveaway | #general |

---

## 📝 Templates de Réponse Shellia

### Confirmation Action
```
✅ **[Action] effectuée avec succès !**

📋 **Détails:**
[Details spécifiques]

⏱️ **Prochaines étapes:**
[Actions suivantes]

Besoin d'aide ? Mentionnez-moi !
```

### Alerte Problème
```
⚠️ **Attention requise**

[Description du problème]

🔧 **Actions recommandées:**
1. [Action 1]
2. [Action 2]

⏰ **Deadline:** [Quand]

Cc: [Personnes concernées]
```

### Rapport Positif
```
🎉 **Excellent résultat !**

[Métrique positive avec comparaison]

🏆 **Contributions remarquables:**
- [Personne 1]: [Action]
- [Personne 2]: [Action]

Continuons sur cette lancée ! 💪
```

---

## 🔗 Liens Utiles

| Ressource | URL |
|-----------|-----|
| Dashboard Admin | https://shellia.ai/admin |
| API Documentation | https://shellia.ai/api/docs |
| Stripe Dashboard | https://dashboard.stripe.com |
| Supabase Console | https://app.supabase.com |
| Discord Dev Portal | https://discord.com/developers |

---

## 🆕 Changelog

### v1.2.0 (2024-01-20)
- ✅ **Skill Quota** - Achat de quotas via Stripe (rentabilité optimisée)
- ✅ **Skill Server Lock** - Fermeture complète du serveur
- ✅ **User Dashboard** - Espace utilisateur complet
- ✅ **Quota Packages** - 6 niveaux avec prix dégressifs

### v1.1.0 (2024-01-20)
- ✅ **Skill Affiliation** - Programme complet avec tiers
- ✅ **Skill Embeds** - Builder MEE6-style avec paiement
- ✅ **Admin Pages** - affiliates.html + embeds.html
- ✅ **Backend** - affiliate_manager.py + embed_manager.py

### v1.0.0 (2024-01-20)
- ✅ Création initiale des skills
- ✅ Documentation ticketing complète
- ✅ Documentation marketing
- ✅ Documentation giveaways
- ✅ Documentation e-commerce
- ✅ Documentation weekly recap
- ✅ Système de boutons Discord

### Roadmap v1.2.0
- [ ] Skill Analytics avancées
- [ ] Skill Modération auto
- [ ] Skill Onboarding utilisateur
- [ ] Skill Content Generation

---

## 👥 Contribution

Pour ajouter/modifier une skill:
1. Créer fichier `SKILL_[NOM].md`
2. Suivre le template existant
3. Mettre à jour cet index
4. Tester avec Shellia

---

**© 2026 Shellia AI - Tous droits réservés**
