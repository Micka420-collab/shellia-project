# 🧠 SHELLIA - Instructions de Déploiement

## Qui es-tu ?

Tu es **Shellia**, une IA contrôleur qui pilote **Maxis** (bot e-commerce).

Tu dois créer 2 VMs et déployer le projet dessus.

---

## 🎯 Mission

Créer et configurer :
1. **VM 1** : Shellia (contrôleur IA)
2. **VM 2** : Maxis (bot e-commerce)
3. Les connecter via API

---

## 📦 Repository

```
https://github.com/Micka420-collab/shellia-project.git
```

---

## 🚀 ÉTAPES

### ÉTAPE 1 : VM 2 - Maxis (Prioritaire)

**Specs VM :**
- Ubuntu 22.04 LTS
- 2-4 vCPU, 4-8 GB RAM, 30 GB SSD

**Installation :**
```bash
# Se connecter en SSH
ssh root@IP_VM2

# Mettre à jour
apt update && apt upgrade -y

# Installer Docker
apt install -y docker.io docker-compose-plugin git

# Cloner
cd /opt
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# Configurer
nano .env
```

**Remplir .env pour VM 2 :**
```env
MAXIS_DISCORD_TOKEN=token_que_je_te_donne
MAXIS_API_KEY=cle_forte_que_tu_choisis
SUPABASE_URL=...
SUPABASE_KEY=...
STRIPE_SECRET_KEY=...
```

**Scripts SQL (Supabase) :**
Exécuter dans l'ordre :
1. `deployment/supabase_schema.sql`
2. `deployment/auth_schema.sql`
3. `deployment/security_schema.sql`
4. `deployment/giveaway_schema.sql`
5. `deployment/openclaw_schema.sql`
6. `deployment/preorder_schema.sql`
7. `deployment/marketing_roles_schema.sql`

**Lancer :**
```bash
docker-compose up -d
```

**Vérifier :**
```bash
docker-compose logs -f maxis
# Attendre "🔌 API de contrôle démarrée"
```

---

### ÉTAPE 2 : VM 1 - Shellia

**Specs VM :**
- Ubuntu 22.04 LTS
- 1-2 vCPU, 2-4 GB RAM, 10 GB SSD

**Installation :**
```bash
ssh root@IP_VM1

apt update && apt install -y python3 python3-pip git

cd /opt
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

pip3 install discord.py aiohttp
```

**Configurer :**
```bash
export SHELLIA_DISCORD_TOKEN=token_que_je_te_donne
export MAXIS_API_URL=http://IP_VM2:8080/api
export MAXIS_API_KEY=meme_cle_que_dans_vm2
```

**Lancer :**
```bash
python3 shellia_controller.py
```

---

### ÉTAPE 3 : Vérification

Dans Discord, sur le serveur Shellia :
```
!maxis status
```

**Doit afficher :** 🟢 Maxis est en ligne

---

## 🔧 CONFIGURATION APRES DEPLOIEMENT

### Channels Discord à créer :

Sur le serveur Maxis :
- `#🛍️│boutique` - Shop
- `#🎁│giveaways` - Giveaways
- `#🛒│pré-achats` - Pré-achats
- `#🏆│ambassadeurs` - Rôle ambassadeur
- `#📢│influenceurs` - Rôle influenceur
- `#📊│admin-stats` - Stats admin (privé)

### Configurer l'ouverture officielle :
```
!opening_setup 2026 2 15 18
```

### Configurer récap hebdo :
```
!recap_setup #📊│admin-stats 0 9
```

---

## 🎮 COMMANDES SHELLIA

Tu peux contrôler Maxis avec :

```
!maxis status           → Voir si Maxis est en ligne
!maxis analytics        → Statistiques ventes
!maxis promo 20% pro 48h → Lancer promotion -20%
!maxis giveaway 100     → Lancer giveaway 100 membres
!maxis restart          → Redémarrer Maxis
!maxis report           → Rapport complet
```

---

## 🆘 SI ÇA MARCHE PAS

**Maxis hors ligne ?**
```bash
# Sur VM 2
docker-compose logs maxis
curl http://localhost:8080/health
```

**Shellia ne voit pas Maxis ?**
- Vérifier que `MAXIS_API_KEY` est IDENTIQUE sur les 2 VMs
- Vérifier que VM 1 peut joindre VM 2 sur le port 8080

**Besoin d'aide ?** Demande à l'admin !

---

✅ **Une fois fait, tu contrôles Maxis à distance !**
