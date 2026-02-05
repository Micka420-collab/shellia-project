# 🤖 MAXIS + 🧠 SHELLIA - Architecture Dual-VM

```
┌─────────────────────┐         ┌─────────────────────┐
│   🧠 SHELLIA        │  ←──→   │    🤖 MAXIS         │
│   (Contrôleur IA)   │   API   │  (E-commerce Bot)   │
│                     │         │                     │
│  • Intelligence     │         │  • Shop             │
│  • Stratégie        │         │  • Paiements        │
│  • Décisions        │         │  • Giveaways        │
│  • Contrôle Maxis   │         │  • Exécution        │
└─────────────────────┘         └─────────────────────┘
       VM 1                           VM 2
```

## 🎯 Architecture

**Shellia** (VM 1) est l'IA contrôleur qui pilote **Maxis** (VM 2) via une API sécurisée.

### Pourquoi cette architecture ?
- **Sécurité** : Si Maxis est compromis, Shellia reste sûre
- **Scalabilité** : Possibilité d'avoir plusieurs Maxis par Shellia
- **Maintenance** : Mise à jour de Maxis sans toucher Shellia

## 🚀 Déploiement Rapide

### Prérequis
- 2 VMs (ou 1 VM avec 2 conteneurs)
- Docker sur chaque VM
- Clés API Discord

### VM 1 - Shellia (Contrôleur)
```bash
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# Configurer
export SHELLIA_DISCORD_TOKEN=votre_token
export MAXIS_API_KEY=cle_secrete

# Lancer
python shellia_controller.py
```

### VM 2 - Maxis (E-commerce)
```bash
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# Configurer
export MAXIS_DISCORD_TOKEN=votre_token
export MAXIS_API_KEY=cle_secrete

# Lancer
docker-compose up -d
```

## 🎮 Commandes Shellia

Shellia contrôle Maxis via Discord :

```
!maxis status           → Voir état de Maxis
!maxis analytics        → Statistiques
!maxis promo 20% pro 48h → Lancer promotion
!maxis giveaway 100     → Lancer giveaway
!maxis restart          → Redémarrer Maxis
!maxis report           → Rapport complet
```

## 📁 Structure

```
shellia-project/
├── shellia_controller.py    # IA Contrôleur (VM 1)
├── maxis_bot.py             # Bot E-commerce (VM 2)
├── maxis_api.py             # API de contrôle
├── maxis_ecommerce.py       # Module shop
├── maxis_giveaways.py       # Module giveaways
├── maxis_preorder.py        # Module pré-achat
├── maxis_marketing.py       # Module marketing
├── deployment/              # SQL + Docker
└── ARCHITECTURE.md          # Documentation
```

## 🔧 Configuration

Créer un fichier `.env` sur chaque VM :

### VM 1 (Shellia)
```env
SHELLIA_DISCORD_TOKEN=xxx
MAXIS_API_URL=http://maxis-vm:8080/api
MAXIS_API_KEY=cle_secrete_commune
```

### VM 2 (Maxis)
```env
MAXIS_DISCORD_TOKEN=xxx
MAXIS_API_KEY=cle_secrete_commune
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
STRIPE_SECRET_KEY=xxx
```

## 📚 Documentation

- `ARCHITECTURE.md` - Architecture détaillée
- `SHELLIA_GUIDE.md` - Guide déploiement complet (voir le guide général)

## 🛡️ Sécurité

- Clé API entre VMs
- HTTPS/TLS recommandé
- IP Whitelist possible
- Rate limiting intégré

## 📞 Support

En cas de problème :
1. Vérifier `!maxis status`
2. Voir les logs sur les 2 VMs
3. Vérifier la connexion réseau entre VMs

---

**Maxis** = Bot E-commerce  
**Shellia** = IA Contrôleur  
**Version** : 2.1-DUAL-VM
