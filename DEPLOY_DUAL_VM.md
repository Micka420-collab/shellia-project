# 🚀 DÉPLOIEMENT DUAL-VM : SHELLIA + MAXIS

## Vue d'ensemble

```
VM 1 (Shellia) ←────API────→ VM 2 (Maxis)
    IA Contrôleur               E-commerce
```

## ÉTAPE 1 : VM 2 - Maxis (E-commerce)

### 1.1 Créer la VM
- **OS** : Ubuntu 22.04 LTS
- **CPU** : 2-4 vCPU
- **RAM** : 4-8 GB
- **Disk** : 30 GB

### 1.2 Installer Docker
```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin git
systemctl enable docker
```

### 1.3 Cloner et configurer
```bash
cd /opt
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# Créer .env
cp .env.example .env
nano .env
```

**Remplir dans .env (VM 2):**
```env
MAXIS_DISCORD_TOKEN=token_bot_maxis
MAXIS_API_KEY=une_cle_secrete_forte
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
STRIPE_SECRET_KEY=xxx
# ... etc
```

### 1.4 Exécuter les scripts SQL
Dans Supabase Dashboard → SQL Editor, exécuter dans l'ordre :
1. `deployment/supabase_schema.sql`
2. `deployment/auth_schema.sql`
3. `deployment/security_schema.sql`
4. `deployment/giveaway_schema.sql`
5. `deployment/openclaw_schema.sql`
6. `deployment/preorder_schema.sql`
7. `deployment/marketing_roles_schema.sql`

### 1.5 Lancer Maxis
```bash
docker-compose up -d

# Vérifier
docker-compose logs -f maxis
```

**Attendre le message :** "🔌 API de contrôle démarrée"

---

## ÉTAPE 2 : VM 1 - Shellia (Contrôleur)

### 2.1 Créer la VM
- **OS** : Ubuntu 22.04 LTS
- **CPU** : 1-2 vCPU
- **RAM** : 2-4 GB
- **Disk** : 10 GB

### 2.2 Installer Python
```bash
apt update && apt install -y python3 python3-pip git
```

### 2.3 Cloner
```bash
cd /opt
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project
```

### 2.4 Installer dépendances
```bash
pip3 install discord.py aiohttp
```

### 2.5 Configurer
```bash
export SHELLIA_DISCORD_TOKEN=token_bot_shellia
export MAXIS_API_URL=http://IP_VM2:8080/api
export MAXIS_API_KEY=meme_cle_que_vm2
```

### 2.6 Lancer Shellia
```bash
python3 shellia_controller.py
```

**Message attendu :** "🧠 Shellia connectée"

---

## ÉTAPE 3 : Vérification

### Tester la connexion
Dans Discord, taper sur le serveur de Shellia :
```
!maxis status
```

**Résultat attendu :** 🟢 Maxis est en ligne

### Tester une commande
```
!maxis analytics
```

**Doit afficher** les stats de Maxis.

---

## COMMANDES DISPONIBLES

### Shellia (Contrôleur)
```
!maxis status              → État de Maxis
!maxis analytics           → Statistiques
!maxis promo 20% pro 48h   → Lancer promotion
!maxis giveaway 100        → Lancer giveaway
!maxis restart             → Redémarrer Maxis
!maxis report              → Rapport complet
!maxis execute !help       → Exécuter commande sur Maxis
```

### Maxis (Direct)
```
/help                      → Aide Maxis
/shop                      → Boutique
/plans                     → Plans disponibles
/giveaway                  → Giveaways
```

---

## DÉPANNAGE

### "Maxis hors ligne"
```bash
# Sur VM 2
docker-compose ps
docker-compose logs maxis

# Vérifier réseau
curl http://localhost:8080/health
```

### "API Key invalide"
- Vérifier que `MAXIS_API_KEY` est IDENTIQUE sur les 2 VMs
- Redémarrer les deux services

### "Shellia ne répond pas"
```bash
# Sur VM 1
ps aux | grep shellia
python3 shellia_controller.py
```

---

## ARCHITECTURE RÉSEAU

```
Internet
    │
    ├──→ VM 1 (Shellia)
    │       Port: Discord (pas de port exposé)
    │       Sortant: API vers VM 2:8080
    │
    └──→ VM 2 (Maxis)
            Port: Discord + 8080 (API)
            Sortant: Supabase, Stripe, Gemini
```

---

## MAINTENANCE

### Mettre à jour Maxis
```bash
# VM 2
cd /opt/shellia-project
git pull
docker-compose down
docker-compose up -d --build
```

### Mettre à jour Shellia
```bash
# VM 1
cd /opt/shellia-project
git pull
# Relancer le processus Python
```

---

✅ **Une fois déployé, Shellia contrôle Maxis à distance !**
