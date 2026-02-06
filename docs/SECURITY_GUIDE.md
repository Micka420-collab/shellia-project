# 🔒 Guide de Sécurité - Shellia AI

**Version :** 2.0  
**Classification :** PUBLIC - Document de sécurité  
**Date :** Février 2026

---

## Vue d'ensemble de la sécurité

Shellia AI met la sécurité et la confidentialité au coeur de son architecture. Ce document détaille nos pratiques de sécurité et vos responsabilités en tant qu'utilisateur.

---

## Architecture de sécurité

### Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE                           │
├─────────────────────────────────────────────────────────────┤
│  • Serveurs dédiés (pas de cloud public AWS/GCP/Azure)     │
│  • Localisation : France & Allemagne uniquement            │
│  • Accès physique sécurisé (datacenters Tier III+)         │
│  • Réseau isolé avec segmentation stricte                   │
└─────────────────────────────────────────────────────────────┘
```

### Chiffrement

| Couche | Méthode | Force |
|--------|---------|-------|
| Transport | TLS 1.3 | 256-bit |
| Stockage | AES-256-GCM | 256-bit |
| Base de données | Chiffrement colonne | 256-bit |
| Backups | AES-256 avec clés dérivées | 256-bit |

### Authentification

Nous utilisons Discord OAuth2 car c'est la méthode la plus sécurisée :

**Avantages :**
- Pas de stockage de mot de passe chez nous
- Tokens à durée limitée (7 jours max)
- Révocation instantanée possible
- Héritage de la 2FA Discord

---

## Protection des données

### Données collectées (minimalisme)

**Nous collectons UNIQUEMENT :**
- ID Discord (pour authentification)
- Nom d'utilisateur Discord
- Avatar Discord
- Email Discord
- Historique requêtes (30 jours max)

**Nous NE collectons PAS :**
- Nom réel
- Adresse postale
- Numéro de téléphone
- Données bancaires (Stripe les gère)
- Localisation GPS
- Historique navigation

### Cycle de vie des données

```
Création du compte
       ↓
Utilisation active
       ↓
30 jours d'inactivité → ALERTE email
       ↓
Suppression automatique des données personnelles
       ↓
Conservation anonymisée des stats (facultatif)
```

### Suppression des données

| Type de donnée | Délai de suppression |
|----------------|---------------------|
| Requêtes | 30 jours |
| Logs connexion | 30 jours |
| Données compte inactif | 30 jours après dernière connexion |
| Factures | 10 ans (obligation légale) |
| Backups | 90 jours |

---

## Conformité réglementaire

### RGPD (UE)

✅ Délégué à la Protection des Données (DPO) déclaré  
✅ Registre des traitements à jour  
✅ Droits utilisateurs implémentés (accès, rectification, effacement)  
✅ Notifications de violation sous 72h  
✅ Impact Privacy (PIA) réalisé  

### Certifications & Audits

- Audit de sécurité annuel par cabinet externe
- Tests de pénétration trimestriels
- Scan de vulnérabilités quotidiens
- Conformité PCI-DSS pour les paiements (via Stripe)

---

## Bonnes pratiques utilisateur

### Checklist de sécurité

- [ ] 2FA activée sur Discord
- [ ] Email avec 2FA
- [ ] Mot de passe Discord unique (pas de réutilisation)
- [ ] Sessions actives vérifiées régulièrement
- [ ] Navigateur à jour
- [ ] Anti-virus actif

### Signalement de problème

Si vous suspectez une compromission :

1. Changez mot de passe Discord IMMÉDIATEMENT
2. Révoquez toutes les sessions Shellia (dashboard)
3. Contactez security@shellia.ai
4. Vérifiez vos emails pour alertes de connexion

### Phishing - Comment reconnaître une tentative

❌ Nous ne demandons JAMAIS :
- Votre mot de passe Discord
- Vos codes 2FA
- Une connexion sur un site autre que shellia.ai
- Un paiement par virement bancaire direct

✅ Nos emails officiels viennent de :
- @shellia.ai
- @nextendo.fr

---

## Contact sécurité

**Email :** security@shellia.ai  
**DPO :** dpo@shellia.ai  
**Honeypot :** honeypot@shellia.ai (signalements anonymes)

**PGP Key :** [Télécharger la clé publique](https://shellia.ai/security/pgp.asc)

---

**© 2026 Shellia AI - Document confidentiel**
