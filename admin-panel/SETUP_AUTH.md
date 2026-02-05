# 🔐 Configuration Authentification Discord OAuth

Guide pour configurer l'authentification Discord sur le dashboard admin.

## 🎯 Résumé

Le dashboard utilise **Discord OAuth2** pour l'authentification :
- ✅ Plus sécurisé que le stockage localStorage
- ✅ Sessions avec expiration automatique
- ✅ Audit trail des connexions
- ✅ Gestion des admins via Discord

---

## 📋 Prérequis

1. Un compte Discord
2. Un serveur Discord (pour tester)
3. Accès au [Discord Developer Portal](https://discord.com/developers/applications)

---

## 🚀 Étapes de Configuration

### Étape 1 : Créer une Application Discord

1. Allez sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Cliquez **"New Application"**
3. Donnez un nom (ex: "Shellia AI Dashboard")
4. Acceptez les conditions
5. Cliquez **"Create"**

### Étape 2 : Configurer l'OAuth2

1. Dans le menu de gauche, cliquez **"OAuth2"** → **"General"**
2. Dans **"Redirects"**, ajoutez votre URL :
   ```
   http://localhost:8080/admin-panel/
   ```
   (ou votre URL de production)
3. Cliquez **"Save Changes"**
4. Copiez le **"Client ID"** (vous en aurez besoin)

### Étape 3 : Copier le Client ID

1. Restez sur la page **"General Information"**
2. Copiez l'**"APPLICATION ID"** (c'est le Client ID)
3. Ça ressemble à : `1234567890123456789`

### Étape 4 : Premier Lancement du Dashboard

1. Ouvrez le dashboard :
   ```bash
   cd shellia-project/admin-panel
   python -m http.server 8080
   ```

2. Ouvrez `http://localhost:8080` dans votre navigateur

3. Vous verrez ce message :
   ```
   ⚙️ Configuration Discord OAuth manquante
   ```

4. Cliquez pour configurer et collez votre **Client ID**

5. Cliquez **"Sauvegarder"**

### Étape 5 : Configurer Supabase

#### A. Appliquer le schéma SQL

```bash
psql $DATABASE_URL -f ../deployment/auth_schema.sql
```

Ou via l'interface Supabase :
1. Allez dans **"SQL Editor"**
2. Créez une **"New query"**
3. Copiez-collez le contenu de `auth_schema.sql`
4. Cliquez **"Run"**

#### B. Ajouter votre premier admin

Dans Supabase SQL Editor :

```sql
-- Remplacez VOTRE_DISCORD_ID par votre vrai ID Discord
-- Pour trouver votre ID : Paramètres utilisateur → Mode développeur → Clic droit sur votre nom → Copier l'identifiant

INSERT INTO admin_users (discord_id, discord_username, is_super_admin, is_active)
VALUES ('VOTRE_DISCORD_ID', 'VotrePseudo', TRUE, TRUE)
ON CONFLICT (discord_id) DO UPDATE 
SET is_super_admin = TRUE, is_active = TRUE;
```

**Pour trouver votre ID Discord :**
1. Discord → Paramètres utilisateur → Avancé
2. Activez **"Mode développeur"**
3. Faites clic droit sur votre nom
4. Cliquez **"Copier l'identifiant"**

### Étape 6 : Test de Connexion

1. Retournez sur le dashboard
2. Cliquez **"Se connecter avec Discord"**
3. Autorisez l'application
4. ✅ Vous êtes connecté !

---

## 🔧 Configuration Avancée

### Ajouter d'autres admins

**Via SQL :**
```sql
INSERT INTO admin_users (discord_id, discord_username, is_super_admin, is_active)
VALUES ('ID_DU_NOUVEL_ADMIN', 'SonPseudo', FALSE, TRUE);
```

**Via le dashboard (super admin uniquement) :**
1. Connectez-vous en super admin
2. Allez dans **"👥 Utilisateurs"**
3. Bientôt : bouton "Promouvoir admin"

### Durée des sessions

Par défaut : **24 heures**

Pour modifier, éditez dans `auth_schema.sql` :
```sql
-- Dans la fonction create_session
p_duration_hours INTEGER DEFAULT 24  -- Changez ici
```

### Révoquer un admin

```sql
UPDATE admin_users 
SET is_active = FALSE 
WHERE discord_id = 'ID_A_REVOLUER';

-- Révoquer toutes ses sessions
SELECT revoke_all_admin_sessions(
    (SELECT id FROM admin_users WHERE discord_id = 'ID_A_REVOLUER')
);
```

---

## 🔒 Sécurité

### Protection contre les attaques

Le système inclut :
- ✅ **Rate limiting** : Max 10 tentatives échouées par IP/heure
- ✅ **CSRF protection** : Vérification du state OAuth
- ✅ **Sessions expirables** : 24h par défaut
- ✅ **Audit trail** : Toutes les connexions sont loguées
- ✅ **IP tracking** : Détection des IPs suspectes

### Bonnes pratiques

1. **Ne partagez jamais** votre Client ID Discord
2. **Utilisez HTTPS** en production (obligatoire pour OAuth)
3. **Révoquez** les sessions inactives régulièrement
4. **Surveillez** les logs de connexion

---

## 🐛 Dépannage

### "Erreur de sécurité: state invalide"

**Cause** : La page a été rafraîchie pendant l'authentification

**Solution** : Recommencez la connexion

### "Accès refusé: vous n'êtes pas administrateur"

**Cause** : Votre Discord ID n'est pas dans la table `admin_users`

**Solution** :
```sql
-- Vérifier si vous êtes admin
SELECT * FROM admin_users WHERE discord_id = 'VOTRE_ID';

-- Si pas de résultat, ajoutez-vous
INSERT INTO admin_users (discord_id, discord_username, is_super_admin, is_active)
VALUES ('VOTRE_ID', 'VotrePseudo', TRUE, TRUE);
```

### "Configuration Discord OAuth manquante"

**Cause** : Le Client ID n'est pas configuré

**Solution** :
1. Ouvrez la console (F12)
2. Tapez : `localStorage.getItem('discord_oauth_config')`
3. Si null, cliquez sur "Configurer" dans le modal

### Sessions qui expirent trop vite

**Cause** : Décalage horaire ou problème de timezone

**Solution** : Vérifiez que Supabase utilise UTC :
```sql
SHOW timezone;
-- Devrait retourner UTC
```

---

## 📊 Monitoring

### Voir les connexions récentes

```sql
SELECT 
    discord_id,
    discord_username,
    action,
    success,
    created_at
FROM admin_login_logs
ORDER BY created_at DESC
LIMIT 20;
```

### Voir les tentatives échouées

```sql
SELECT * FROM recent_failed_logins;
```

### Nettoyer les vieilles sessions

```sql
SELECT cleanup_expired_sessions();
```

---

## 🔄 Migration depuis l'ancien système

Si vous utilisiez l'ancien système (localStorage) :

1. Connectez-vous avec Discord OAuth
2. Les credentials Supabase sont migrés automatiquement
3. Vous pouvez supprimer les anciennes clés :
   ```javascript
   localStorage.removeItem('supabase_url');
   localStorage.removeItem('supabase_key');
   ```

---

## 📝 Résumé des URLs

| URL | Description |
|-----|-------------|
| `http://localhost:8080` | Dashboard en local |
| `https://discord.com/developers/applications` | Discord Developer |
| `https://app.supabase.com` | Console Supabase |

---

## ✅ Checklist de Déploiement

- [ ] Application Discord créée
- [ ] Redirect URI configurée
- [ ] Client ID copié dans le dashboard
- [ ] Schéma SQL appliqué
- [ ] Premier admin créé
- [ ] Test de connexion réussi
- [ ] HTTPS configuré (production)

---

**Le dashboard est maintenant sécurisé avec Discord OAuth !** 🔐✨
