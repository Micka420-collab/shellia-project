# 🔐 Système de Login Sécurisé - Shellia AI Dashboard

## Architecture de Sécurité

```
┌─────────────────────────────────────────────────────────────┐
│                    PAGE DE LOGIN                            │
│                  (login.html)                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔒 Avant authentification:                                  │
│  • Fond d'écran avec effets visuels (particules)            │
│  • PAS d'accès au dashboard                                  │
│  • PAS de connexion Supabase visible                        │
│  • PAS de fond du dashboard visible                         │
│                                                              │
│  ✅ Après authentification Discord OAuth2:                   │
│  • Redirection vers index.html                              │
│  • Session chiffrée stockée                                 │
│  • Accès complet au dashboard                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Fonctionnalités de Sécurité

### 1. **Page de Login Isolée** (`login.html`)
- **Fond animé** avec particules et effets visuels
- **Pas de contenu sensible** visible avant authentification
- **Design épuré** concentré sur l'authentification

### 2. **Authentification Discord OAuth2**
- Protocole OAuth2 standard
- PKCE (Proof Key for Code Exchange) pour plus de sécurité
- Vérification du state (protection CSRF)

### 3. **Chiffrement de Session**
- Algorithme: **AES-256-GCM**
- Clé dérivée des caractéristiques du navigateur
- Stockage: `sessionStorage` uniquement (pas localStorage)
- Expiration: 24 heures

### 4. **Protection Contre**
- ✅ CSRF (Cross-Site Request Forgery)
- ✅ Replay attacks (timestamp + state)
- ✅ Session hijacking (chiffrement + IP)
- ✅ Man-in-the-middle (HTTPS obligatoire)

## Flux d'Authentification

```
1. Utilisateur arrive sur login.html
   ↓
2. Clique "Continuer avec Discord"
   ↓
3. Redirection vers Discord OAuth
   ↓
4. Autorisation sur Discord
   ↓
5. Retour avec access_token + state
   ↓
6. Vérification du state (CSRF protection)
   ↓
7. Récupération infos utilisateur
   ↓
8. Vérification statut admin (Supabase)
   ↓
9. Création session chiffrée
   ↓
10. Redirection vers index.html
    ↓
11. Dashboard chargé avec accès complet
```

## Fichiers

| Fichier | Description |
|---------|-------------|
| `login.html` | Page de login isolée avec effets visuels |
| `login-styles.css` | Styles avec animations et glassmorphism |
| `login-auth.js` | Logique d'authentification sécurisée |
| `login-effects.js` | Effets visuels (particules, animations) |

## Configuration

### 1. Configurer Discord OAuth

1. [Discord Developer Portal](https://discord.com/developers/applications)
2. Créer une application
3. OAuth2 → General
4. Ajouter redirect URI: `https://votre-domaine.com/login.html`
5. Copier le **Client ID**

### 2. Premier Lancement

```javascript
// Dans la console du navigateur sur login.html
saveAuthConfig('VOTRE_CLIENT_ID_DISCORD');
```

Ou créer un fichier `auth-config.js`:
```javascript
// auth-config.js
sessionStorage.setItem('auth_config', JSON.stringify({
    discordClientId: '1234567890123456789'
}));
```

### 3. Ajouter le Premier Admin

```sql
-- Dans Supabase SQL Editor
INSERT INTO admin_users (discord_id, discord_username, is_super_admin, is_active)
VALUES ('VOTRE_DISCORD_ID', 'VotrePseudo', TRUE, TRUE);
```

## Effets Visuels

### Particules Animées
- Nombre: 50 particules
- Connexions entre particules proches
- Interaction avec la souris
- Couleurs: bleu, violet, cyan

### Fond
- Dégradé animé lentement
- Grille subtile
- Glow central pulsant
- Scanline occasionnelle

### Glassmorphism
- Backdrop blur: 20px
- Bordures translucides
- Ombres douces

## Sécurités Additionnelles

### Content Security Policy (CSP)
```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://cdn.jsdelivr.net;
  connect-src 'self' https://*.supabase.co https://discord.com;
  img-src 'self' https://cdn.discordapp.com;
```

### Headers de Sécurité
```http
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

### Cache Control
```http
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Expires: 0
```

## Accès d'Urgence

En cas de problème avec Discord OAuth:

1. Cliquer sur "Accès d'urgence" sur la page de login
2. Entrer la clé de secours (fournie par super admin)
3. Entrer le code 2FA si activé

**Note**: Les accès d'urgence sont fortement logués.

## Déploiement en Production

### 1. HTTPS Obligatoire
```bash
# Avec Let's Encrypt
certbot --nginx -d votre-domaine.com
```

### 2. Headers de Sécurité (Nginx)
```nginx
server {
    listen 443 ssl;
    server_name votre-domaine.com;
    
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    location / {
        root /var/www/shellia/admin-panel;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. Redirection HTTP vers HTTPS
```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$server_name$request_uri;
}
```

## Maintenance

### Vérifier les Sessions Actives
```sql
SELECT 
    admin_id,
    ip_address,
    created_at,
    expires_at
FROM admin_sessions
WHERE expires_at > NOW()
ORDER BY created_at DESC;
```

### Révoquer Toutes les Sessions
```sql
-- D'un admin spécifique
SELECT revoke_all_admin_sessions('ADMIN_ID');

-- De tous les admins (urgence)
TRUNCATE admin_sessions;
```

### Voir les Tentatives Échouées
```sql
SELECT 
    discord_id,
    action,
    success,
    ip_address,
    created_at
FROM admin_login_logs
WHERE success = FALSE
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

## Dépannage

### "State invalide"
- Cause: Page rafraîchie pendant OAuth ou attaque CSRF
- Solution: Recommencer la connexion

### "Vous n'êtes pas administrateur"
- Cause: Discord ID non dans la table admin_users
- Solution: Ajouter l'utilisateur manuellement dans Supabase

### Session expire rapidement
- Cause: Décalage horaire ou problème de timezone
- Solution: Vérifier que Supabase utilise UTC

### Chiffrement échoue
- Cause: Changement de navigateur/appareil
- Solution: Se reconnecter (la session est liée au navigateur)

## Bonnes Pratiques

1. **Jamais** de credentials en dur dans le code
2. **Toujours** HTTPS en production
3. **Régulièrement** vérifier les logs de sécurité
4. **Immédiatement** révoquer les sessions suspectes
5. **Former** les admins à la sécurité

---

**Ce système de login offre une sécurité enterprise-grade avec une expérience utilisateur moderne.**
