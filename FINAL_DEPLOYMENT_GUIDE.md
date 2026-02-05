# 🚀 Guide de Déploiement Final - Shellia AI v2.0

Guide complet pour déployer Shellia AI Bot avec toutes les fonctionnalités sécurisées.

---

## 📋 Table des Matières

1. [Architecture du Système](#architecture)
2. [Prérequis](#prérequis)
3. [Déploiement Base de Données](#database)
4. [Configuration Discord OAuth](#oauth)
5. [Déploiement du Bot](#bot)
6. [Déploiement du Dashboard](#dashboard)
7. [Vérifications](#vérifications)
8. [Maintenance](#maintenance)

---

## 🏗️ Architecture du Système {#architecture}

```
┌─────────────────────────────────────────────────────────────┐
│                         UTILISATEUR                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌──────────────┐ ┌──────────┐ ┌─────────────────┐
│   Website    │ │ Dashboard│ │   Discord Bot   │
│   (Statique) │ │  (OAuth) │ │   (Sécurisé)    │
└──────┬───────┘ └────┬─────┘ └────────┬────────┘
       │              │                │
       │              │                │
       └──────────────┼────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │    SUPABASE       │
            │  ├─ Auth          │
            │  ├─ Database      │
            │  ├─ Realtime      │
            │  └─ Storage       │
            └──────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌────────────┐ ┌──────────┐ ┌──────────────┐
│   Redis    │ │  Gemini  │ │   Stripe     │
│(Rate Limit)│ │    AI    │ │  (Paiements) │
└────────────┘ └──────────┘ └──────────────┘
```

---

## 📦 Prérequis {#prérequis}

### Comptes Requis

- [ ] **Discord** : Compte + Application Bot
- [ ] **Supabase** : Projet (gratuit suffit)
- [ ] **Google AI** : API Key Gemini
- [ ] **Stripe** : Compte (test ou live)
- [ ] **Hébergeur** : VPS ou Railway/Render/Heroku

### Logiciels

```bash
# Sur votre machine
node --version    # v18+
npm --version     # v9+
python --version  # 3.11+
git --version     # 2.40+

# Sur le serveur
redis-server --version  # v7+ (optionnel)
```

---

## 🗄️ Étape 1 : Base de Données {#database}

### 1.1 Créer le projet Supabase

1. Allez sur [supabase.com](https://supabase.com)
2. Créez un nouveau projet
3. Copiez l'**URL** et la **clé service_role**

### 1.2 Appliquer les schémas SQL

```bash
cd shellia-project/deployment

# Ordre important !
psql $DATABASE_URL -f supabase_schema.sql
psql $DATABASE_URL -f security_schema.sql
psql $DATABASE_URL -f auth_schema.sql
```

Ou via l'interface Supabase :
1. SQL Editor → New query
2. Copiez-collez chaque fichier
3. Run

### 1.3 Vérifier les tables

```sql
-- Doit afficher toutes les tables
\dt

-- Tables principales :
-- users, daily_quotas, user_streaks, payments
-- rate_limits, conversation_history, admin_users
-- admin_sessions, secure_config
```

---

## 🔐 Étape 2 : Configuration Discord OAuth {#oauth}

### 2.1 Créer l'application Discord

1. [Discord Developer Portal](https://discord.com/developers/applications)
2. New Application → "Shellia AI Dashboard"
3. OAuth2 → General

### 2.2 Configurer les Redirects

```
# Développement
http://localhost:8080/admin-panel/

# Production (remplacez par votre domaine)
https://votre-domaine.com/admin-panel/
```

### 2.3 Copier le Client ID

- General Information → **APPLICATION ID**
- Ressemble à : `1234567890123456789`

### 2.4 Ajouter le premier admin

```sql
-- Remplacez par VOTRE vrai Discord ID
INSERT INTO admin_users (discord_id, discord_username, is_super_admin, is_active)
VALUES ('VOTRE_DISCORD_ID', 'VotrePseudo', TRUE, TRUE);
```

**Pour trouver votre Discord ID :**
- Discord → Paramètres → Avancé → Mode développeur ON
- Clic droit sur votre nom → Copier l'identifiant

---

## 🤖 Étape 3 : Déploiement du Bot {#bot}

### 3.1 Cloner le projet

```bash
git clone https://github.com/votre-repo/shellia-ai.git
cd shellia-ai
```

### 3.2 Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3.3 Installer les dépendances

```bash
pip install -r bot/requirements.txt
```

### 3.4 Configuration environnement

```bash
cd bot

# Créer le .env
cat > .env << 'EOF'
# Discord
DISCORD_TOKEN=votre_token_discord
DISCORD_APPLICATION_ID=votre_app_id

# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Gemini
GEMINI_API_KEY=AIzaSy...

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Optionnel - Redis
REDIS_URL=redis://localhost:6379/0

# Sécurité
ADMIN_API_SECRET=un_secret_long_et_aleatoire
EOF
```

### 3.5 Chiffrer les secrets (IMPORTANT !)

```bash
# Générer une clé maître
python -c "from secure_config import SecureConfigManager; print(SecureConfigManager.generate_master_key())"

# Copiez la clé générée
export SECURE_CONFIG_KEY="gAAAAAB..."

# Chiffrer le .env
python secure_config.py encrypt --env-file .env

# Vérifier
head -5 .env
# Doit afficher: GEMINI_API_KEY=ENC:gAAAAAB...
```

### 3.6 Tester le bot

```bash
python bot_secure.py
```

Vous devriez voir :
```
🚀 Démarrage Shellia AI Bot v2.0 (Sécurisé)...
🔒 Sécurité activée: True
✅ Bot connecté: Shellia AI#1234
✅ Sécurité initialisée
✅ 15 commandes slash synchronisées
```

### 3.7 Déployer en production

**Option A : Docker (Recommandé)**

```bash
docker-compose -f deployment/docker-compose.security.yml up -d
```

**Option B : PM2**

```bash
npm install -g pm2
pm2 start bot/bot_secure.py --name shellia-bot --interpreter python
pm2 save
pm2 startup
```

**Option C : Systemd**

```bash
sudo cp deployment/shellia-bot.service /etc/systemd/system/
sudo systemctl enable shellia-bot
sudo systemctl start shellia-bot
sudo systemctl status shellia-bot
```

---

## 🎨 Étape 4 : Déploiement du Dashboard {#dashboard}

### 4.1 Construire le dashboard

```bash
cd admin-panel

# Option 1 : Serveur statique simple
python -m http.server 8080

# Option 2 : Netlify (recommandé pour production)
npm install -g netlify-cli
netlify deploy --prod --dir=.

# Option 3 : Vercel
npm install -g vercel
vercel --prod
```

### 4.2 Configurer le Client ID Discord

1. Ouvrez le dashboard
2. Au premier lancement, entrez votre **Client ID Discord**
3. Cliquez "Sauvegarder"

### 4.3 Configurer HTTPS (Obligatoire pour OAuth)

**Netlify** : HTTPS automatique

**Vercel** : HTTPS automatique

**Votre serveur** :
```bash
# Utiliser Nginx + Let's Encrypt
sudo certbot --nginx -d votre-domaine.com
```

---

## ✅ Étape 5 : Vérifications {#vérifications}

### 5.1 Tester l'authentification

1. Allez sur le dashboard
2. Cliquez "Se connecter avec Discord"
3. Autorisez l'application
4. ✅ Vous devriez voir votre avatar et pseudo

### 5.2 Tester le bot

Dans Discord :
```
/help          → Affiche l'aide
/quota         → Votre quota
/image un chat → Génère une image (si Pro/Ultra)
```

### 5.3 Tester la sécurité

```bash
# Lancer les tests
cd shellia-project
python run_tests.py

# Vérifier la sécurité
python check_security.py
```

### 5.4 Vérifier les logs

```bash
# Logs du bot
tail -f logs/bot.log

# Logs de sécurité (Supabase)
psql $DATABASE_URL -c "SELECT * FROM security_logs ORDER BY timestamp DESC LIMIT 10;"

# Connexions admin
psql $DATABASE_URL -c "SELECT * FROM admin_login_logs ORDER BY created_at DESC LIMIT 10;"
```

---

## 🔧 Étape 6 : Maintenance {#maintenance}

### 6.1 Backups automatiques

**Supabase** : PITR activé par défaut

**Script de backup quotidien** :
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d)
pgsql $DATABASE_URL -f - > backup_$DATE.sql << 'EOF'
COPY (SELECT * FROM users) TO STDOUT WITH CSV;
COPY (SELECT * FROM payments) TO STDOUT WITH CSV;
EOF

# Upload vers S3 ou autre
aws s3 cp backup_$DATE.sql s3://votre-bucket/backups/
```

Crontab :
```bash
0 2 * * * /path/to/backup.sh
```

### 6.2 Monitoring

**Dashboard Supabase** : https://app.supabase.com/project/_/logs/explorer

**Alertes à configurer** :
- Taux d'erreur > 5%
- Coût API > $50/jour
- Connexions admin suspects

### 6.3 Mises à jour

```bash
# Mettre à jour le bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart shellia-bot

# Mettre à jour le dashboard
git pull
cd admin-panel
netlify deploy --prod
```

### 6.4 Rotation des clés

**Tous les 3 mois** :
1. Générer de nouvelles clés API
2. Mettre à jour via le dashboard
3. Tester
4. Révoquer les anciennes

---

## 🚨 Checklist Finale

### Avant mise en production :

- [ ] Tous les schémas SQL appliqués
- [ ] Discord OAuth configuré
- [ ] Secrets chiffrés (ENC:)
- [ ] HTTPS activé sur le dashboard
- [ ] Premier admin créé dans Supabase
- [ ] Tests passés (`python run_tests.py`)
- [ ] Bot démarré et connecté
- [ ] Dashboard accessible
- [ ] Connexion Discord testée
- [ ] Backup automatique configuré
- [ ] Monitoring activé
- [ ] Documentation lue par l'équipe

---

## 📞 Support

En cas de problème :

1. **Logs** : `tail -f logs/bot.log`
2. **Tests** : `python check_security.py`
3. **Discord** : [Votre serveur support]
4. **Documentation** : Lisez les README dans chaque dossier

---

## 🎉 Félicitations !

Votre bot Shellia AI est maintenant :
- ✅ Sécurisé avec authentification Discord OAuth2
- ✅ Protégé contre les attaques (rate limiting, circuit breaker)
- ✅ Monitoré via dashboard complet
- ✅ Prêt pour la production

**Temps estimé de déploiement** : 30-45 minutes

---

**Version** : 2.0-Security  
**Dernière mise à jour** : Février 2026  
**Auteur** : Shellia AI Team
