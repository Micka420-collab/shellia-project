# Checklist de Déploiement Sécurité - Shellia AI Bot v2.0

## 📋 Résumé des Livrables

### Modules de Sécurité Créés

| Fichier | Description | Lignes |
|---------|-------------|--------|
| `bot/secure_config.py` | Chiffrement Fernet des secrets | 440 |
| `bot/stripe_webhook_validator.py` | Validation HMAC webhooks | 380 |
| `bot/persistent_rate_limiter.py` | Rate limit Redis/Supabase | 370 |
| `bot/circuit_breaker.py` | Pattern Circuit Breaker | 370 |
| `bot/conversation_history.py` | Historique persistant | 380 |
| `bot/security_integration.py` | Intégration unifiée | 400 |
| `deployment/security_schema.sql` | Schéma DB sécurité | 470 |

**Total**: ~2,800 lignes de code de sécurité

---

## ✅ Checklist de Déploiement

### Phase 1: Préparation (Local)

- [ ] **1.1** Installer les dépendances
```bash
cd shellia-project/bot
pip install -r requirements.txt
```

- [ ] **1.2** Vérifier les modules
```bash
python check_security.py
```

- [ ] **1.3** Générer la clé maître
```bash
cd bot
python -c "from secure_config import SecureConfigManager; print(SecureConfigManager.generate_master_key())"
# Copier la clé générée
```

- [ ] **1.4** Chiffrer le fichier .env
```bash
export SECURE_CONFIG_KEY="votre_clé_copiée"
python secure_config.py encrypt --env-file ../.env
mv ../.env.encrypted ../.env
```

- [ ] **1.5** Vérifier le chiffrement
```bash
grep "^GEMINI" ../.env | grep "ENC:" && echo "✅ OK" || echo "❌ Échec"
```

### Phase 2: Base de Données

- [ ] **2.1** Appliquer le schéma SQL
```bash
psql $SUPABASE_URL -f ../deployment/security_schema.sql
```

- [ ] **2.2** Vérifier les tables créées
```sql
\dt
-- Doit afficher: rate_limits, conversation_history, webhook_logs, 
-- audit_logs, security_logs, user_bans, circuit_breaker_state, 
-- ip_rate_limits, secure_config
```

- [ ] **2.3** Vérifier les index
```sql
\di
-- Vérifier que les index sur user_id et timestamps existent
```

### Phase 3: Redis (Optionnel mais Recommandé)

- [ ] **3.1** Démarrer Redis
```bash
docker run -d -p 127.0.0.1:6379:6379 --name shellia-redis redis:alpine
```

- [ ] **3.2** Tester la connexion
```bash
redis-cli ping
# Doit retourner: PONG
```

### Phase 4: Déploiement

- [ ] **4.1** Configurer les variables d'environnement
```bash
export SECURE_CONFIG_KEY="votre_clé_maître"
export REDIS_URL="redis://localhost:6379/0"  # Si Redis utilisé
```

- [ ] **4.2** Tester le démarrage
```bash
cd bot
python -c "
from security_integration import SecurityIntegration
from supabase_client import SupabaseDB

db = SupabaseDB()
security = SecurityIntegration(db)
import asyncio
asyncio.run(security.initialize())
print('Statut:', security.get_stats())
"
```

- [ ] **4.3** Démarrer le bot
```bash
python bot.py
```

### Phase 5: Tests Post-Déploiement

- [ ] **5.1** Tester le rate limiting
```bash
# Envoyer 15 messages rapidement au bot
# Le 11ème devrait être bloqué
```

- [ ] **5.2** Tester un webhook Stripe invalide
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Stripe-Signature: invalid" \
  -d '{}'
# Doit logger une tentative invalide
```

- [ ] **5.3** Vérifier les logs de sécurité
```sql
SELECT * FROM security_logs 
ORDER BY timestamp DESC 
LIMIT 10;
```

- [ ] **5.4** Tester l'historique persistant
```sql
SELECT COUNT(*) FROM conversation_history;
-- Doit augmenter après chaque conversation
```

### Phase 6: Monitoring

- [ ] **6.1** Configurer les alertes
```sql
-- Créer une vue pour monitoring
CREATE VIEW security_dashboard AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) FILTER (WHERE event_type = 'stripe_webhook_invalid') as invalid_webhooks,
    COUNT(*) FILTER (WHERE event_type = 'rate_limit_exceeded') as rate_limits,
    COUNT(*) FILTER (WHERE severity = 'critical') as critical_events
FROM security_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1 DESC;
```

- [ ] **6.2** Configurer les backups
```bash
# Supabase PITR (Point-in-Time Recovery) est recommandé
# Ou script de backup quotidien
```

---

## 🔍 Validation Finale

Avant de mettre en production, vérifier:

| Vérification | Méthode | Résultat Attendu |
|--------------|---------|------------------|
| Secrets chiffrés | `grep "^GEMINI" .env` | Commence par `ENC:` |
| Webhook validé | Stripe Dashboard | 100% succès |
| Rate limit actif | Test 15 msg/min | 11ème bloqué |
| Historique persistant | Redémarrage bot | Contexte conservé |
| Circuit breaker | Simuler échec API | Passage en OPEN |
| Audit logs | Action admin | Entrée dans audit_logs |

---

## 🚨 Procédure de Rollback

En cas de problème:

```bash
# 1. Arrêter le bot
pkill -f bot.py

# 2. Restaurer l'ancien .env (non chiffré)
cp .env.backup .env

# 3. Redémarrer sans chiffrement
unset SECURE_CONFIG_KEY
python bot.py
```

---

## 📚 Documentation

- [Guide d'Implémentation Complète](deployment/SECURITY_IMPLEMENTATION_GUIDE.md)
- [Changements de Sécurité](SECURITY_CHANGES.md)
- [Schéma SQL](deployment/security_schema.sql)
- [Tests Unitaires](tests/test_security.py)

---

## 📞 Support

En cas de problème:
1. Consulter les logs: `tail -f logs/security.log`
2. Vérifier la config: `python check_security.py`
3. Tester l'intégration: `python bot/security_integration.py check`

---

**Date de déploiement**: ___________  
**Responsable**: ___________  
**Version**: 2.0-Security
