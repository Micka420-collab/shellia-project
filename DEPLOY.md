# 🚀 Déploiement Rapide - Shellia AI

## Déploiement en 3 commandes

```bash
# 1. Cloner
git clone https://github.com/Micka420-collab/shellia-project.git
cd shellia-project

# 2. Configurer
cp .env.example .env
# Éditer .env avec vos clés API

# 3. Lancer
docker-compose up -d
```

**C'est tout !** Le bot est en ligne. 🎉

---

## Prérequis

- Docker & Docker Compose installés
- Fichier `.env` configuré avec vos clés API

---

## Configuration requise (.env)

### Minimum requis:
```env
DISCORD_TOKEN=votre_token
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=votre_cle
GEMINI_API_KEY=votre_cle
STRIPE_SECRET_KEY=sk_test_...
ENCRYPTION_KEY=votre_cle_fernet
SECRET_KEY=votre_secret
```

---

## Vérification

```bash
# Voir les logs
docker-compose logs -f bot

# Commandes Discord disponibles
/help
/openclaw
/giveaway
```

---

## Guide complet

Pour un déploiement détaillé avec VM, voir [SHELLIA_GUIDE.md](SHELLIA_GUIDE.md)
