# 🐚 Shellia AI - Discord E-commerce Bot v2.0

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/votre-repo/shellia-ai)
[![Security](https://img.shields.io/badge/security-A+-brightgreen.svg)](SECURITY_COMPLETE.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> 🤖 **Shellia** est une IA e-commerce avancée pour Discord avec génération d'images, paiements Stripe, sécurité enterprise-grade, et dashboard admin complet.

---

## ✨ Fonctionnalités Principales

### 🎨 **Bot Discord**
- IA conversationnelle avec Google Gemini
- Génération d'images avec Gemini 2.0 Flash Image
- Système de quotas intelligent par utilisateur
- Commandes produits et catalogue
- Paiements Stripe intégrés
- Sécurité multi-couches (rate limiting, circuit breaker)

### 🔐 **Sécurité Enterprise**
- Authentification Discord OAuth2 + PKCE
- Sessions chiffrées AES-256-GCM
- Protection contre XSS, CSRF, SQL Injection
- Protection Prototype Pollution & DOM Clobbering
- CSP strict avec nonce
- SRI (Subresource Integrity)
- Rate limiting persistant
- Circuit breaker pour API externes
- Audit trail complet

### 📊 **Dashboard Admin**
- Interface moderne avec glassmorphism
- Visualisations avec Chart.js
- Gestion des utilisateurs et commandes
- Modération avec timeout/ban/warn
- Logs de sécurité en temps réel
- Système de support par tickets
- 7 pages complètes + modales

### 🗄️ **Base de Données**
- Supabase (PostgreSQL)
- 15+ tables avec RLS activé
- Fonctions RPC sécurisées
- Triggers automatiques
- Sauvegarde automatique

---

## 🚀 Installation Rapide

### Prérequis
- Python 3.11+
- Node.js 18+
- Compte Supabase
- Compte Discord Developer
- Clé API Google Gemini
- Compte Stripe (test/live)

### 1. Cloner et installer

```bash
git clone https://github.com/votre-repo/shellia-ai.git
cd shellia-ai

# Python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Tests
pip install -r requirements-dev.txt
```

### 2. Configuration

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer les variables
nano .env
```

**Variables requises:**
```env
# Discord
DISCORD_TOKEN=votre_token_discord
DISCORD_CLIENT_ID=votre_client_id
DISCORD_CLIENT_SECRET=votre_client_secret
DISCORD_REDIRECT_URI=https://votre-domaine.com/callback

# Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre_cle_service_role

# Google Gemini
GEMINI_API_KEY=votre_cle_gemini

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Sécurité
ENCRYPTION_KEY=votre_cle_fernet_base64
```

### 3. Base de données

```bash
# Exécuter les scripts SQL dans l'ordre
# Via Supabase Dashboard → SQL Editor

deployment/supabase_schema.sql      # Tables principales
deployment/auth_schema.sql          # Tables auth
deployment/security_schema.sql      # Tables sécurité
deployment/scheduler_schema.sql     # Tables scheduler
```

### 4. Lancer l'application

```bash
# Bot
python bot/bot_secure.py

# Dashboard (Apache/Nginx)
# Copier admin-panel/ dans /var/www/html/
sudo cp -r admin-panel/ /var/www/html/shellia-admin/

# Ou serveur de développement
cd admin-panel && python -m http.server 8080
```

---

## 📁 Structure du Projet

```
shellia-project/
│
├── 📁 bot/                          # Bot Discord
│   ├── bot_secure.py               # Bot principal avec sécurité
│   ├── secure_config.py            # Gestion secrets chiffrés
│   ├── security_integration.py     # Intégration modules sécurité
│   ├── stripe_webhook_validator.py # Validation HMAC Stripe
│   ├── persistent_rate_limiter.py  # Rate limiting persistant
│   ├── circuit_breaker.py          # Circuit breaker API
│   └── conversation_history.py     # Historique chiffré
│
├── 📁 admin-panel/                  # Dashboard Admin
│   ├── login.html                  # Page de login
│   ├── index.html                  # Dashboard principal
│   ├── users.html                  # Gestion utilisateurs
│   ├── orders.html                 # Gestion commandes
│   ├── moderation.html             # Modération
│   ├── support.html                # Support tickets
│   ├── logs.html                   # Logs sécurité
│   ├── settings.html               # Paramètres
│   ├── login-auth.js               # Auth OAuth2 + chiffrement
│   ├── security-advanced.js        # 🛡️ Protections avancées
│   ├── style.css                   # Styles + glassmorphism
│   ├── .htaccess                   # Config Apache sécurisée
│   └── nginx.conf                  # Config Nginx sécurisée
│
├── 📁 deployment/                   # Scripts de déploiement
│   ├── docker-compose.yml          # Docker Compose
│   ├── Dockerfile                  # Image Docker
│   ├── deploy.sh                   # Script de déploiement
│   ├── update.sh                   # Script de mise à jour
│   └── *.sql                       # Schémas base de données
│
├── 📁 tests/                        # Tests
│   ├── test_security.py            # Tests unitaires sécurité
│   ├── test_integration.py         # Tests E2E
│   └── conftest.py                 # Fixtures pytest
│
├── 📁 docs/                         # Documentation
│   ├── API_REFERENCE.md            # Référence API
│   ├── SECURITY_COMPLETE.md        # Guide sécurité complet
│   ├── ADMIN_GUIDE.md              # Guide admin
│   └── DEPLOYMENT.md               # Guide déploiement
│
├── 📄 .env.example                  # Template configuration
├── 📄 requirements.txt              # Dépendances Python
├── 📄 requirements-dev.txt          # Dépendances dev
└── 📄 PROJECT_COMPLETE_README.md    # Ce fichier
```

---

## 🎮 Commandes Discord

### Utilisateur
| Commande | Description |
|----------|-------------|
| `!help` | Afficher l'aide |
| `!ask [question]` | Poser une question à Shellia |
| `!image [prompt]` | Générer une image |
| `!product [id]` | Voir un produit |
| `!catalog` | Voir le catalogue |
| `!buy [id]` | Acheter un produit |
| `!cart` | Voir le panier |
| `!checkout` | Passer commande |
| `!order [id]` | Voir une commande |
| `!support [message]` | Contacter le support |
| `!feedback [texte]` | Donner un avis |

### Admin
| Commande | Description |
|----------|-------------|
| `!admin_stats` | Statistiques serveur |
| `!admin_orders` | Liste des commandes |
| `!admin_user [@user]` | Infos utilisateur |
| `!admin_warn [@user] [raison]` | Avertir |
| `!admin_timeout [@user] [minutes]` | Timeout |
| `!admin_ban [@user] [raison]` | Bannir |
| `!admin_ticket [id]` | Voir un ticket |
| `!admin_config [clé] [valeur]` | Configurer |

---

## 🛡️ Sécurité

### Protections Implémentées

| Protection | Niveau | Description |
|------------|--------|-------------|
| **Authentification** | 🔴 Critique | OAuth2 + PKCE, sessions chiffrées |
| **Autorisation** | 🔴 Critique | RLS, rôles admin/vendeur/user |
| **Rate Limiting** | 🟠 Haut | Persistent, multi-niveaux |
| **Input Validation** | 🟠 Haut | Validation stricte, sanitization |
| **Encryption** | 🟠 Haut | AES-256-GCM, Fernet |
| **Audit Trail** | 🟡 Moyen | Logs complets, signalement |
| **Circuit Breaker** | 🟡 Moyen | Protection API externe |
| **CSP** | 🟡 Moyen | Strict avec nonce |
| **SRI** | 🟢 Bas | Checksums CDN |
| **Honeypot** | 🟢 Bas | Anti-bot avancé |

**Score global: 9.3/10** ⭐ Enterprise-Grade

Voir [SECURITY_COMPLETE.md](SECURITY_COMPLETE.md) pour les détails complets.

---

## 📊 Dashboard Admin

### Pages Disponibles
1. **Login** - Authentification Discord sécurisée
2. **Dashboard** - Vue d'ensemble avec statistiques
3. **Utilisateurs** - Gestion et modération
4. **Commandes** - Suivi des ventes
5. **Modération** - Warn/timeout/ban
6. **Support** - Gestion des tickets
7. **Logs** - Sécurité et audit
8. **Paramètres** - Configuration

### Fonctionnalités
- 🎨 **Design moderne**: Glassmorphism + animations
- 📈 **Visualisations**: Chart.js (ventes, utilisateurs)
- 🔐 **Sécurité**: Sessions chiffrées, 2FA support
- 🔔 **Temps réel**: WebSocket pour notifications
- 📱 **Responsive**: Mobile et desktop

---

## 🧪 Tests

```bash
# Tous les tests
pytest tests/ -v --cov

# Tests sécurité uniquement
pytest tests/test_security.py -v

# Tests E2E
pytest tests/test_integration.py -v

# Avec couverture
pytest tests/ --cov=bot --cov-report=html
```

### Tests Implémentés
- ✅ 20+ tests unitaires
- ✅ 15+ tests E2E
- ✅ Tests de charge
- ✅ Tests de sécurité
- ✅ Tests d'intégration API

---

## 🚀 Déploiement

### Option 1: Docker (Recommandé)

```bash
cd deployment
docker-compose up -d

# Mettre à jour
docker-compose pull
docker-compose up -d
```

### Option 2: VPS Cloud

```bash
# 1. Préparer le serveur
chmod +x deployment/deploy.sh
./deployment/deploy.sh

# 2. Configurer le reverse proxy (Nginx)
sudo cp deployment/nginx.conf /etc/nginx/sites-available/shellia
sudo ln -s /etc/nginx/sites-available/shellia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 3. SSL avec Let's Encrypt
sudo certbot --nginx -d votre-domaine.com
```

### Option 3: PaaS (Railway, Render, etc.)

```bash
# Railway
railway login
railway init
railway up

# Render
# Connecter le repo Git à Render Dashboard
```

Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour le guide complet.

---

## 📈 Monitoring

### Métriques Disponibles
- Nombre d'utilisateurs actifs
- Commandes par jour
- Revenus (Stripe)
- Taux d'utilisation quotas
- Latence bot
- Erreurs et exceptions

### Outils de Monitoring
```bash
# Logs bot
tail -f logs/bot.log

# Logs sécurité
tail -f logs/security.log

# Métriques temps réel
python -c "from bot.security_integration import metrics; metrics.display_dashboard()"
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SECURITY_COMPLETE.md](SECURITY_COMPLETE.md) | Guide sécurité complet |
| [API_REFERENCE.md](API_REFERENCE.md) | Référence API |
| [ADMIN_GUIDE.md](ADMIN_GUIDE.md) | Guide administrateur |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Guide déploiement |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guide contribution |

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

---

## 📄 Licence

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

---

## 🙏 Remerciements

- [discord.py](https://github.com/Rapptz/discord.py) - Bibliothèque Discord
- [Supabase](https://supabase.com/) - Base de données
- [Google Gemini](https://ai.google.dev/) - Intelligence artificielle
- [Stripe](https://stripe.com/) - Paiements
- [Chart.js](https://www.chartjs.org/) - Visualisations

---

## 📞 Support

- 💬 Discord: [Votre serveur Discord]
- 📧 Email: support@votre-domaine.com
- 🐛 Issues: [GitHub Issues](https://github.com/votre-repo/shellia-ai/issues)
- 📖 Wiki: [GitHub Wiki](https://github.com/votre-repo/shellia-ai/wiki)

---

## 🎯 Roadmap

### ✅ Complété (v2.0)
- [x] Bot Discord complet
- [x] Dashboard admin 7 pages
- [x] Sécurité enterprise-grade
- [x] Génération d'images
- [x] Paiements Stripe
- [x] Tests automatisés

### 🔮 À venir (v2.1)
- [ ] TOTP 2FA pour admins
- [ ] Mode sombre/clair
- [ ] Notifications push
- [ ] Application mobile
- [ ] Support multi-serveur
- [ ] Analytics avancés

### 🚀 Futur (v3.0)
- [ ] IA personnalisée par serveur
- [ ] Marketplace de plugins
- [ ] API publique
- [ ] Webhook personnalisés
- [ ] Intégration Shopify/WooCommerce

---

<div align="center">

**🌟 N'oubliez pas de mettre une étoile si vous aimez le projet ! 🌟**

[⭐ Star](https://github.com/votre-repo/shellia-ai) |
[🐛 Issues](https://github.com/votre-repo/shellia-ai/issues) |
[💬 Discussions](https://github.com/votre-repo/shellia-ai/discussions)

</div>

---

<p align="center">
  <strong>Fait avec ❤️ par l'équipe Shellia AI</strong>
</p>

<p align="center">
  <sub>Version 2.0 - Février 2026</sub>
</p>
