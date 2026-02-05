# Dashboard Admin - Shellia AI v2.0 🔐

Dashboard sécurisé avec **page de login isolée** et authentification Discord OAuth2.

## 🆕 Nouveau : Login Sécurisé Isolé

```
┌──────────────────────────────────────────────────────────┐
│  🔒 PAGE DE LOGIN (login.html)                           │
│  • Fond avec particules animées                          │
│  • Pas d'accès au dashboard avant auth                   │
│  • OAuth2 Discord uniquement                             │
│  • Session chiffrée AES-256                              │
└──────────────────────────────────────────────────────────┘
                            │
                            │ Auth réussie
                            ▼
┌──────────────────────────────────────────────────────────┐
│  📊 DASHBOARD (index.html)                               │
│  • 7 pages de monitoring                                 │
│  • Accès complet aux données                             │
│  • Gestion des tâches planifiées                         │
└──────────────────────────────────────────────────────────┘
```

## 🚀 Démarrage Rapide (3 minutes)

### 1. Configuration (1 min)

```bash
cd admin-panel

# Copier le fichier de configuration
cp auth-config.example.js auth-config.js

# Éditer auth-config.js avec votre Client ID Discord
# Remplacez: 'VOTRE_CLIENT_ID_DISCORD_ICI'
# Par: '1234567890123456789' (votre vrai ID)
```

**Obtenir votre Client ID Discord:**
1. [Discord Developer Portal](https://discord.com/developers/applications)
2. Créer une application → OAuth2 → General
3. Copier l'"APPLICATION ID"
4. Configurer le Redirect URI: `http://localhost:8080/login.html`

### 2. Lancer (1 min)

```bash
python -m http.server 8080
```

### 3. Premier Accès (1 min)

1. Ouvrez `http://localhost:8080`
2. Vous êtes redirigé vers `login.html`
3. Page de login avec **effets visuels**
4. Cliquez "Continuer avec Discord"
5. Autorisez l'application
6. ✅ Dashboard chargé avec accès complet

## 🔐 Sécurité

### Ce qui est PROTEGE

- ❌ **Pas d'accès** au dashboard sans authentification
- ❌ **Pas de connexion** Supabase legacy visible
- ❌ **Pas de fond** du dashboard avant login
- ❌ **Pas de données** sensibles en clair

### Ce qui est SECURISE

- ✅ **Page login isolée** (`login.html`)
- ✅ **Fond animé** avec particules (pas de contenu sensible)
- ✅ **OAuth2 Discord** (pas de mot de passe stocké)
- ✅ **Session chiffrée** AES-256-GCM
- ✅ **Redirection forcée** si non authentifié
- ✅ **Headers de sécurité** (CSP, HSTS, etc.)

### Architecture

```
Utilisateur
    │
    ├──► login.html (page isolée)
    │     • Fond avec effets
    │     • Auth Discord
    │     • Session chiffrée
    │
    └──► index.html (si auth OK)
          • Dashboard complet
          • Toutes les données
          • Gestion admin
```

## 📁 Structure

```
admin-panel/
├── login.html              ⭐ PAGE DE LOGIN (isolée)
├── login-styles.css        ⭐ Styles avec effets visuels
├── login-auth.js           ⭐ Logique auth sécurisée
├── login-effects.js        ⭐ Particules & animations
├── LOGIN_SECURITY.md       📖 Doc sécurité complète
│
├── index.html              📊 Dashboard (protégé)
├── styles.css              📊 Styles dashboard
├── app.js                  📊 Logique métier
├── auth.js                 📊 Vérification auth
│
├── auth-config.example.js  ⚙️ Config exemple
├── .htaccess               ⚙️ Config Apache
├── nginx.conf              ⚙️ Config Nginx
│
├── SETUP_AUTH.md           📖 Guide config auth
├── TASKS_GUIDE.md          📖 Guide tâches planifiées
└── README.md               📖 Ce fichier
```

## 🎨 Effets Visuels du Login

### Particules Animées
- 50 particules en mouvement
- Connexions dynamiques entre particules
- Interaction avec la souris
- Couleurs: bleu, violet, cyan

### Fond
- Dégradé animé lentement
- Grille subtile
- Glow central pulsant
- Glassmorphism moderne

### Interface
- Design épuré et professionnel
- Animations fluides
- Logo avec effet glitch subtil
- Badge de sécurité visible

## 🔧 Configuration Avancée

### Apache (.htaccess)
Déjà inclus avec:
- Redirection HTTPS
- Headers de sécurité
- Protection fichiers sensibles
- Pas de cache pour auth

### Nginx (nginx.conf)
Fourni avec:
- SSL/TLS configuration
- Rate limiting
- Headers de sécurité
- Redirection automatique

### Content Security Policy
```
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
connect-src 'self' https://*.supabase.co https://discord.com;
img-src 'self' https://cdn.discordapp.com;
```

## 🚨 Déploiement Production

### 1. HTTPS Obligatoire
```bash
certbot --nginx -d votre-domaine.com
```

### 2. Headers de Sécurité
Déjà configurés dans .htaccess / nginx.conf

### 3. Vérification
```bash
# Testez la sécurité
curl -I https://votre-domaine.com/login.html
# Doit afficher: X-Frame-Options: DENY, etc.
```

### 4. Redirection
```bash
# Racine doit rediriger vers login
https://votre-domaine.com/ → https://votre-domaine.com/login.html
```

## 🐛 Dépannage

### "Redirection en boucle"
Cause: Mauvaise configuration du base URL
Solution: Vérifier `auth-config.js` et le redirect URI Discord

### "Page blanche après login"
Cause: SessionStorage non supporté ou bloqué
Solution: Vérifier les paramètres de confidentialité du navigateur

### "State invalide"
Cause: Page rafraîchie pendant OAuth
Solution: Recommencer la connexion

### "Accès refusé"
Cause: Discord ID non dans admin_users
Solution: Ajouter dans Supabase (voir SETUP_AUTH.md)

## 📊 Dashboard Features

Une fois connecté:
- 📊 Vue d'ensemble (stats temps réel)
- 👥 Gestion utilisateurs
- 💰 Suivi des paiements
- 🔒 Centre de sécurité
- 📈 Analytics avancés
- ⚙️ Configuration API
- ⏰ Tâches planifiées (Cron)

## 🛡️ Security Checklist

- [ ] HTTPS activé
- [ ] Client ID Discord configuré
- [ ] Redirect URI Discord configuré
- [ ] Premier admin créé dans Supabase
- [ ] Headers de sécurité activés
- [ ] Rate limiting configuré
- [ ] Logs de sécurité activés
- [ ] Session timeout configuré

## 📞 Support

- Documentation: `LOGIN_SECURITY.md`
- Configuration: `SETUP_AUTH.md`
- Tâches: `TASKS_GUIDE.md`

---

**Votre dashboard est maintenant ultra-sécurisé avec une expérience utilisateur moderne !** 🔐✨

Version: 2.0-Security-OAuth2
