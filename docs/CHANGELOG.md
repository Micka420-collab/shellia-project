# 📝 Changelog - Shellia AI

Toutes les modifications notables de ce projet seront documentées ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/lang/fr/).

---

## [2.0.0] - 2026-02-04

### Ajouté

#### E-commerce complet
- Système de boutique avec panier
- Intégration Stripe pour paiements
- 4 plans d'abonnement (Free, Pro, Ultra, Founder)
- Précommandes avec Early Bird et Founder
- Système de codes promo

#### Système de giveaways
- Giveaways automatiques aux paliers de membres
- Grade "Winner" avec accès Pro 3 jours

#### Marketing et communauté
- 7 grades marketing (Ambassador, Influencer, Creator, etc.)
- Grade spécial "Founder"
- Compte à rebours automatique pour l'ouverture
- Recaps hebdomadaires automatiques le lundi

#### Support client
- Système de tickets avec commandes Discord
- Dashboard web de gestion des tickets
- Tickets isolés par utilisateur

#### Outils de gestion
- Button Manager pour créer des boutons stylisés
- Embed Manager (Humbles) pour embeds avec paiements
- Système d'affiliation 5 niveaux (Bronze à Diamond)
- Server Lock pour verrouiller le serveur

#### Quotas et utilisation
- Quota quotidien 50/jour (Free)
- Quota quotidien illimité (Pro/Ultra/Founder)
- Quota achetable qui n'expire jamais
- Dashboard utilisateur complet

#### Sécurité et conformité
- Architecture double VM (Shellia + Maxis)
- Authentification Discord OAuth2 via Supabase
- Chiffrement AES-256-GCM
- Conformité RGPD complète
- Politique de confidentialité
- Conditions d'utilisation
- Politique des cookies
- Page des droits RGPD

#### Site web
- Landing page moderne (index)
- Page fonctionnalités
- Page tarifs
- Page communauté
- Page à propos
- Design responsive avec animations

#### Documentation
- Guide de démarrage rapide
- Guide utilisateur complet
- Guide de sécurité
- FAQ
- Guide administrateur serveur
- Documentation API complète
- Guide RGPD

#### Architecture technique
- Dual-VM : Shellia (controller) + Maxis (executor)
- Communication API entre VMs sur port 8080
- Supabase avec RLS activé
- Rate limiting
- Audit trails

### Modifié

- Refonte complète de l'architecture
- Migration vers architecture microservices
- Amélioration des performances de l'IA

### Sécurité

- Mise en place du CSP (Content Security Policy)
- SRI (Subresource Integrity) sur tous les assets
- Protection contre la pollution de prototype
- Audit de sécurité externe (Score: 9.3/10)

---

## [1.5.0] - 2025-12-15

### Ajouté
- Intégration Google Gemini API
- Système de contexte par serveur
- Commandes slash Discord

### Modifié
- Amélioration des réponses IA
- Optimisation des temps de réponse

### Corrigé
- Bug de réponse en double
- Problème de timeout sur longues requêtes

---

## [1.4.0] - 2025-11-01

### Ajouté
- Support multi-langues
- Historique des conversations
- Export des données utilisateur

---

## [1.3.0] - 2025-09-20

### Ajouté
- Intégration base de données Supabase
- Système de logs
- Monitoring des erreurs

---

## [1.2.0] - 2025-08-10

### Ajouté
- Authentification Discord
- Système de permissions
- Commandes administrateur

---

## [1.1.0] - 2025-07-01

### Ajouté
- Rate limiting basique
- Gestion des erreurs
- Logs de base

---

## [1.0.0] - 2025-06-01

### Ajouté
- Version initiale
- Bot Discord basique
- Intégration IA simple
- Réponses en texte

---

## Types de changements

- `Ajouté` pour les nouvelles fonctionnalités
- `Modifié` pour les changements de fonctionnalités existantes
- `Déprécié` pour les fonctionnalités qui seront bientôt supprimées
- `Corrigé` pour les corrections de bugs
- `Sécurité` pour les correctifs de sécurité
- `Supprimé` pour les fonctionnalités supprimées

---

**© 2026 Shellia AI - Powered by NEXTENDO**
