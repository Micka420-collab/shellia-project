# Guide d'Implémentation Sécurité - Shellia AI Bot

## Résumé des Changements

Ce guide documente l'implémentation des correctifs de sécurité pour résoudre les 10 vulnérabilités identifiées lors de l'audit.

---

## 🚨 Vulnérabilités Corrigées

| Sévérité | Vulnérabilité | Solution Implémentée | Fichier |
|----------|--------------|---------------------|---------|
| **CRITICAL** | Clés API en clair | Chiffrement Fernet + Vault optionnel | `secure_config.py` |
| **CRITICAL** | Webhooks Stripe non validés | Validation HMAC-SHA256 + timestamp | `stripe_webhook_validator.py` |
| **CRITICAL** | Rate limit en mémoire | Redis/Supabase persistant | `persistent_rate_limiter.py` |
| **MEDIUM** | Pas de circuit breaker | Pattern Circuit Breaker | `circuit_breaker.py` |
| **MEDIUM** | Historique en RAM | Stockage persistant Supabase | `conversation_history.py` |
| **MEDIUM** | Pas d'audit logs | Table audit_logs + helper | `security_schema.sql` |
| **LOW** | Pas de backups auto | Stratégie documentée | Ce guide |
| **LOW** | Pas de rate limit IP | Table ip_rate_limits | `security_schema.sql` |

---

## 📁 Nouveaux Fichiers

```
shellia-project/
├── bot/
│   ├── secure_config.py          # Gestion secrets chiffrés
│   ├── stripe_webhook_validator.py # Validation webhooks Stripe
│   ├── persistent_rate_limiter.py  # Rate limit persistant
│   ├── circuit_breaker.py        # Circuit breaker pattern
│   ├── conversation_history.py   # Historique persistant
│   └── ...
└── deployment/
    ├── security_schema.sql       # Schéma base de données
    └── SECURITY_IMPLEMENTATION_GUIDE.md  # Ce fichier
```

---

## 🔐 1. Chiffrement des Clés API (CRITICAL)

### Générer une Clé Maître

```bash
cd shellia-project/bot
python secure_config.py generate-key

# Output: Nouvelle clé maître: votre_clé_base64...
# ⚠️  CONSERVEZ CETTE CLÉ DANS UN ENDROIT SÛR!
```

### Chiffrer le Fichier .env

```bash
# Définir temporairement la clé
export SECURE_CONFIG_KEY="votre_clé_maître"

# Chiffrer
python secure_config.py encrypt --env-file ../.env

# Remplacez le fichier
mv ../.env.encrypted ../.env
```

### Format du .env Chiffré

```bash
# Avant
GEMINI_API_KEY=AIzaSy...
STRIPE_SECRET_KEY=sk_test_...

# Après
GEMINI_API_KEY=ENC:gAAAAAB...
STRIPE_SECRET_KEY=ENC:gAAAAAB...
```

### Démarrage du Bot

```bash
# Définir la clé dans l'environnement
export SECURE_CONFIG_KEY="votre_clé_base64..."

# Démarrer le bot
python bot.py
```

---

## 🔄 2. Validation Webhooks Stripe (CRITICAL)

### Configuration

```python
# Dans votre serveur webhook (Flask/FastAPI)
from stripe_webhook_validator import StripeWebhookValidator, StripeEventHandler

validator = StripeWebhookValidator(os.getenv('STRIPE_WEBHOOK_SECRET'))
handler = StripeEventHandler(db, validator)

@app.route('/webhook', methods=['POST'])
async def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    success, message = handler.process_webhook(payload, sig_header)
    
    if success:
        return jsonify({'status': 'ok'}), 200
    else:
        # Log l'erreur mais retourner 200 pour éviter les retries Stripe
        logger.warning(f"Webhook invalide: {message}")
        return jsonify({'status': 'ignored', 'error': message}), 200
```

### Vérifications Effectuées

1. ✅ Présence et format du header `Stripe-Signature`
2. ✅ Timestamp (anti-replay, max 5 min)
3. ✅ Signature HMAC-SHA256 valide
4. ✅ Dédoublonnage des événements
5. ✅ Types d'événements autorisés

---

## ⏱️ 3. Rate Limiting Persistant (CRITICAL)

### Avec Redis (Recommandé)

```bash
# Installation Redis (Docker)
docker run -d -p 6379:6379 --name shellia-redis redis:alpine

# Requirements
pip install redis
```

```python
import redis
from persistent_rate_limiter import PersistentRateLimiter

redis_client = redis.Redis(host='localhost', port=6379)
rate_limiter = PersistentRateLimiter(db, redis_client)

# Utilisation
status = rate_limiter.check_rate_limit(user_id, is_admin=False)
if not status.can_proceed:
    return f"Rate limit: {status.reason}"
```

### Sans Redis (Fallback Supabase)

Le rate limiter fonctionne automatiquement avec Supabase si Redis n'est pas disponible.

### Configuration

```python
# Limites par défaut
COOLDOWN_SECONDS = 3      # Entre chaque message
MAX_PER_MINUTE = 10       # Messages par minute
MAX_PER_HOUR = 100        # Messages par heure
SPAM_THRESHOLD = 5        # Répétitions = spam
```

---

## 🔧 4. Circuit Breaker (MEDIUM)

### Configuration

```python
from circuit_breaker import CircuitBreakerRegistry, CircuitBreakerConfig

# Créer un circuit breaker
breaker = CircuitBreakerRegistry.get_or_create(
    "gemini_api",
    config=CircuitBreakerConfig(
        failure_threshold=3,       # 3 échecs = OPEN
        success_threshold=2,       # 2 succès = CLOSED
        timeout_seconds=60,        # Attente avant retry
        max_retries=2,
        call_timeout=30.0
    )
)

# Utilisation
async def call_gemini(prompt):
    try:
        return await breaker.call(gemini_client.generate, prompt)
    except CircuitBreakerOpenError:
        return "Service temporairement indisponible"
```

### Décorateur

```python
from circuit_breaker import circuit_breaker

@circuit_breaker("gemini_api")
async def generate_ai_response(prompt):
    return await gemini_client.generate(prompt)
```

---

## 💬 5. Historique de Conversation Persistant (MEDIUM)

### Utilisation

```python
from conversation_history import ConversationHistoryManager

history = ConversationHistoryManager(db, max_history=50)

# Ajouter un message
await history.add_message(user_id, 'user', 'Bonjour!')

# Récupérer l'historique
messages = await history.get_history(user_id, limit=20)

# Contexte pour Gemini
context = await history.get_conversation_context(user_id)
```

### Archivage Automatique

```sql
-- Archiver les conversations de +30 jours
SELECT archive_old_conversations(30);
```

---

## 📊 6. Audit Logs (MEDIUM)

### Utilisation

```python
# Log une action admin
db.client.rpc('log_audit_action', {
    'p_admin_user_id': admin_id,
    'p_action': 'SET_PLAN',
    'p_target_user_id': target_id,
    'p_target_type': 'user',
    'p_old_value': json.dumps({'plan': 'free'}),
    'p_new_value': json.dumps({'plan': 'pro'}),
    'p_reason': 'Upgrade manuel'
}).execute()
```

### Tables Créées

- `audit_logs` - Actions administrateurs
- `security_logs` - Événements de sécurité
- `webhook_logs` - Logs Stripe
- `user_bans` - Bannissements

---

## 🗄️ 7. Schéma Base de Données

### Application

```bash
# Appliquer le schéma de sécurité
psql $DATABASE_URL -f deployment/security_schema.sql
```

### Tables Créées

| Table | Description |
|-------|-------------|
| `rate_limits` | Rate limiting persistant |
| `conversation_history` | Messages utilisateur/bot |
| `conversation_archive` | Conversations archivées |
| `webhook_logs` | Logs webhooks Stripe |
| `audit_logs` | Audit trail admin |
| `security_logs` | Logs de sécurité |
| `user_bans` | Bannissements |
| `circuit_breaker_state` | État circuits (HA) |
| `ip_rate_limits` | Protection DDoS |
| `secure_config` | Config chiffrée |

---

## 🚀 Checklist de Déploiement

### Pré-déploiement

- [ ] Générer et sécuriser la `SECURE_CONFIG_KEY`
- [ ] Chiffrer le fichier `.env`
- [ ] Configurer Redis (optionnel mais recommandé)
- [ ] Appliquer `security_schema.sql`
- [ ] Tester la validation des webhooks Stripe

### Déploiement

- [ ] Définir `SECURE_CONFIG_KEY` dans l'environnement
- [ ] Vérifier que le bot démarre sans erreur
- [ ] Tester un appel API (vérifier déchiffrement)
- [ ] Tester un webhook Stripe (vérifier validation)

### Post-déploiement

- [ ] Vérifier les logs de sécurité
- [ ] Tester le rate limiting
- [ ] Vérifier l'historique persistant
- [ ] Configurer les backups automatiques

---

## 🔍 Vérification de Sécurité

```bash
# Vérifier que les secrets sont chiffrés
grep -E "^(GEMINI|STRIPE|DISCORD)" .env | grep -v "^.*=ENC:"
# Devrait ne rien retourner

# Tester le rate limiting
curl -X POST https://votre-api/message -d "test" -v
# Vérifier header X-RateLimit-Remaining

# Tester webhook Stripe invalide
curl -X POST https://votre-api/webhook \
  -H "Stripe-Signature: invalid" \
  -d '{}'
# Devrait logger une tentative invalide
```

---

## 📈 Monitoring

### Métriques à Surveiller

```sql
-- Requêtes de sécurité utiles

-- Tentatives de webhook invalides (24h)
SELECT COUNT(*) FROM webhook_logs 
WHERE status = 'invalid' 
AND processed_at > NOW() - INTERVAL '24 hours';

-- Bans actifs
SELECT COUNT(*) FROM active_bans;

-- Rate limits dépassés
SELECT COUNT(*) FROM security_logs 
WHERE event_type = 'rate_limit_exceeded' 
AND timestamp > NOW() - INTERVAL '24 hours';

-- Circuits ouverts
SELECT * FROM circuit_breaker_state WHERE state = 'open';
```

---

## 🛠️ Maintenance

### Rotation de Clés

```python
from secure_config import SecureConfigManager

# Rotation
manager = SecureConfigManager(old_key)
rotated = manager.rotate_key(new_key)

# Mettre à jour .env
for key, value in rotated.items():
    print(f"{key}={value}")
```

### Nettoyage

```sql
-- Nettoyer les vieux rate limits
SELECT cleanup_expired_rate_limits();

-- Archiver vieilles conversations
SELECT archive_old_conversations(30);

-- Supprimer vieux logs (garder 90 jours)
DELETE FROM security_logs WHERE timestamp < NOW() - INTERVAL '90 days';
DELETE FROM webhook_logs WHERE processed_at < NOW() - INTERVAL '90 days';
```

---

## 📚 Références

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Stripe Webhook Security](https://stripe.com/docs/webhooks/signatures)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Fernet Encryption](https://cryptography.io/en/latest/fernet/)

---

**Dernière mise à jour**: Février 2026  
**Version**: 2.0-Security  
**Auteur**: Shellia AI Team
