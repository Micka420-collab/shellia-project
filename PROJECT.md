# 🤖 MAXIS - Bot E-commerce Discord

## Architecture

Ce projet utilise une architecture **dual-VM** :

| VM | Rôle | Bot Discord |
|----|------|-------------|
| VM 1 | 🧠 **Shellia** - Contrôleur IA | Shellia#XXXX |
| VM 2 | 🤖 **Maxis** - E-commerce | Maxis#XXXX |

Shellia pilote Maxis via une API sécurisée.

## Fonctionnalités

### 🤖 Maxis (E-commerce)
- Shop avec produits
- Paiements Stripe
- Plans Free/Pro/Ultra
- **Giveaways** automatiques aux paliers
- **Pré-achats** (Early Bird, Founder, Supporter)
- **Rôles marketing** (Ambassadeur, Influenceur, etc.)
- Système économique (coins)

### 🧠 Shellia (Contrôleur)
- Surveillance de Maxis
- Lancement de promotions
- Gestion des giveaways
- Rapports analytics
- Décisions stratégiques

## Déploiement

### Rapide (pour test)
```bash
# Sur une seule VM
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project
cp .env.example .env
# Éditer .env avec les tokens
docker-compose up -d
```

### Production (Dual-VM)
Voir `DEPLOY_DUAL_VM.md`

## Commandes

### Contrôler Maxis (via Shellia)
```
!maxis status      → État de Maxis
!maxis analytics   → Stats
!maxis promo ...   → Lancer promo
!maxis giveaway    → Lancer giveaway
```

### Utiliser Maxis (direct)
```
/shop              → Boutique
/plans             → Voir les plans
/giveaway          → Participer giveaway
```

## Structure

```
shellia-project/
├── shellia_controller.py    # VM 1 - Contrôleur
├── maxis_bot.py             # VM 2 - Bot principal
├── maxis_api.py             # API de contrôle
├── maxis_ecommerce.py       # Module shop
├── maxis_giveaways.py       # Module giveaways
├── maxis_preorder.py        # Module pré-achat
├── maxis_marketing.py       # Module marketing
├── docker-compose.yml       # Docker Maxis
├── DEPLOY_DUAL_VM.md        # Guide déploiement
└── SHELLIA_INSTRUCTIONS.md  # Instructions Shellia
```

## Documentation

- `ARCHITECTURE.md` - Architecture détaillée
- `DEPLOY_DUAL_VM.md` - Guide déploiement complet
- `SHELLIA_INSTRUCTIONS.md` - Instructions pour Shellia

## Version

**2.1-DUAL-VM** - Production Ready

---

*Shellia contrôle Maxis. Maxis gère le e-commerce.*
