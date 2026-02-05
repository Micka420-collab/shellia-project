# 🤖 GUIDE COMPLET POUR SHELLIA - Déploiement VM & Bot

**Objectif:** Créer une VM et déployer le projet Shellia AI Bot avec toutes les fonctionnalités
**Repository:** https://github.com/Micka420-collab/shellia-project.git  
**Version:** 2.1-OPENCLOW-PLUS (Production Ready)  
**Date:** Février 2026

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble du projet](#vue-densemble)
2. [Architecture complète](#architecture)
3. [Spécifications VM](#specifications-vm)
4. [Installation étape par étape](#installation)
5. [Configuration des services externes](#configuration-externe)
6. [Configuration du bot](#configuration-bot)
7. [Déploiement Docker](#deploiement-docker)
8. [Configuration des nouvelles fonctionnalités](#configuration-nouveautes)
9. [Vérification du déploiement](#verification)
10. [Commandes de gestion](#commandes-gestion)
11. [Dépannage](#depannage)
12. [Maintenance](#maintenance)

---

## 1. VUE D'ENSEMBLE

### Qu'est-ce que Shellia AI ?

**Shellia AI v2.1** est un écosystème Discord e-commerce complet avec :

#### 🤖 Bot Discord
- IA conversationnelle (Google Gemini)
- Génération d'images avec quotas
- Système de plans (Free, Pro, Ultra)
- Paiements Stripe
- Parrainage et fidélité

#### 🦀 OpenClaw (Business Automation)
- Analytics business (MRR, ARPU, conversion, churn)
- Promotions automatiques (welcome, winback, upsell)
- Giveaways intelligents avec ROI tracking
- Récupération clients inactifs

#### 🎁 Giveaways Automatiques
- Détection paliers membres (50, 100, 250, 500, 1000+)
- Grade Winner avec Pro gratuit
- Système d'économie virtuelle

#### 🛍️ NOUVEAU : Système de Pré-achat
- **Tiers Early Bird** (-30%), Founder (-20%), Supporter (-10%)
- Annonces automatiques avec compte à rebours
- Social proof (annonces d'achats)
- Urgence marketing ("plus que X places")

#### 🎭 NOUVEAU : Rôles Marketing
- **Ambassadeur** - Parrainage et représentation
- **Influenceur** - Création de contenu
- **Créateur** - Visuels et médias
- **Helper** - Support communauté
- **Event Host** - Organisation événements
- **Beta Tester** - Tests features
- **Partenaire** - Partenariats officiels

#### 🎊 NOUVEAU : Ouverture Officielle
- Lancement automatisé avec l'IA
- Annonces aux milestones (T-7j, T-3j, T-24h, T-1h, T-0)
- Compte à rebours visuel
- Remerciements early adopters

#### 📊 NOUVEAU : Récap Hebdomadaire Admin
- Analyse IA des métriques
- Recommandations automatiques
- Envoi tous les lundis matin
- Tous les KPIs (argent, marketing, communauté)

#### 🔐 Sécurité Enterprise
- Score 9.3/10
- Encryption AES-256-GCM
- OAuth2 + PKCE
- Protection avancée (CSP, SRI, etc.)

---

## 2. ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VM OPENCLOW                                     │
│                        Ubuntu 22.04 LTS + Docker                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         DOCKER COMPOSE                              │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │   │
│  │  │  🤖 BOT     │  │  🔄 REDIS   │  │  🌐 NGINX (optionnel)       │  │   │
│  │  │  Python     │  │  Cache      │  │  Dashboard Admin            │  │   │
│  │  │  3.11       │  │  Rate Limit │  │                             │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────┬───────────────┘  │   │
│  │         │                │                       │                  │   │
│  │         └────────────────┼───────────────────────┘                  │   │
│  │                          │                                          │   │
│  │  MODULES INTERNES:       │                                          │   │
│  │  • OpenClaw Manager      │                                          │   │
│  │  • Preorder System       │                                          │   │
│  │  • Marketing Roles       │                                          │   │
│  │  • Grand Opening         │                                          │   │
│  │  • Weekly Recap          │                                          │   │
│  │  • Giveaway System       │                                          │   │
│  │  • Security Integration  │                                          │   │
│  └──────────────────────────┼──────────────────────────────────────────┘   │
│                             │                                               │
│                             ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     SUPABASE (PostgreSQL Cloud)                     │   │
│  │  • 20+ tables avec RLS                                             │   │
│  │  • Auth + Storage                                                  │   │
│  │  • Realtime subscriptions                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SERVICES EXTERNES:                                                         │
│  • Discord API      • Stripe API      • Google Gemini API                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SPÉCIFICATIONS VM

### Configuration recommandée

```yaml
VM Specifications:
  OS: Ubuntu 22.04 LTS (64-bit)
  CPU: 2-4 vCPU (4 recommandé pour production)
  RAM: 4-8 GB (8 GB recommandé)
  Disk: 30 GB SSD minimum (50 GB recommandé)
  
Network:
  Ports entrants:
    - 22/tcp   (SSH)
    - 80/tcp   (HTTP - optionnel si web)
    - 443/tcp  (HTTPS - optionnel si web)
  Sortant: Tout (HTTPS requis pour APIs)
  
Software Stack:
  - Docker 24.0+
  - Docker Compose 2.20+
  - Git
  - UFW (firewall)
  - Fail2ban (sécurité)
```

### Providers recommandés

| Provider | Prix/mois | Facilité | Lien |
|----------|-----------|----------|------|
| **OpenClaw** | Variable | ⭐⭐⭐⭐⭐ | Ton infrastructure |

---

## 4. INSTALLATION ÉTAPE PAR ÉTAPE

### Étape 1: Créer la VM

```bash
# Se connecter à OpenClaw / Provider
# Créer une VM avec Ubuntu 22.04 LTS
# Configurer: 2-4 vCPU, 4-8 GB RAM, 50 GB SSD

# Se connecter en SSH
ssh root@IP_DE_LA_VM

# OU si utilisateur créé
ssh username@IP_DE_LA_VM
```

### Étape 2: Mise à jour système et installation

```bash
# Mettre à jour
apt update && apt upgrade -y

# Installer les dépendances
apt install -y \
    curl \
    wget \
    git \
    nano \
    vim \
    htop \
    net-tools \
    ufw \
    fail2ban \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Installer Docker Compose
apt install -y docker-compose-plugin

# Vérifier installations
docker --version
docker compose version

# Activer Docker au démarrage
systemctl enable docker
systemctl start docker

# Optionnel: ajouter utilisateur au groupe docker
usermod -aG docker $USER
# Se déconnecter et reconnecter
```

### Étape 3: Configuration sécurité (IMPORTANT)

```bash
# Configurer UFW (firewall)
ufw default deny incoming
ufw default allow outgoing

# Autoriser les ports nécessaires
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP (si web)
ufw allow 443/tcp  # HTTPS (si web)

# Activer firewall
ufw --force enable

# Vérifier
ufw status verbose

# Configurer Fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### Étape 4: Cloner le repository

```bash
# Créer le répertoire
mkdir -p /opt
cd /opt

# Cloner le projet
git clone https://github.com/Micka420-collab/shellia-project.git

# Entrer dans le répertoire
cd shellia-project

# Vérifier la structure
ls -la
```

**Structure attendue:**
```
/opt/shellia-project/
├── bot/                           # Code du bot
│   ├── bot_secure.py
│   ├── openclaw_manager.py
│   ├── preorder_system.py         # NOUVEAU
│   ├── marketing_roles.py         # NOUVEAU
│   ├── grand_opening.py           # NOUVEAU
│   ├── weekly_admin_recap.py      # NOUVEAU
│   ├── marketing_commands.py      # NOUVEAU
│   ├── auto_giveaway.py
│   └── ...
├── admin-panel/                   # Dashboard web
├── deployment/                    # Scripts & SQL
├── docs/                          # Documentation
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── SHELLIA_GUIDE.md              # Ce guide
```

---

## 5. CONFIGURATION DES SERVICES EXTERNES

Avant de configurer le bot, tu dois créer des comptes sur:

### 5.1 Discord Developer Portal

1. Aller sur https://discord.com/developers/applications
2. "New Application" → Nom: "Maxis"
3. Dans "Bot" → "Add Bot"
4. Copier le **TOKEN** (garder secret !)
5. Activer les intents:
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
6. Dans "OAuth2" → "General":
   - Copier **CLIENT ID**
   - Copier **CLIENT SECRET**

### 5.2 Supabase

1. Aller sur https://supabase.com
2. "New Project" → Nom: "shellia-ai"
3. Attendre la création
4. Dans "Project Settings" → "API":
   - Copier **URL** (SUPABASE_URL)
   - Copier **service_role key** (SUPABASE_KEY)
   - Copier **anon key** (SUPABASE_ANON_KEY)

### 5.3 Google Gemini

1. Aller sur https://ai.google.dev/
2. "Get API Key"
3. Créer une clé
4. Copier la **GEMINI_API_KEY**

### 5.4 Stripe

1. Aller sur https://dashboard.stripe.com
2. Compte recommandé: commencer en TEST mode
3. Dans "Developers" → "API keys":
   - Copier **Secret key** (STRIPE_SECRET_KEY)
4. Dans "Developers" → "Webhooks":
   - Créer un endpoint: `https://votre-domaine/webhook/stripe`
   - Sélectionner tous les événements
   - Copier le **Signing secret** (STRIPE_WEBHOOK_SECRET)
5. Clé publique (STRIPE_PUBLISHABLE_KEY) pour le dashboard

---

## 6. CONFIGURATION DU BOT

### Étape 6: Créer le fichier .env

```bash
cd /opt/shellia-project

# Copier le template
cp .env.example .env

# Éditer
nano .env
```

### Configuration complète (.env)

```env
# ============================================
# 🤖 DISCORD CONFIGURATION
# ============================================
DISCORD_TOKEN=votre_token_discord_bot_ici
DISCORD_CLIENT_ID=votre_client_id_ici
DISCORD_CLIENT_SECRET=votre_client_secret_ici
DISCORD_REDIRECT_URI=https://votre-domaine.com/callback

# ============================================
# 🗄️ SUPABASE CONFIGURATION
# ============================================
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_cle_service_role_ici
SUPABASE_ANON_KEY=votre_cle_anon_ici

# ============================================
# 🧠 GOOGLE GEMINI CONFIGURATION
# ============================================
GEMINI_API_KEY=votre_cle_gemini_ici

# ============================================
# 💳 STRIPE CONFIGURATION
# ============================================
STRIPE_SECRET_KEY=sk_test_...ou_sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...ou_pk_live_...

# ============================================
# 🔐 SECURITY CONFIGURATION
# ============================================
# Générer: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=votre_cle_fernet_base64_ici=

# Clé secrète (32+ caractères aléatoires)
SECRET_KEY=votre_cle_secrete_tres_longue_et_aleatoire_ici_min_32_chars

# ============================================
# 🦀 OPENCLOW CONFIGURATION
# ============================================
OPENCLOW_MODE=full
OPENCLOW_VM_ID=shellia-vm-prod

# Objectifs business
TARGET_MRR=5000
TARGET_CONVERSION_RATE=0.05
MAX_CAC=50

# ============================================
# 🎁 GIVEAWAY CONFIGURATION
# ============================================
GIVEAWAY_ENABLED=true
WINNER_PLAN_DURATION_DAYS=3
WINNER_PLAN_TYPE=pro

# ============================================
# 🛍️ PREORDER CONFIGURATION (NOUVEAU)
# ============================================
PREORDER_ENABLED=true
PREORDER_CHANNEL_ID=           # À remplir après création du channel

# ============================================
# 🎭 MARKETING ROLES CONFIGURATION (NOUVEAU)
# ============================================
MARKETING_ROLES_ENABLED=true

# ============================================
# 🎊 GRAND OPENING CONFIGURATION (NOUVEAU)
# ============================================
GRAND_OPENING_ENABLED=true
OPENING_DATE=2026-02-15 18:00:00  # Format: YYYY-MM-DD HH:MM:SS

# ============================================
# 📊 WEEKLY RECAP CONFIGURATION (NOUVEAU)
# ============================================
WEEKLY_RECAP_ENABLED=true
RECAP_DAY=0   # 0=Lundi, 6=Dimanche
RECAP_HOUR=9  # 9h du matin

# ============================================
# 🔄 REDIS CONFIGURATION
# ============================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# ============================================
# 📊 MONITORING
# ============================================
LOG_LEVEL=INFO
ENABLE_METRICS=true
METRICS_PORT=9090

# ============================================
# 🌐 ENVIRONMENT
# ============================================
ENVIRONMENT=production
DEBUG=false
```

**Générer la clé Fernet:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 7. DÉPLOIEMENT DOCKER

### Étape 7: Initialiser la base de données

```bash
# Se connecter au Dashboard Supabase
# Aller dans "SQL Editor"
# Exécuter les scripts dans cet ORDRE:

# 1. Tables principales
cat deployment/supabase_schema.sql | copier-coller

# 2. Authentification
cat deployment/auth_schema.sql | copier-coller

# 3. Sécurité
cat deployment/security_schema.sql | copier-coller

# 4. Giveaways
cat deployment/giveaway_schema.sql | copier-coller

# 5. OpenClaw / Business
cat deployment/openclaw_schema.sql | copier-coller

# 6. Scheduler
cat deployment/scheduler_schema.sql | copier-coller

# 7. NOUVEAU: Preorder
cat deployment/preorder_schema.sql | copier-coller

# 8. NOUVEAU: Marketing Roles
cat deployment/marketing_roles_schema.sql | copier-coller

# 9. NOUVEAU: Grand Opening
cat deployment/grand_opening_schema.sql | copier-coller

# 10. NOUVEAU: Weekly Recap
cat deployment/weekly_recap_schema.sql | copier-coller
```

### Étape 8: Lancer avec Docker Compose

```bash
cd /opt/shellia-project

# Pull des images (première fois)
docker compose pull

# Build et démarrage
docker compose up -d --build

# Vérifier les logs
# Attendre 30-60 secondes pour le démarrage
docker compose logs -f bot
```

**Signes que tout fonctionne:**
```
✅ Bot connecté: Shellia AI#1234
✅ Sécurité initialisée
✅ OpenClaw Manager initialisé
✅ PreorderMarketingSystem initialisé
✅ MarketingRolesManager initialisé
✅ GrandOpeningManager initialisé
✅ WeeklyAdminRecap configuré
✅ Système de giveaways automatiques initialisé
✅ Commandes slash synchronisées
```

### Étape 9: Vérifier les conteneurs

```bash
# Voir les conteneurs actifs
docker compose ps

# Statut attendu:
# NAME              STATUS
# shellia-bot       Up (healthy)
# shellia-redis     Up (healthy)

# Si problème, voir les logs
docker compose logs bot --tail=100
docker compose logs redis --tail=50
```

---

## 8. CONFIGURATION DES NOUVELLES FONCTIONNALITÉS

### 8.1 Configurer le Pré-achat

```bash
# Dans Discord, créer un channel:
# #🛍️│pré-achat

# Récupérer l'ID du channel (clic droit → Copy ID, mode dev activé)
# Mettre à jour .env:
nano .env
# PREORDER_CHANNEL_ID=1234567890123456789

# Redémarrer le bot
docker compose restart bot
```

**Créer un pré-achat:**
```
!preorder_create "Pack Pro Founder" 99.99 14 30 "Pack exclusif pour les fondateurs"
```

### 8.2 Configurer les Rôles Marketing

```bash
# Créer les channels pour les rôles:
# #🏆│ambassadeurs
# #📢│influenceurs
# #🎨│createurs
# etc.
```

**Les rôles disponibles:**
- 🌟 Ambassadeur - Parrainage (20% commission)
- 📢 Influenceur - Contenu (€50-200/mois)
- 🎨 Créateur - Visuels (€10-50/piece)
- 🆘 Helper - Support (€20-50/mois)
- 🎉 Event Host - Événements
- 🧪 Beta Tester - Tests (Pro gratuit)
- 🤝 Partenaire - Partenariats (30% commission)

**Voir les rôles:**
```
!marketing_roles
```

**Postuler:**
```
!marketing_apply ambassador "Je veux aider la communauté à grandir !"
```

### 8.3 Configurer l'Ouverture Officielle

```bash
# Choisir une date
# Exemple: 15 Février 2026 à 18h00
```

**Configurer:**
```
!opening_setup 2026 2 15 18
```

**L'IA va automatiquement:**
- T-7 jours: Annonce officielle
- T-3 jours: Teaser
- T-24h: Dernier rappel
- T-1h: Compte à rebours
- T-0: OUVERTURE OFFICIELLE 🚀
- T+24h: Bilan jour 1
- T+7j: Bilan semaine 1

**Forcer l'ouverture (admin):**
```
!opening_force
```

### 8.4 Configurer le Récap Hebdomadaire

```bash
# Créer un channel admin privé
# #📊│admin-recap
```

**Configurer:**
```
!recap_setup #📊│admin-recap 0 9
```

**Paramètres:**
- 0 = Lundi (jour d'envoi)
- 9 = 9h du matin

**Forcer un récap immédiat:**
```
!recap_force
```

---

## 9. VÉRIFICATION DU DÉPLOIEMENT

### Tester sur Discord

```
# Commandes basiques
/help              → Doit afficher l'aide
/quota             → Voir son quota
/plans             → Plans disponibles
/openclaw          → Dashboard business (admin)

# Commandes marketing
/preorder_stats    → Stats pré-achats (admin)
/marketing_roles   → Liste rôles marketing
/opening_status    → Statut ouverture

# Commandes giveaways
/giveaway          → Infos giveaways
/winner            → Info grade Winner
/balance           → Solde coins
```

### Vérifier les modules

```bash
# Dans les logs, chercher:
docker compose logs bot | grep -E "(✅|❌|ERROR)"

# Doit afficher:
# ✅ OpenClaw Manager initialisé
# ✅ PreorderMarketingSystem initialisé
# ✅ MarketingRolesManager initialisé
# ✅ GrandOpeningManager initialisé
# ✅ WeeklyAdminRecap configuré
```

---

## 10. COMMANDES DE GESTION

### Docker

```bash
cd /opt/shellia-project

# Voir les logs en temps réel
docker compose logs -f bot

# Redémarrer
docker compose restart

# Arrêter
docker compose down

# Mettre à jour (pull + restart)
docker compose pull
docker compose up -d

# Backup Redis
docker exec shellia-redis redis-cli BGSAVE
```

### Bot (Discord)

**Admin:**
```
!openclaw                      → Dashboard business
!oc_metrics 7                  → Métriques 7 jours
!preorder_create ...           → Créer pré-achat
!marketing_approve @user role  → Approuver rôle
!opening_setup ...             → Configurer ouverture
!recap_setup ...               → Configurer récap
!recap_force                   → Forcer récap
!serverstats                   → Stats serveur
```

**Utilisateur:**
```
/giveaway                      → Infos giveaways
/marketing_roles               → Voir rôles
/marketing_apply role          → Postuler
/balance                       → Solde
/winner                        → Info grade Winner
```

---

## 11. DÉPANNAGE

### Problème: Bot ne démarre pas

```bash
# Voir les logs
docker compose logs bot

# Erreurs communes:
# 1. Variables manquantes
#    → Vérifier .env
#    → Vérifier que toutes les clés sont remplies

# 2. Token Discord invalide
#    → Régénérer sur Discord Developer Portal

# 3. Connexion Supabase échoue
#    → Vérifier SUPABASE_URL et SUPABASE_KEY
#    → Vérifier IP autorisée (Supabase → Database → IPv4)

# 4. Tables SQL manquantes
#    → Exécuter tous les scripts SQL

# Redémarrer proprement
docker compose down
docker compose up -d --build
```

### Problème: Commandes slash non visibles

```bash
# Dans Discord:
# 1. Faire / dans le serveur
# 2. Attendre 1h (cache Discord)

# Forcer la sync (si commande dispo):
!sync

# Ou redémarrer le bot
docker compose restart bot
```

### Problème: Giveaways/Preorder ne fonctionnent pas

```bash
# Vérifier logs
docker compose logs bot | grep -E "(giveaway|preorder)"

# Vérifier channels configurés
# Vérifier permissions du bot (Manage Messages, Add Reactions)
```

### Problème: Weekly Recap ne s'envoie pas

```bash
# Vérifier config
# RECAP_DAY et RECAP_HOUR dans .env

# Vérifier channel ID
# Le bot doit avoir accès au channel admin

# Forcer un test
!recap_force
```

---

## 12. MAINTENANCE

### Quotidienne (2 minutes)

```bash
# Vérifier logs erreurs
docker compose logs --tail=50 bot | grep ERROR

# Vérifier espace disque
df -h

# Vérifier mémoire
free -h
```

### Hebdomadaire (10 minutes)

```bash
# Mettre à jour images Docker
cd /opt/shellia-project
docker compose pull
docker compose up -d

# Nettoyer vieux logs
docker exec shellia-bot find /app/logs -name "*.log" -mtime +7 -delete

# Vérifier métriques
# Dans Discord: !openclaw
```

### Mensuelle (30 minutes)

```bash
# Mettre à jour système
apt update && apt upgrade -y

# Renouveler certificats SSL (si web)
certbot renew --dry-run

# Review sécurité
# - Changer clés API si nécessaire
# - Vérifier logs de sécurité
# - Mettre à jour mots de passe
```

---

## ✅ CHECKLIST FINALE DÉPLOIEMENT

### Pré-déploiement
- [ ] VM créée avec specs correctes
- [ ] Ubuntu 22.04 LTS installé
- [ ] Docker & Docker Compose installés
- [ ] Firewall configuré (UFW)
- [ ] Fail2ban activé

### Configuration
- [ ] Repository cloné
- [ ] Fichier .env créé et rempli
- [ ] Clés API Discord obtenues
- [ ] Projet Supabase créé
- [ ] Clé Gemini obtenue
- [ ] Compte Stripe configuré

### Base de données
- [ ] Tous les scripts SQL exécutés (10 scripts)
- [ ] Tables vérifiées dans Supabase
- [ ] RLS policies activées

### Déploiement
- [ ] Docker Compose lancé
- [ ] Bot connecté à Discord
- [ ] Logs sans erreur
- [ ] Commandes slash visibles

### Configuration nouvelles features
- [ ] Channel pré-achat créé
- [ ] ID channel configuré dans .env
- [ ] Channels marketing créés
- [ ] Date ouverture configurée
- [ ] Channel admin récap créé

### Tests
- [ ] !help fonctionne
- [ ] !openclaw fonctionne (admin)
- [ ] !giveaway fonctionne
- [ ] !marketing_roles fonctionne
- [ ] !opening_status fonctionne

---

## 📞 SUPPORT

En cas de problème:
1. Consulter les logs: `docker compose logs -f bot`
2. Vérifier la config: `cat .env | grep -v KEY`
3. Redémarrer: `docker compose restart`
4. Vérifier les permissions du bot dans Discord

---

## 🎉 UNE FOIS TERMINÉ

Le bot sera 100% opérationnel avec:
- 🤖 Bot Discord IA
- 🦀 OpenClaw Business Automation
- 🎁 Giveaways automatiques
- 🛍️ **Système de pré-achat**
- 🎭 **Rôles marketing**
- 🎊 **Ouverture officielle automatisée**
- 📊 **Récap hebdomadaire admin**

**Shellia pourra gérer automatiquement le business et le marketing !** 🚀

---

**Version:** 2.1-OPENCLOW-PLUS  
**Date:** Février 2026  
**Statut:** ✅ PRODUCTION READY
