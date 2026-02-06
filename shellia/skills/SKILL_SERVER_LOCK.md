# 🔒 SKILL: Server Lock

## Description
Verrouillage complet et total du serveur Discord. Empêche TOUTE entrée même avec invitations existantes ou liens d'affiliation.

---

## ⚡ Fonctionnement

Quand le serveur est **LOCK**:
- ❌ **Aucune entrée possible**
- ❌ **Toutes les invitations révoquées** automatiquement
- ❌ **Création d'invitations bloquée** (même pour mods)
- ❌ **Widget serveur désactivé**
- ❌ **Discovery désactivé**
- ❌ **Liens d'affiliation inactifs**
- ❌ **Nouveaux membres kick instantanément**

**Seuls les ADMINISTRATEURS peuvent déverrouiller.**

---

## 🛡️ Mesures de Sécurité

### 1. Révocation d'Invitations
```python
async def revoke_all_invites(guild):
    invitations = await guild.invites()
    for invite in invitations:
        await invite.delete(reason="Serveur verrouillé")
```

### 2. Blocage Création Invites
```python
# Permissions retirées à tous les rôles sauf admin
for role in guild.roles:
    if role.name.lower() not in ['admin', 'owner']:
        await role.edit(permissions=Permissions(
            create_instant_invite=False
        ))
```

### 3. Kick Automatique
```python
async def on_member_join(member):
    if server_is_locked:
        if not is_admin(member):
            await member.send("🔒 Serveur temporairement fermé")
            await member.kick(reason="Serveur verrouillé")
```

### 4. Widget & Discovery
```python
await guild.edit(
    widget_enabled=False,
    discoverable=False
)
```

---

## 📡 Commandes

### Verrouiller le Serveur
```
!server_lock [raison]
```

**Confirmation requise:**
```
⚠️ CONFIRMATION REQUISE

Vous allez FERMER le serveur.

Raison: Maintenance

Conséquences:
• ❌ Aucune entrée possible
• ❌ Toutes les invitations révoquées
• ❌ Liens d'affiliation inactifs
• ❌ Widget serveur désactivé

Seul un administrateur pourra rouvrir.

[Bouton: CONFIRMER LA FERMETURE 🔒]
```

### Déverrouiller
```
!server_unlock
```

**Seuls les administrateurs peuvent utiliser cette commande.**

### Voir le Statut
```
!server_status
```

### Mode "Nuke" (Kick All + Lock)
```
!server_kick_all [raison]
```

⚠️ **Expulse TOUS les membres non-staff** puis verrouille.

---

## 💬 Utilisation par Shellia

### Scénario 1: Verrouillage maintenance
```
Admin: !server_lock Maintenance système 2h

Shellia: "🔒 **SERVEUR FERMÉ**

Le serveur est maintenant verrouillé.

Raison: Maintenance système 2h
Par: @Admin

🚫 Aucune entrée possible
🚫 Invitations révoquées
🚫 Widget désactivé

Réouverture prévue: Dans 2 heures"
```

### Scénario 2: Tentative d'entrée bloquée
```
[Nouveau membre tente de rejoindre via lien affiliation]

→ Kick automatique
→ DM envoyé:

"🔒 **Shellia Community** est temporairement fermé.

Raison: Maintenance système 2h

Le serveur rouvrira bientôt.
Revenez plus tard !"
```

### Scénario 3: Déverrouillage
```
Admin: !server_unlock

Shellia: "🔓 **SERVEUR ROUVERT !**

Le serveur est de nouveau ouvert !

✅ Invitations actives
✅ Liens d'affiliation fonctionnels
✅ Widget réactivé

Bienvenue à tous ! 🎉"
```

### Scénario 4: Kick all + lock (raid protection)
```
Admin: !server_kick_all Raid détecté

Shellia: "🔒👢 **SERVEUR VIDÉ ET FERMÉ**

Protection anti-raid activée.

• 342 membres non-staff expulsés
• Toutes les invitations révoquées
• Serveur verrouillé

Les membres légitimes devront être réinvités manuellement."
```

---

## 🔗 Cas d'Usage

| Cas | Commande |
|-----|----------|
| Maintenance | `!server_lock Maintenance 2h` |
| Mise à jour majeure | `!server_lock Mise à jour v2.0` |
| Raid en cours | `!server_kick_all Raid détecté` |
| Fermeture temporaire | `!server_lock Vacances staff` |
| Incident sécurité | `!server_lock Incident en cours` |

---

## ⚠️ Avertissements

```diff
+ Seuls les administrateurs peuvent déverrouiller
+ Les owners peuvent toujours entrer (sécurité)
+ Les bots restent dans le serveur

- Les membres kickés doivent être réinvités
- Les invitations permanentes sont perdues
- Les liens vanity sont désactivés
```

---

## 📊 Logs & Audit

Toutes les actions sont loguées:
```json
{
  "action": "server_lock",
  "user_id": "123456789",
  "timestamp": "2024-01-20T14:30:00Z",
  "reason": "Maintenance",
  "invites_revoked": 45,
  "members_kicked": 0
}
```
