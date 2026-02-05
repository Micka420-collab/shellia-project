# ⏰ Démarrage Rapide - Tâches Planifiées

Guide rapide pour créer vos premières tâches répétitives.

## 🎯 En 3 Clics

### 1. Ouvrir l'onglet Tâches
```
Dashboard → ⏰ Tâches
```

### 2. Choisir un Template
Cliquez sur un template prédéfini :
- 💾 **backup_database** - Sauvegarde quotidienne
- 🧹 **cleanup_old_logs** - Nettoyage logs anciens
- 📊 **generate_daily_report** - Rapport d'activité

### 3. Configurer
```
Nom: Backup Quotidien
Fréquence: 0 2 * * * (tous les jours à 2h)
Fuseau horaire: Europe/Paris
```

Cliquez **"💾 Créer la tâche"**

✅ **Fait !** Votre tâche s'exécutera automatiquement.

---

## 📅 Expressions Cron Courantes

| Fréquence | Expression Cron |
|-----------|-----------------|
| Toutes les 5 minutes | `*/5 * * * *` |
| Toutes les heures | `0 * * * *` |
| Tous les jours à 2h | `0 2 * * *` |
| Tous les lundis 9h | `0 9 * * 1` |
| 1er du mois | `0 0 1 * *` |
| Toutes les 6 heures | `0 */6 * * *` |

---

## 🎮 Actions Rapides

### Exécuter maintenant
Cliquez ▶️ sur une tâche pour la lancer immédiatement.

### Voir les logs
Cliquez 👁️ sur une exécution pour voir les détails.

### Désactiver temporairement
Cliquez ⏸️ pour mettre une tâche en pause.

---

## 🛠️ Tâches Recommandées

### 1. Backup quotidien (CRITIQUE)
```
Type: 💾 Backup
Fréquence: 0 2 * * *
Description: Sauvegarde complète DB
```

### 2. Nettoyage logs (IMPORTANT)
```
Type: 🧹 Cleanup
Fréquence: 0 3 * * 0 (dimanche 3h)
Description: Supprime logs > 90 jours
```

### 3. Rapport hebdomadaire (OPTIONNEL)
```
Type: 📊 Report
Fréquence: 0 9 * * 1 (lundi 9h)
Description: Stats de la semaine
```

---

## 🐛 Si ça ne marche pas

### La tâche ne s'exécute pas
1. Vérifiez qu'elle est **activée** (pas ⏸️)
2. Vérifiez l'**heure** (fuseau horaire)
3. Testez manuellement avec ▶️

### Échec répété
1. Cliquez 👁️ sur l'exécution échouée
2. Lisez le **message d'erreur**
3. Corrigez le problème
4. Cliquez 🔄 pour réessayer

---

## 📊 Surveillance

### Indicateurs à surveiller
- **En retard** (⚠️) : Tâche non exécutée à l'heure prévue
- **Échecs 24h** : Nombre d'erreurs récentes
- **En cours** : Tâches en exécution actuellement

### Alertes
Configurez une tâche pour vous alerter :
```
Type: 🔔 Notification
Fréquence: 0 */6 * * * (toutes les 6h)
Condition: Si échecs > 0
```

---

**Vos tâches sont maintenant configurées !** 🎉

Pour plus de détails, consultez `admin-panel/TASKS_GUIDE.md`
