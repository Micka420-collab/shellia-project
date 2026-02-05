# 🏗️ ARCHITECTURE SHELLIA → MAXIS

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VM SHELLIA (Contrôleur)                         │
│                         Discord Bot : Shellia#1234                      │
│                                                                         │
│  🧠 Shellia IA (Cerveau)                                               │
│  ├── Analyse des demandes                                              │
│  ├── Prise de décisions                                                │
│  ├── Gestion des stratégies                                            │
│  └── Communication avec Maxis                                          │
│                                                                         │
│  🎮 Commandes de contrôle :                                            │
│  ├── !maxis status           → Voir état de Maxis                      │
│  ├── !maxis config           → Configurer Maxis                        │
│  ├── !maxis start/stop       → Démarrer/Arrêter                        │
│  ├── !maxis promo            → Lancer une promotion                    │
│  ├── !maxis analytics        → Voir les stats                          │
│  └── !maxis execute <cmd>    → Exécuter commande sur Maxis             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ API de contrôle (HTTP/WebSocket)
                                    │ Sécurisée (clé API)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         VM MAXIS (E-commerce)                           │
│                         Discord Bot : Maxis#5678                        │
│                                                                         │
│  🤖 Maxis Bot                                                          │
│  ├── E-commerce complet                                                │
│  ├── Paiements Stripe                                                  │
│  ├── Giveaways                                                         │
│  ├── Preorders                                                         │
│  └── Exécution des ordres de Shellia                                   │
│                                                                         │
│  📊 Modules fonctionnels :                                             │
│  ├── maxis_core.py         (Cœur du bot)                               │
│  ├── maxis_ecommerce.py    (Shop, panier, commandes)                   │
│  ├── maxis_giveaways.py    (Giveaways automatiques)                    │
│  ├── maxis_preorder.py     (Pré-achats)                                │
│  ├── maxis_marketing.py    (Rôles marketing)                           │
│  └── maxis_api.py          (API de réception des ordres)               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Communication VM ↔ VM

### Méthode 1 : API REST (Recommandée)
```
Shellia (VM 1)  →  POST https://maxis-vm/api/control  →  Maxis (VM 2)
                        (authentification par clé API)
```

### Méthode 2 : WebSocket (Temps réel)
```
Shellia (VM 1)  ←→  WebSocket  ←→  Maxis (VM 2)
                      (connexion persistante)
```

### Méthode 3 : Base de données partagée
```
Shellia écrit dans DB  →  Maxis lit et exécute
```

## Flux de contrôle

### Exemple : Lancer une promotion

```
1. Admin demande à Shellia (Discord):
   "@Shellia Lance une promotion de 20% sur les plans Pro"
   
2. Shellia analyse et comprend :
   → Créer promotion -20% plan Pro
   → Durée: 48h
   → Cible: utilisateurs inactifs
   
3. Shellia envoie ordre à Maxis via API :
   POST /api/control/promo
   {
       "action": "create_promo",
       "discount": 20,
       "target": "pro_plan",
       "duration": 48,
       "auth_key": "xxx"
   }
   
4. Maxis exécute :
   → Crée la promotion
   → Envoie les messages
   → Confirme à Shellia
   
5. Shellia répond à l'admin :
   "✅ Promotion lancée ! 20% sur les plans Pro pendant 48h."
```

## Sécurité

- **Authentification** : Clé API secrète entre les VMs
- **Chiffrement** : HTTPS/TLS pour toutes les communications
- **IP Whitelist** : Seules les IPs des VMs autorisées
- **Rate Limiting** : Protection contre les abus

## Commandes Shellia (Contrôle Maxis)

| Commande | Description | Exemple |
|----------|-------------|---------|
| `!maxis status` | État de Maxis | Online/Offline |
| `!maxis analytics` | Stats ventes | €500, 12 ventes |
| `!maxis promo <params>` | Lancer promo | `!maxis promo 20% pro 48h` |
| `!maxis giveaway` | Lancer giveaway | `!maxis giveaway 100members` |
| `!maxis config <key> <val>` | Configurer | `!maxis config price_pro 29.99` |
| `!maxis restart` | Redémarrer Maxis | Redémarrage... |
| `!maxis execute <cmd>` | Commande brute | `!maxis execute !announce Promo` |
| `!maxis report` | Rapport complet | Stats de la semaine |

## Avantages de cette architecture

1. **Séparation des responsabilités** :
   - Shellia = Intelligence / Stratégie
   - Maxis = Exécution / E-commerce

2. **Scalabilité** :
   - Possibilité d'avoir plusieurs Maxis contrôlés par une Shellia
   - Ou plusieurs Shellia pour un Maxis

3. **Sécurité** :
   - Si Maxis est compromis, Shellia reste sûre
   - Possibilité de couper Maxis sans perdre Shellia

4. **Maintenance** :
   - Mise à jour de Maxis sans toucher Shellia
   - Tests sur Maxis sans risque pour Shellia
