# 🤖 GUIDE IA - Gestion de Shellia Bot sur Proxmox

> **Document pour IA Administratrice**  
> Ce guide permet à une IA de gérer, monitorer et maintenir Shellia AI Bot sur une VM Proxmox.

---

## 📋 TABLE DES MATIÈRES

1. [Architecture](#architecture)
2. [Déploiement Initial](#déploiement-initial)
3. [Configuration Supabase](#configuration-supabase)
4. [Gestion Quotidienne](#gestion-quotidienne)
5. [Monitoring & Alertes](#monitoring--alertes)
6. [Procédures d'Urgence](#procédures-durgence)
7. [Mises à Jour](#mises-à-jour)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                      PROXMOX HOST                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  VM/LXC: shellia-bot (Ubuntu 22.04)                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  Bot Discord│  │ Admin Panel │  │   Nginx     │ │   │
│  │  │   (Python)  │  │   (HTML/JS) │  │  (Reverse)  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Services Externes:                                  │   │
│  │  • Supabase (PostgreSQL)                            │   │
│  │  • Google Gemini API                                │   │
│  │  • Discord API                                      │   │
│  │  • Stripe                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Ressources Recommandées

| Composant | CPU     | RAM | Disque | Network  |
| --------- | ------- | --- | ------ | -------- |
| Bot       | 2 cores | 2GB | 50GB   | 100 Mbps |
| Total     | 2 cores | 2GB | 50GB   | -        |

---

## 🚀 DÉPLOIEMENT INITIAL

### 1. Création de la VM sur Proxmox

```bash
# Se connecter au node Proxmox
ssh root@proxmox-host

# Créer une VM Ubuntu 22.04
qm create 9000 --name shellia-bot --memory 2048 --cores 2 --net0 virtio,bridge=vmbr0
qm importdisk 9000 ubuntu-22.04-server-cloudimg-amd64.img local-lvm
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot order=scsi0
qm set 9000 --serial0 socket --vga serial0
qm set 9000 --agent enabled=1

# Démarrer
qm start 9000
```

### 2. Configuration Initiale de la VM

```bash
# Se connecter à la VM
ssh ubuntu@shellia-bot-ip

# Mise à jour
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y python3-pip python3-venv git curl nginx

# Créer l'utilisateur shellia
sudo useradd -m -s /bin/bash shellia
sudo usermod -aG sudo shellia

# Créer la structure
sudo mkdir -p /opt/shellia
sudo chown shellia:shellia /opt/shellia

# Passer à l'utilisateur shellia
su - shellia
cd /opt/shellia

# Cloner le projet (ou copier les fichiers)
git clone https://github.com/Micka420-collab/shellia-project.git .
# OU copier depuis un autre emplacement
```

### 3. Installation du Bot

```bash
cd /opt/shellia

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
cd bot
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
nano .env  # Éditer avec les vraies valeurs
```

### 4. Configuration des Variables d'Environnement

```bash
# /opt/shellia/bot/.env
DISCORD_TOKEN=your_discord_token
GUILD_ID=your_guild_id
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_api_key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
ADMIN_PANEL_PORT=8080
ADMIN_PANEL_SECRET=your_secret
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 5. Installation du Service Systemd

```bash
# En tant que root
sudo cp /opt/shellia/deployment/shellia-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shellia-bot

# Créer l'utilisateur si pas fait
sudo useradd -r -s /bin/false shellia
sudo mkdir -p /opt/shellia/bot/logs
sudo chown -R shellia:shellia /opt/shellia

# Démarrer
sudo systemctl start shellia-bot
sudo systemctl status shellia-bot
```

---

## 🗄️ CONFIGURATION SUPABASE

### 1. Créer un Projet Supabase

1. Aller sur https://supabase.com
2. Créer un nouveau projet
3. Noter l'URL et la clé service_role

### 2. Exécuter le Schema SQL

```sql
-- Aller dans SQL Editor > New Query
-- Copier-coller le contenu de deployment/supabase_schema.sql
-- Exécuter
```

### 3. Vérifier les Tables Créées

```sql
-- Liste des tables
SELECT table_name
FROM information.tables
WHERE table_schema = 'public';

-- Doit retourner:
-- users
-- daily_quotas
-- user_streaks
-- streak_history
-- user_badges
-- referral_codes
-- referrals
-- referral_rewards
-- user_trials
-- user_violations
-- security_logs
-- message_history
-- payments
```

### 4. Configurer les Politiques RLS

```sql
-- Vérifier que RLS est actif
SELECT relname, relrowsecurity
FROM pg_class
WHERE relname IN ('users', 'daily_quotas', 'user_streaks');
```

---

## 📊 GESTION QUOTIDIENNE

### Commandes de Base

```bash
# Statut du bot
sudo systemctl status shellia-bot

# Logs en temps réel
sudo journalctl -u shellia-bot -f

# Redémarrer le bot
sudo systemctl restart shellia-bot

# Arrêter le bot
sudo systemctl stop shellia-bot

# Voir les logs d'erreur
sudo journalctl -u shellia-bot --since "1 hour ago" | grep ERROR
```

### Vérification de Santé

```bash
# Script de healthcheck
#!/bin/bash
# /opt/shellia/scripts/healthcheck.sh

BOT_STATUS=$(systemctl is-active shellia-bot)
DISCORD_API=$(curl -s -o /dev/null -w "%{http_code}" https://discord.com/api/v10/gateway)
SUPABASE_API=$(curl -s -o /dev/null -w "%{http_code}" -H "apikey: $SUPABASE_KEY" "$SUPABASE_URL/rest/v1/")

echo "Bot Status: $BOT_STATUS"
echo "Discord API: $DISCORD_API"
echo "Supabase API: $SUPABASE_API"

if [ "$BOT_STATUS" != "active" ] || [ "$DISCORD_API" != "200" ]; then
    echo "ALERT: Service degradation detected!"
    # Envoyer alerte (webhook, email, etc.)
fi
```

### Backup de la Base de Données

```bash
#!/bin/bash
# /opt/shellia/scripts/backup.sh

BACKUP_DIR="/opt/shellia/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup via Supabase CLI
supabase db dump -f "$BACKUP_DIR/shellia_backup_$DATE.sql"

# Garder seulement les 7 derniers backups
ls -t "$BACKUP_DIR"/shellia_backup_*.sql | tail -n +8 | xargs rm -f

echo "Backup completed: $BACKUP_DIR/shellia_backup_$DATE.sql"
```

---

## 📈 MONITORING & ALERTES

### 1. Métriques à Surveiller

| Métrique         | Seuil d'Alerte | Action                   |
| ---------------- | -------------- | ------------------------ |
| CPU > 80%        | 5 min          | Investiguer              |
| RAM > 90%        | 5 min          | Redémarrer si nécessaire |
| Disk > 85%       | Immédiat       | Nettoyer les logs        |
| Bot Offline      | Immédiat       | Redémarrer               |
| API Errors > 10% | 15 min         | Vérifier clés API        |
| Cost > 50$/jour  | Immédiat       | Vérifier abus            |

### 2. Script de Monitoring

```bash
#!/bin/bash
# /opt/shellia/scripts/monitor.sh

WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK"

send_alert() {
    local message="$1"
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"🚨 Shellia Alert: $message\"}" \
         "$WEBHOOK_URL"
}

# Check bot status
if [ "$(systemctl is-active shellia-bot)" != "active" ]; then
    send_alert "Bot is DOWN! Attempting restart..."
    sudo systemctl restart shellia-bot
fi

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    send_alert "Disk usage at ${DISK_USAGE}%!"
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 90 ]; then
    send_alert "Memory usage at ${MEM_USAGE}%!"
fi
```

### 3. Cron Jobs

```bash
# Crontab pour shellia
# crontab -e

# Healthcheck toutes les 5 minutes
*/5 * * * * /opt/shellia/scripts/healthcheck.sh >> /opt/shellia/logs/health.log 2>&1

# Backup quotidien à 3h du matin
0 3 * * * /opt/shellia/scripts/backup.sh >> /opt/shellia/logs/backup.log 2>&1

# Monitoring toutes les minutes
* * * * * /opt/shellia/scripts/monitor.sh >> /opt/shellia/logs/monitor.log 2>&1

# Nettoyage des logs hebdomadaire
0 0 * * 0 find /opt/shellia/logs -name "*.log" -mtime +7 -delete
```

---

## 🚨 PROCÉDURES D'URGENCE

### Scénario 1: Bot Ne Répond Plus

```bash
# 1. Vérifier le statut
sudo systemctl status shellia-bot

# 2. Voir les logs d'erreur
sudo journalctl -u shellia-bot --since "10 minutes ago" | tail -50

# 3. Redémarrer
sudo systemctl restart shellia-bot

# 4. Vérifier après redémarrage
sleep 5
sudo systemctl status shellia-bot

# 5. Si toujours KO, vérifier les clés API
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     "https://generativelanguage.googleapis.com/v1beta/models"
```

### Scénario 2: Rate Limit Discord

```bash
# Symptômes: 429 errors dans les logs
# Action: Attendre et monitorer

# Vérifier les headers rate limit
grep "429" /opt/shellia/logs/bot.log | tail -20

# Redémarrer avec backoff exponentiel
sudo systemctl stop shellia-bot
sleep 60
sudo systemctl start shellia-bot
```

### Scénario 3: Coûts API Anormaux

```bash
# Vérifier dans Supabase
# SQL Query:
SELECT
    date,
    SUM(cost_usd) as total_cost,
    SUM(messages_used) as total_messages
FROM daily_quotas
WHERE date >= CURRENT_DATE - 7
GROUP BY date
ORDER BY date DESC;

# Si coût > 50$ en un jour:
# 1. Identifier l'utilisateur problématique
SELECT user_id, SUM(cost_usd) as cost
FROM daily_quotas
WHERE date = CURRENT_DATE
GROUP BY user_id
ORDER BY cost DESC
LIMIT 10;

# 2. Bannir si nécessaire
UPDATE users
SET is_banned = TRUE, ban_reason = 'API abuse'
WHERE user_id = PROBLEMATIC_USER_ID;
```

### Scénario 4: Base de Données Inaccessible

```bash
# 1. Vérifier connectivité Supabase
curl -I "$SUPABASE_URL/rest/v1/"

# 2. Vérifier les logs du bot
grep -i "supabase\|database\|connection" /opt/shellia/logs/bot.log | tail -20

# 3. Si persistant, vérifier statut Supabase
# Aller sur https://status.supabase.com/

# 4. Mode dégradé: bot fonctionne sans DB
# (implémenter fallback en mémoire)
```

### Scénario 5: Spam/Attaque

```bash
# Identifier les spammers
# SQL Query:
SELECT user_id, COUNT(*) as msg_count
FROM message_history
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) > 100
ORDER BY msg_count DESC;

# Bannir en masse
UPDATE users
SET is_banned = TRUE, ban_reason = 'Spam attack'
WHERE user_id IN (SELECT user_id FROM spammer_list);

# Activer mode lent
# Modifier config.py: COOLDOWN_SECONDS = 10
sudo systemctl restart shellia-bot
```

---

## 🔄 MISES À JOUR

### Mise à Jour du Bot

```bash
# 1. Backup
cd /opt/shellia
./scripts/backup.sh

# 2. Arrêter le bot
sudo systemctl stop shellia-bot

# 3. Mettre à jour le code
cd /opt/shellia
# git pull  # ou copier nouveaux fichiers

# 4. Mettre à jour les dépendances
source venv/bin/activate
pip install -r bot/requirements.txt --upgrade

# 5. Appliquer les migrations SQL (si nécessaire)
# Voir deployment/migrations/

# 6. Redémarrer
sudo systemctl start shellia-bot

# 7. Vérifier
sudo systemctl status shellia-bot
sleep 5
tail -20 /opt/shellia/logs/bot.log
```

### Rollback en Cas de Problème

```bash
# 1. Arrêter
sudo systemctl stop shellia-bot

# 2. Restaurer depuis backup
cd /opt/shellia
git reset --hard HEAD~1  # ou restaurer fichiers

# 3. Restaurer DB si nécessaire
# supabase db restore backup_file.sql

# 4. Redémarrer
sudo systemctl start shellia-bot
```

---

## 🔧 TROUBLESHOOTING

### Problèmes Courants

#### Bot ne démarre pas

```bash
# Vérifier les erreurs
sudo journalctl -u shellia-bot --no-pager | tail -50

# Vérifier les variables d'environnement
cat /opt/shellia/bot/.env | grep -v "^#" | grep -v "^$"

# Vérifier les permissions
ls -la /opt/shellia/bot/
sudo chown -R shellia:shellia /opt/shellia

# Tester manuellement
su - shellia
cd /opt/shellia/bot
source ../venv/bin/activate
python bot.py
```

#### Erreurs de connexion Supabase

```bash
# Tester la connexion
curl -H "apikey: $SUPABASE_KEY" \
     -H "Authorization: Bearer $SUPABASE_KEY" \
     "$SUPABASE_URL/rest/v1/users?limit=1"

# Vérifier le format de l'URL
# Doit être: https://xxxxxx.supabase.co

# Vérifier la clé (service_role, pas anon)
echo $SUPABASE_KEY | cut -c1-20
# Doit commencer par eyJ...
```

#### Erreurs Discord

```
# LoginFailure: Improper token
# → Régénérer le token sur Discord Developer Portal

# PrivilegedIntentsRequired
# → Activer intents dans Discord Developer Portal

# ConnectionResetError
# → Vérifier firewall/réseau
```

#### Erreurs Gemini API

```bash
# 429 Too Many Requests
# → Attendre, vérifier quotas Google AI Studio

# 400 Bad Request
# → Vérifier format des requêtes

# Clé invalide
# → Régénérer sur https://aistudio.google.com
```

### Logs Importants

```bash
# Logs systemd
sudo journalctl -u shellia-bot -f

# Logs applicatifs
tail -f /opt/shellia/logs/bot.log

# Logs d'erreur
grep ERROR /opt/shellia/logs/bot.log | tail -20

# Logs d'accès (si nginx)
sudo tail -f /var/log/nginx/shellia-access.log
```

---

## 📚 RÉFÉRENCE RAPIDE

### Commandes Essentielles

```bash
# Statut
sudo systemctl status shellia-bot

# Logs
sudo journalctl -u shellia-bot -f -n 100

# Redémarrage
sudo systemctl restart shellia-bot

# Mise à jour
sudo systemctl stop shellia-bot && \
git pull && \
sudo systemctl start shellia-bot

# Backup
supabase db dump -f backup.sql

# Restore
psql -h $SUPABASE_HOST -U postgres -d postgres < backup.sql
```

### URLs Importantes

| Service            | URL                                         |
| ------------------ | ------------------------------------------- |
| Discord Dev Portal | https://discord.com/developers/applications |
| Supabase Dashboard | https://supabase.com/dashboard              |
| Google AI Studio   | https://aistudio.google.com                 |
| Stripe Dashboard   | https://dashboard.stripe.com                |

### Fichiers de Configuration

| Fichier                                       | Description               |
| --------------------------------------------- | ------------------------- |
| `/opt/shellia/bot/.env`                       | Variables d'environnement |
| `/opt/shellia/bot/config.py`                  | Configuration du bot      |
| `/etc/systemd/system/shellia-bot.service`     | Service systemd           |
| `/opt/shellia/deployment/supabase_schema.sql` | Schema DB                 |

---

## 📝 CHECKLIST MAINTENANCE HEBDOMADAIRE

- [ ] Vérifier les logs d'erreur
- [ ] Vérifier l'utilisation des ressources (CPU/RAM/Disk)
- [ ] Vérifier les coûts API
- [ ] Backup de la base de données
- [ ] Vérifier les mises à jour de sécurité
- [ ] Vérifier les statistiques utilisateurs
- [ ] Nettoyer les vieux logs

---

## 🔐 SÉCURITÉ

### Bonnes Pratiques

1. **Ne jamais** committer les fichiers `.env`
2. **Rotation régulière** des clés API (tous les 90 jours)
3. **Firewall**: uniquement ports 80, 443, 22
4. **Updates** de sécurité automatiques
5. **Monitoring** des accès anormaux

### Vérification de Sécurité

```bash
# Vérifier les processus
ps aux | grep shellia

# Vérifier les connexions réseau
netstat -tulpn | grep python

# Vérifier les fichiers sensibles
find /opt/shellia -type f -perm /o+w  # World writable

# Vérifier les mises à jour
apt list --upgradable
```

---

**Document version:** 5.0  
**Last updated:** 2026  
**Maintained by:** IA Shellia Admin
