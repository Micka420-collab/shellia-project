# Changements de Sécurité - Shellia AI Bot v2.0

## Résumé Exécutif

Cette mise à jour corrige **10 vulnérabilités de sécurité** identifiées lors de l'audit (3 critiques, 3 moyennes, 4 basses). Tous les correctifs sont rétrocompatibles et peuvent être déployés sans interruption de service.

---

## 🎯 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    SHELLIA AI v2.0                          │
│                  Security Hardening                          │
├─────────────────────────────────────────────────────────────┤
│  🔐 API Keys        │ Chiffrement Fernet (AES-128)          │
│  🔄 Webhooks        │ Validation HMAC-SHA256 + Timestamp    │
│  ⏱️ Rate Limit      │ Redis/Supabase persistant             │
│  🔧 Circuit Breaker │ Protection cascade défaillance        │
│  💬 History         │ Stockage persistant Supabase          │
│  📊 Audit           │ Logs complets admin & sécurité        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure des Fichiers

### Nouveaux Modules de Sécurité

```
shellia-project/
├── bot/
│   ├── secure_config.py              # Gestion secrets chiffrés
│   ├── stripe_webhook_validator.py   # Validation webhooks Stripe
│   ├── persistent_rate_limiter.py    # Rate limit persistant
│   ├── circuit_breaker.py            # Pattern circuit breaker
│   ├── conversation_history.py       # Historique persistant
│   ├── security_integration.py       # Intégration unifiée
│   └── ...
├── deployment/
│   ├── security_schema.sql           # Schéma base sécurité
│   └── SECURITY_IMPLEMENTATION_GUIDE.md
├── SECURITY_CHANGES.md               # Ce fichier
└── .env                              # CHIFFRER CE FICHIER!
```

---

## 🔴 Vulnérabilités Critiques Corrigées

### 1. Clés API en Texte Clair (CRITICAL)

**Problème**: Les clés API étaient stockées en clair dans `.env`

**Impact**: Fuite de credentials si le serveur est compromis

**Solution**: Chiffrement Fernet (AES-128-CBC + HMAC)

```bash
# Avant
GEMINI_API_KEY=AIzaSyABC123...

# Après
GEMINI_API_KEY=ENC:gAAAAAB...
```

**Implémentation**:
```python
from secure_config import SecureConfigManager

config = SecureConfigManager()  # Utilise SECURE_CONFIG_KEY
api_key = config.get_secret('GEMINI_API_KEY', encrypted=True)
```

---

### 2. Webhooks Stripe Non Validés (CRITICAL)

**Problème**: Aucune vérification cryptographique des webhooks

**Impact**: Attaque par falsification de paiements

**Solution**: Validation HMAC-SHA256 avec timestamp anti-replay

```python
from stripe_webhook_validator import StripeWebhookValidator

validator = StripeWebhookValidator('whsec_...')
result = validator.validate_webhook(payload, signature_header)

if not result.is_valid:
    # Rejeter le webhook
    log_security_event('stripe_webhook_invalid')
```

**Vérifications**:
- ✅ Signature HMAC-SHA256
- ✅ Timestamp (±5 min)
- ✅ Dédoublonnage event_id
- ✅ Types d'événements whitelistés

---

### 3. Rate Limiting en Mémoire (CRITICAL)

**Problème**: Les limites étaient perdues au redémarrage du bot

**Impact**: Contournement des limites par redémarrage

**Solution**: Stockage persistant Redis ou Supabase

```python
from persistent_rate_limiter import PersistentRateLimiter

# Avec Redis (recommandé)
redis_client = redis.Redis(host='localhost', port=6379)
rate_limiter = PersistentRateLimiter(db, redis_client)

# Ou fallback Supabase
rate_limiter = PersistentRateLimiter(db)  # Sans Redis

status = rate_limiter.check_rate_limit(user_id)
```

---

## 🟡 Vulnérabilités Moyennes Corrigées

### 4. Pas de Circuit Breaker (MEDIUM)

**Problème**: Échecs en cascade si l'API Gemini est down

**Impact**: Surcharge du bot, timeout utilisateurs

**Solution**: Pattern Circuit Breaker

```python
from circuit_breaker import circuit_breaker, CircuitBreakerConfig

breaker = CircuitBreakerRegistry.get_or_create(
    "gemini_api",
    config=CircuitBreakerConfig(
        failure_threshold=3,    # 3 échecs = OPEN
        success_threshold=2,    # 2 succès = CLOSED
        timeout_seconds=60      # Attente 1 min
    )
)

try:
    response = await breaker.call(gemini_client.generate, prompt)
except CircuitBreakerOpenError:
    return "Service temporairement indisponible"
```

**États**:
- `CLOSED`: Fonctionnement normal
- `OPEN`: Rejette les appels (protection)
- `HALF_OPEN`: Test de récupération

---

### 5. Historique en RAM (MEDIUM)

**Problème**: Historique perdu au redémarrage

**Impact**: Perte du contexte conversationnel

**Solution**: Stockage persistant avec archivage

```python
from conversation_history import ConversationHistoryManager

history = ConversationHistoryManager(db, max_history=50)

# Ajouter
await history.add_message(user_id, 'user', 'Bonjour!')

# Récupérer contexte pour Gemini
context = await history.get_conversation_context(user_id)
```

---

### 6. Pas d'Audit Logs (MEDIUM)

**Problème**: Aucune traçabilité des actions admin

**Impact**: Impossible d'auditer les modifications

**Solution**: Table `audit_logs` avec helper SQL

```sql
-- Logger une action admin
SELECT log_audit_action(
    p_admin_user_id := 123,
    p_action := 'SET_PLAN',
    p_target_user_id := 456,
    p_old_value := '{"plan": "free"}',
    p_new_value := '{"plan": "pro"}'
);
```

**Tables créées**:
- `audit_logs` - Actions administrateurs
- `security_logs` - Événements de sécurité
- `webhook_logs` - Webhooks Stripe
- `user_bans` - Bannissements

---

## 🟢 Vulnérabilités Basses Corrigées

### 7. Pas de Backups Auto (LOW)

**Solution**: Script de backup documenté + Supabase PITR (Point-in-Time Recovery)

```bash
# Backup quotidien (à ajouter au crontab)
0 2 * * * /path/to/backup.sh
```

### 8. Rate Limit par IP (LOW)

**Solution**: Table `ip_rate_limits` pour protection DDoS

```sql
SELECT * FROM check_ip_rate_limit('192.168.1.1', '/api/message', 100);
```

### 9. Pas de Logs de Sécurité (LOW)

**Solution**: Table `security_logs` avec différents niveaux

```python
db.client.table('security_logs').insert({
    'event_type': 'suspicious_login',
    'severity': 'critical',
    'event_data': {'ip': '...', 'attempts': 5}
})
```

### 10. Circuit Breaker Non Distribué (LOW)

**Solution**: Table `circuit_breaker_state` pour HA

---

## 🚀 Guide de Migration Rapide

### Étape 1: Appliquer le Schéma SQL

```bash
# Connexion à Supabase
psql $DATABASE_URL -f deployment/security_schema.sql
```

### Étape 2: Chiffrer les Secrets

```bash
cd shellia-project/bot

# Générer une clé maître
python -c "from secure_config import SecureConfigManager; print(SecureConfigManager.generate_master_key())"

# Output: gAAAAAB...

# Chiffrer le .env
export SECURE_CONFIG_KEY="gAAAAAB..."
python secure_config.py encrypt --env-file ../.env

# Remplacer
mv ../.env.encrypted ../.env
```

### Étape 3: Configurer Redis (Optionnel)

```bash
docker run -d -p 6379:6379 --name shellia-redis redis:alpine
```

### Étape 4: Redémarrer le Bot

```bash
export SECURE_CONFIG_KEY="votre_clé_maître"
python bot.py
```

---

## 📊 Monitoring

### Requêtes SQL Utiles

```sql
-- Vérifier les tentatives de webhook invalides (24h)
SELECT COUNT(*) FROM webhook_logs 
WHERE status = 'invalid' 
AND processed_at > NOW() - INTERVAL '24 hours';

-- Vérifier les circuits ouverts
SELECT circuit_name, state, failure_count 
FROM circuit_breaker_state 
WHERE state != 'closed';

-- Bans actifs
SELECT * FROM active_bans;

-- Actions admin récentes
SELECT * FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 10;
```

### Métriques à Surveiller

| Métrique | Seuil d'Alerte |
|----------|----------------|
| Webhooks invalides | > 10/jour |
| Circuits ouverts | > 0 |
| Rate limits dépassés | > 100/jour |
| Bans actifs | Monitorer |

---

## 🔍 Vérification Post-Déploiement

```bash
# 1. Vérifier chiffrement
grep "^GEMINI_API_KEY" .env | grep "ENC:" && echo "✅ OK" || echo "❌ Non chiffré"

# 2. Tester rate limiting
python security_integration.py check

# 3. Vérifier tables
psql $DATABASE_URL -c "\dt" | grep -E "(rate_limits|audit_logs|security_logs)"

# 4. Tester webhook
python -c "
from bot.stripe_webhook_validator import StripeWebhookValidator
v = StripeWebhookValidator('whsec_test')
print('✅ Module chargé')
"
```

---

## 📚 Documentation

- [Guide d'Implémentation Complète](deployment/SECURITY_IMPLEMENTATION_GUIDE.md)
- [Schéma SQL](deployment/security_schema.sql)
- [API Reference](bot/security_integration.py)

---

## ⚠️ Notes Importantes

1. **NE JAMAIS** commiter la clé maître dans git
2. **TOUJOURS** utiliser HTTPS pour les webhooks en production
3. **CONFIGURER** les backups automatiques (Supabase PITR recommandé)
4 **MONITORER** les logs de sécurité quotidiennement

---

## 📞 Support

En cas de problème:
1. Vérifier les logs: `tail -f logs/security.log`
2. Tester la config: `python security_integration.py check`
3. Consulter le [Guide de Dépannage](deployment/SECURITY_IMPLEMENTATION_GUIDE.md#troubleshooting)

---

**Version**: 2.0-Security  
**Date**: Février 2026  
**Statut**: Prêt pour production
