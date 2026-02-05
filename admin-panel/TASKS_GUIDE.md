# ⏰ Guide des Tâches Planifiées

Le dashboard permet de créer et gérer des tâches répétitives automatiques.

## 🎯 Types de Tâches Disponibles

| Type | Description | Exemples |
|------|-------------|----------|
| **💾 Backup** | Sauvegardes de données | Backup DB quotidien |
| **🧹 Cleanup** | Nettoyage de données anciennes | Suppression logs > 90 jours |
| **📊 Report** | Génération de rapports | Rapport quotidien d'activité |
| **🔔 Notification** | Alertes aux utilisateurs | Notif quota faible |
| **⚙️ Custom** | Tâches personnalisées | Scripts SQL/Python |

## 🚀 Créer une Tâche

### Étape 1: Choisir un template

Dans l'onglet **"⏰ Tâches"**, section **"📦 Templates"** :
- 💾 **backup_database** : Sauvegarde complète DB
- 🧹 **cleanup_old_logs** : Nettoyage logs anciens
- 🧹 **cleanup_rate_limits** : Nettoyage rate limits expirés
- 📊 **generate_daily_report** : Rapport quotidien
- 🔔 **notify_low_quota** : Notif utilisateurs quota faible

### Étape 2: Configurer le Cron

**Fréquences courantes :**

```
Tous les jours à 2h    : 0 2 * * *
Toutes les 6 heures    : 0 */6 * * *
Tous les dimanches     : 0 0 * * 0
Tous les 1er du mois   : 0 0 1 * *
Toutes les 5 minutes   : */5 * * * *
```

**Format Cron :**
```
┌───────────── minute (0 - 59)
│ ┌───────────── heure (0 - 23)
│ │ ┌───────────── jour du mois (1 - 31)
│ │ │ ┌───────────── mois (1 - 12)
│ │ │ │ ┌───────────── jour de la semaine (0 - 6)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

### Étape 3: Création manuelle

1. Cliquez **"➕ Nouvelle tâche"**
2. Remplissez :
   - **Nom** : ex: "Backup quotidien"
   - **Description** : ex: "Sauvegarde complète de la DB"
   - **Type** : Backup
   - **Cron** : `0 2 * * *` (2h du matin)
   - **Fuseau horaire** : Europe/Paris

3. Cliquez **"💾 Créer la tâche"**

## 📊 Surveillance

### Statistiques visibles

- **Tâches actives** : Nombre de tâches activées
- **En cours** : Tâches en exécution actuellement
- **Succès 24h** : Nombre de réussites sur 24h
- **Échecs 24h** : Nombre d'échecs sur 24h

### Statuts des tâches

| Statut | Description | Action |
|--------|-------------|--------|
| 📅 Planifiée | En attente d'exécution | - |
| 🔜 Bientôt | Dans moins d'1 heure | - |
| ⏳ En cours | Exécution en cours | Attendre |
| ⚠️ En retard | Dépassée non exécutée | Vérifier logs |
| ⏸️ Désactivée | Tâche inactive | Activer si besoin |

### Historique d'exécution

Pour chaque exécution :
- **Date** : Quand ça s'est exécuté
- **Durée** : Temps d'exécution en secondes
- **Statut** : ✅ Succès / ❌ Échec / ⏳ En cours
- **Logs** : Cliquez 👁️ pour voir les détails

## 🎮 Actions Disponibles

### Sur une tâche

| Icône | Action | Description |
|-------|--------|-------------|
| ▶️ | **Exécuter** | Lancer manuellement maintenant |
| ✏️ | **Modifier** | Changer la configuration |
| ⏸️/▶️ | **Activer/Désactiver** | Pause/reprise de la tâche |
| 🗑️ | **Supprimer** | Supprimer définitivement |

### Sur une exécution échouée

| Icône | Action | Description |
|-------|--------|-------------|
| 👁️ | **Voir détails** | Logs et erreurs |
| 🔄 | **Réessayer** | Relancer la tâche |

## 🛠️ Tâches Système Prédéfinies

Ces tâches sont créées automatiquement :

### 1. Nettoyage rate limits
```
Type: cleanup
Fréquence: Toutes les 6h
Action: Supprime les rate limits expirés
```

### 2. Archivage conversations
```
Type: cleanup
Fréquence: Tous les jours à 4h
Action: Archive les conversations > 30 jours
```

### 3. Nettoyage sessions
```
Type: cleanup
Fréquence: 2x par jour
Action: Supprime les sessions admin expirées
```

### 4. Rapport quotidien
```
Type: report
Fréquence: Tous les jours à 8h
Action: Génère stats d'activité
```

## 🐛 Dépannage

### "⚠️ En retard"

**Causes possibles :**
1. Le worker de tâches ne tourne pas
2. Erreur lors de l'exécution précédente
3. Tâche bloquée (timeout)

**Solutions :**
```bash
# Vérifier les logs
psql $DATABASE_URL -c "
SELECT * FROM task_executions 
WHERE status = 'failed' 
ORDER BY created_at DESC LIMIT 5;"

# Forcer l'exécution
SELECT execute_task_now('TASK_ID', NULL);
```

### Tâche "En cours" bloquée

```sql
-- Marquer comme failed
UPDATE scheduled_tasks 
SET is_running = FALSE 
WHERE id = 'TASK_ID';

-- Voir l'exécution bloquée
SELECT * FROM task_executions 
WHERE task_id = 'TASK_ID' 
AND status = 'running';
```

### Échec répété

1. Cliquez 👁️ sur l'exécution échouée
2. Lisez le message d'erreur
3. Corrigez le problème (ex: clé API invalide)
4. Cliquez 🔄 pour réessayer

## 🔒 Sécurité

- Les tâches s'exécutent avec les droits `service_role`
- Chaque exécution est loguée dans `task_executions`
- Timeout par défaut : 1 heure
- Max 3 retry en cas d'échec

## 📈 Bonnes Pratiques

1. **Stagger les tâches** : Ne planifiez pas tout à la même heure
   ```
   ❌ 0 2 * * *  (toutes les tâches à 2h)
   ✅ 0 2 * * *  (backup)
   ✅ 0 3 * * *  (cleanup)
   ✅ 0 4 * * *  (report)
   ```

2. **Surveillez les échecs** : Vérifiez régulièrement l'onglet ❌

3. **Testez avant** : Utilisez "▶️ Exécuter" pour tester manuellement

4. **Logs** : Consultez les logs en cas de problème

5. **Fusée horaire** : Utilisez Europe/Paris pour les tâches métier

## 📝 Exemples de Tâches Personnalisées

### Exporter les stats hebdomadaires

```sql
-- Type: custom
-- Cron: 0 9 * * 1 (Lundi 9h)
-- Script SQL:
COPY (
    SELECT 
        DATE_TRUNC('week', created_at) as week,
        COUNT(*) as new_users,
        SUM(messages_sent) as total_messages
    FROM users
    WHERE created_at > NOW() - INTERVAL '1 week'
    GROUP BY 1
) TO '/tmp/weekly_stats.csv' WITH CSV;
```

### Notifier les admins des erreurs

```sql
-- Type: notification
-- Cron: */15 * * * * (toutes les 15 min)
-- Condition: Si des erreurs dans les dernières 15 min
```

---

**Note** : Le système de tâches planifiées nécessite un worker externe (pg_cron, node-cron, ou similar) pour fonctionner en production. Le dashboard permet de configurer les tâches, mais l'exécution réelle doit être gérée par un service externe.
