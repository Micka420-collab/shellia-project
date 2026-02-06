# Configuration Discord OAuth avec Supabase

## 1. Créer une application Discord

1. Allez sur https://discord.com/developers/applications
2. Cliquez sur "New Application"
3. Donnez un nom à votre application (ex: "Shellia AI")
4. Allez dans l'onglet "OAuth2" → "General"

### Redirect URLs à ajouter :
```
http://localhost:5500/auth/callback.html          (développement local)
https://votredomaine.com/auth/callback.html       (production)
```

### Récupérer les identifiants :
- **Client ID** : Copiez la valeur
- **Client Secret** : Générez et copiez la valeur (gardez-la secrète !)

## 2. Configurer Supabase Auth

1. Allez sur votre dashboard Supabase
2. Allez dans "Authentication" → "Providers"
3. Activez "Discord"
4. Entrez :
   - **Client ID** (de Discord)
   - **Client Secret** (de Discord)
5. Enregistrez

## 3. Mettre à jour le code

Dans les fichiers suivants, remplacez les valeurs :

### `js/supabase-config.js`
```javascript
const SUPABASE_URL = 'https://votre-projet.supabase.co';
const SUPABASE_ANON_KEY = 'votre-clé-anon-publique';
```

### `auth/callback.html`
```javascript
const SUPABASE_URL = 'https://votre-projet.supabase.co';
const SUPABASE_ANON_KEY = 'votre-clé-anon-publique';
```

### `user-dashboard.html`
```javascript
const SUPABASE_URL = 'https://votre-projet.supabase.co';
const SUPABASE_ANON_KEY = 'votre-clé-anon-publique';
```

## 4. Créer la table profiles (optionnel)

Dans l'éditeur SQL Supabase :

```sql
create table profiles (
  id uuid references auth.users on delete cascade,
  discord_id text,
  username text,
  avatar_url text,
  email text,
  created_at timestamp with time zone default timezone('utc'::text, now()),
  updated_at timestamp with time zone default timezone('utc'::text, now()),
  
  primary key (id)
);

-- Activer RLS
alter table profiles enable row level security;

-- Politiques
create policy "Users can view own profile"
  on profiles for select
  using ( auth.uid() = id );

create policy "Users can update own profile"
  on profiles for update
  using ( auth.uid() = id );
```

## 5. Flux d'authentification

```
1. Utilisateur clique "Connexion avec Discord"
   ↓
2. Redirection vers discord.com/oauth2/authorize
   ↓
3. Utilisateur autorise l'application
   ↓
4. Discord redirige vers /auth/callback.html?code=xxx
   ↓
5. Supabase échange le code contre une session
   ↓
6. Utilisateur connecté → redirection dashboard
```

## 6. Permissions Discord demandées

- **identify** : Accès au nom d'utilisateur et avatar
- **email** : Accès à l'adresse email
- **guilds** : Liste des serveurs Discord (optionnel)

## 7. Sécurité

✓ Les tokens Discord ne sont jamais stockés côté client
✓ Seul le token Supabase est conservé (dans localStorage par défaut)
✓ Les sessions expirent automatiquement
✓ Possibilité de révoquer les sessions depuis Supabase

## 8. Tester localement

1. Lancez un serveur local (Live Server VS Code, ou Python)
2. Accédez à http://localhost:5500/login.html
3. Cliquez sur "Continuer avec Discord"
4. Vérifiez que la redirection fonctionne

## Liens utiles

- Discord Developer Portal : https://discord.com/developers/applications
- Supabase Auth Docs : https://supabase.com/docs/guides/auth
- Discord OAuth2 Docs : https://discord.com/developers/docs/topics/oauth2
