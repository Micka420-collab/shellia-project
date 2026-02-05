# 🚀 Démarrage Rapide - Dashboard Admin

Guide rapide pour commencer avec le dashboard de configuration Shellia AI.

## 📸 Aperçu

```
┌──────────────────────────────────────────────────────────────┐
│  🤖 Shellia AI      │  ⚙️ Configuration API                  │
│                     │                                        │
│  📊 Vue d'ensemble  │  🔐 Clé Maître:                        │
│  👥 Utilisateurs    │  [gAAAAAB...              ] [Générer]  │
│  💰 Paiements       │                                        │
│  🔒 Sécurité        │  ───────────────────────────────────── │
│  📈 Analytics       │                                        │
│  ⚙️ Configuration   │  🧠 Google Gemini                      │
│                     │  Clé: [••••••••••••] [👁️] [🧪 Test]    │
│                     │  Status: ✅ 12 modèles disponibles     │
│                     │                                        │
│                     │  💳 Stripe                             │
│                     │  Clé: [••••••••••••] [👁️] [🧪 Test]    │
│                     │  Status: ✅ TestAccount                │
│                     │                                        │
│                     │  💬 Discord                            │
│                     │  Token: [••••••••••••] [👁️] [🧪 Test]   │
│                     │  Status: ✅ ShelliaAI#1234             │
│                     │                                        │
│                     │  [💾 Sauvegarder] [📥 Export] [📤 Imp] │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 3 Étapes pour Configurer

### 1️⃣ Ouvrir le Dashboard

```bash
cd shellia-project/admin-panel

# Option A: Double-clic sur index.html

# Option B: Serveur local (meilleur)
python -m http.server 8080
# → Ouvrir http://localhost:8080
```

### 2️⃣ Se Connecter

Entrez vos credentials Supabase :

```
URL Supabase: https://abcdefgh12345678.supabase.co
Clé service:  eyJhbGciOiJIUzI1NiIs... (service_role)
```

### 3️⃣ Configurer les Clés API

#### Étape A: Générer une Clé Maître
1. Allez dans l'onglet **⚙️ Configuration**
2. Cliquez sur **"🔄 Générer"** pour créer une clé maître
3. **Copiez-la et gardez-la précieusement !**
4. Cliquez **"💾 Sauvegarder la clé maître"**

#### Étape B: Ajouter les Clés API
Pour chaque service :

| Service | Où trouver la clé | Action |
|---------|-------------------|--------|
| **Gemini** | [Google AI Studio](https://makersuite.google.com/app/apikey) | Créer → Copier |
| **Stripe** | [Dashboard Stripe](https://dashboard.stripe.com/apikeys) | Développeurs → Clés API |
| **Discord** | [Discord Dev](https://discord.com/developers/applications) | Votre Bot → Token |
| **Supabase** | [Project Settings](https://app.supabase.com) | Paramètres → API |

1. Collez la clé dans le champ correspondant
2. Cliquez **"🧪 Tester"** pour vérifier
3. Si ✅ → La clé est valide !

#### Étape C: Sauvegarder
1. Cliquez sur **"💾 Sauvegarder toutes les clés"**
2. Les clés sont chiffrées et stockées dans Supabase
3. Un fichier `.env.backup` est téléchargé automatiquement

## 🔄 Mise à Jour des Clés

### Scénario : Clé Gemini expirée

1. Allez dans **⚙️ Configuration**
2. Supprimez l'ancienne clé Gemini
3. Collez la nouvelle clé
4. Cliquez **"🧪 Tester"** pour vérifier
5. Cliquez **"💾 Sauvegarder toutes les clés"**

**✅ Le bot utilisera automatiquement la nouvelle clé !**

## 📥 Import/Export

### Exporter votre config
```
Cliquez "📥 Exporter .env" → Télécharge .env.backup
```

### Importer une config
```
Cliquez "📤 Importer .env" → Sélectionnez votre fichier .env
```

Format supporté :
```bash
GEMINI_API_KEY=AIzaSy...
STRIPE_SECRET_KEY=sk_test_...
DISCORD_TOKEN=MTA...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=eyJ...
```

## 🛡️ Sécurité Checklist

- [ ] Clé maître générée et sauvegardée hors ligne
- [ ] Toutes les clés API sont chiffrées
- [ ] Tests de validation effectués
- [ ] Fichier .env.backup téléchargé
- [ ] Historique des modifications vérifié

## 🐛 Problèmes Courants

### "Test échoué" pour Gemini
```
Cause: CORS (sécurité navigateur)
Solution: Utilisez l'API backend (config_api.py) 
          OU vérifiez la clé manuellement
```

### "Impossible de sauvegarder"
```
Vérifiez:
1. Table 'secure_config' existe dans Supabase
2. Vous utilisez la clé 'service_role'
3. Pas d'erreur dans la console (F12)
```

### "Clé maître invalide"
```
Solution: 
1. Générez-en une nouvelle
2. Assurez-vous qu'elle fait 44 caractères
3. Format: gAAAAAB... (base64)
```

## 📝 Commandes Discord Alternative

Si vous ne voulez pas utiliser le dashboard :

```bash
# Dans Discord (admin uniquement)
/setconfig GEMINI_API_KEY AIzaSy...

# Teste et sauvegarde automatiquement
```

## 🎓 Fonctionnement Technique

```
Vous → Dashboard → Chiffrement (Fernet) → Supabase
                ↓
         localStorage (clé maître uniquement)
```

1. **Clé Maître** : Reste dans votre navigateur
2. **Clés API** : Chiffrées avec AES-128-CBC
3. **Stockage** : Table `secure_config` dans Supabase
4. **Audit** : Table `audit_logs` pour l'historique

## 📞 Besoin d'Aide ?

1. **Console navigateur** : F12 → Console (voir les erreurs)
2. **Logs Supabase** : Table `security_logs`
3. **Documentation** : `admin-panel/README.md`

---

**Prêt en 5 minutes !** 🚀
