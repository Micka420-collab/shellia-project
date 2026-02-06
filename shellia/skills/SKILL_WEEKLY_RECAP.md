# 📅 SKILL: Weekly Recap (Rapport Hebdomadaire)

## Description
Génération automatique de rapports hebdomadaires complets avec analyse IA pour le channel admin tous les lundis.

---

## 🕐 Déclenchement

```python
# Cron: Tous les lundis à 9h00
SCHEDULE = "0 9 * * 1"  # Lundi 9h00

async def generate_weekly_recap():
    week_data = await collect_week_data()
    analysis = await analyze_with_gemini(week_data)
    await post_to_admin_channel(analysis)
```

---

## 📊 Données Collectées

### 1. Communauté
```python
community_metrics = {
    "new_members": await get_new_members_last_7d(),
    "total_members": guild.member_count,
    "active_members": await get_active_members_last_7d(),
    "messages_sent": await get_message_count_last_7d(),
    "growth_rate": calculate_growth(),
    "left_members": await get_members_left(),
    "retention_rate": calculate_retention()
}
```

### 2. Économie
```python
economy_metrics = {
    "revenue": await get_revenue_last_7d(),
    "new_orders": await get_new_orders(),
    "new_subscriptions": await get_new_subs(),
    "churned_subscriptions": await get_churned(),
    "mrr": calculate_mrr(),
    "arr": calculate_arr(),
    "arpu": calculate_arpu(),
    "ltv": calculate_ltv()
}
```

### 3. Support
```python
support_metrics = {
    "tickets_created": await get_tickets_created(),
    "tickets_resolved": await get_tickets_resolved(),
    "avg_resolution_time": await get_avg_resolution_time(),
    "satisfaction_score": await get_csat(),
    "sla_compliance": await get_sla_compliance(),
    "top_categories": await get_top_ticket_categories()
}
```

### 4. Marketing
```python
marketing_metrics = {
    "new_ambassadors": await get_new_ambassadors(),
    "referrals": await get_referral_count(),
    "social_mentions": await get_social_mentions(),
    "content_created": await get_ugc_count(),
    "engagement_rate": await get_engagement_rate()
}
```

### 5. Technique
```python
tech_metrics = {
    "uptime": await get_uptime(),
    "avg_response_time": await get_api_latency(),
    "errors_count": await get_error_count(),
    "commands_used": await get_command_usage()
}
```

---

## 🤖 Analyse Gemini

```python
async def analyze_with_gemini(data: dict) -> str:
    prompt = f"""
    Tu es Shellia, l'IA analytique de la communauté.
    Analyse ces données hebdomadaires et génère un rapport engageant:
    
    DONNÉES BRUTES:
    {json.dumps(data, indent=2)}
    
    INSTRUCTIONS:
    1. Mets en évidence les points positifs avec des emojis
    2. Identifie les alertes ou points d'attention
    3. Compare avec la semaine précédente
    4. Donne 2-3 recommandations concrètes
    5. Format: Discord-friendly avec sections claires
    6. Ton: Professionnel mais enthousiaste
    7. Longueur: 1500-2000 caractères max
    
    STRUCTURE ATTENDUE:
    - Titre accrocheur avec résumé
    - 📈 Section communauté
    - 💰 Section économie  
    - 🎫 Section support
    - 🎯 Section marketing
    - ⚡ Section technique
    - 💡 Recommandations finales
    """
    
    response = await gemini.generate(prompt)
    return response.text
```

---

## 💬 Format de Sortie (Exemple)

```
Shellia: "📊 **Weekly Recap - Semaine 3 Janvier 2024**

🎉 Encore une excellente semaine pour la communauté !

═══════════════════

📈 **COMMUNAUTÉ**
• +127 nouveaux membres (+15% vs semaine dernière) 🚀
• 3,245 messages échangés
• Taux de rétention: 94% (excellent !)
• On approche des **500 membres** - préparez le giveaway !

💰 **ÉCONOMIE**
• Revenue: €2,340 (+8%)
• 23 nouveaux Pro, 4 Ultra, 1 Founder
• MRR actuel: €8,950
• Churn: seulement 2% 👏

🎫 **SUPPORT**
• 45 tickets ouverts, 42 résolus
• Temps moyen: 18h (objectif: 24h) ✅
• Satisfaction: 4.8/5 ⭐
• ⚠️ 3 tickets critiques > 12h - besoin d'attention

🎯 **MARKETING**
• 5 nouveaux Ambassadors
• 12 codes affiliés créés
• Giveaway 100 membres: 89 participants
• Top referreur: @Alice (€340 générés)

⚡ **TECHNIQUE**
• Uptime: 99.98% 
• Latence moyenne: 45ms
• 0 incidents majeurs
• 12,450 commandes traitées

═══════════════════

💡 **RECOMMANDATIONS CETTE SEMAINE:**

1. **Lancer le giveaway 500 membres** → On est à 489, ça va déclencher bientôt !

2. **Follow-up churn** → 2 users ont annulé, lancer campagne winback

3. **Article FAQ** → 40% des tickets = questions récurrentes, créer self-service

═══════════════════

🗓️ **Objectifs Semaine Prochaine:**
• Atteindre 550 membres
• Maintenir churn < 3%
• Résoudre tickets < 20h moyenne

Bonne semaine à tous ! 💪"
```

---

## 🎨 Variantes de Format

### Version Courte (Busy Week)
```
Shellia: "📊 **Quick Recap**

✅ Good: +89 membres, €1,890 revenue, 4.9/5 support
⚠️ Watch: 5 tickets > 24h, serveur latency +20%
🎯 Next: Préparer giveaway 500, fix API cache

Détails: [Dashboard]"
```

### Version Détaillée (Review)
```
[Full report avec graphiques embed, tableaux, liens cliquables]
```

### Version Alertes (Problems)
```
Shellia: "🚨 **Weekly Alert Report**

3 problèmes nécessitent votre attention:

1. **Support SLA dépassé** - 8 tickets > 48h
2. **Churn élevé** - 5% cette semaine (vs 2% normale)
3. **Erreurs API** - +300% erreurs 500

Actions recommandées:
→ Augmenter staff support
→ Analyse cohorte churn
→ Rollback dernier deploy

[Voir détails]"
```

---

## 📈 Visualisations (Embeds Discord)

### Graphique de Croissance
```python
embed = discord.Embed(
    title="📈 Courbe de Croissance",
    description="```\nJ+0:  ████ 400\nJ+1:  █████ 450 (+12%)\nJ+2:  ██████ 489 (+9%)\nJ+3:  ███████ 510 (+4%)\nJ+4:  ████████ 542 (+6%)\nJ+5:  █████████ 567 (+5%)\nJ+6:  ██████████ 589 (+4%)\nJ+7:  ███████████ 612 (+4%)  🎉\n```"
)
```

### Leaderboard
```
🏆 Top Contributeurs Cette Semaine:

🥇 @Alice - 234 messages, 45 invites
🥈 @Bob - 189 messages, 23 invites  
🥉 @Charlie - 156 messages, 12 invites

💎 Top Ambassadeurs Revenue:
1. @Alice - €340
2. @Bob - €280
3. @Dave - €195
```

---

## 🔧 Personnalisation

### Filtres par Rôle
```python
async def send_targeted_recap():
    # Admin version - tout
    await admin_channel.send(full_recap)
    
    # Mod version - focus modération
    mod_recap = filter_for_mods(full_recap)
    await mod_channel.send(mod_recap)
    
    # Public version - highlights
    public_recap = filter_public(full_recap)
    await general_channel.send(public_recap)
```

### Fréquence Ajustable
```python
RECAP_SCHEDULES = {
    "daily": {"cron": "0 9 * * *", "detail": "brief"},
    "weekly": {"cron": "0 9 * * 1", "detail": "full"},
    "monthly": {"cron": "0 9 1 * *", "detail": "comprehensive"}
}
```

---

## 🎯 KPIs Tracks

```yaml
community_health:
  - growth_rate > 5%: 🟢 | 0-5%: 🟡 | < 0%: 🔴
  - retention > 90%: 🟢 | 80-90%: 🟡 | < 80%: 🔴
  
financial_health:
  - mrr_growth > 10%: 🟢 | 0-10%: 🟡 | < 0%: 🔴
  - churn < 5%: 🟢 | 5-10%: 🟡 | > 10%: 🔴
  
support_health:
  - csat > 4.5: 🟢 | 4.0-4.5: 🟡 | < 4.0: 🔴
  - sla_compliance > 95%: 🟢 | 90-95%: 🟡 | < 90%: 🔴
```
