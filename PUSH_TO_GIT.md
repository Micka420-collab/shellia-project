# 📤 PUSH SUR GITHUB - Instructions

## 🚀 Prêt à pousser ?

Tout est configuré et prêt ! Suis ces étapes :

---

## ÉTAPE 1: Ouvrir un terminal

Sur Windows :
- Appuie sur `Windows + R`
- Tape `cmd` et Entrée
- OU utilise PowerShell

---

## ÉTAPE 2: Aller dans le dossier du projet

```cmd
cd "C:\Users\Mick\Downloads\Kimi_Agent_Discord Channel Setup & API (1)\shellia-project"
```

---

## ÉTAPE 3: Vérifier les fichiers

```cmd
dir
```

Tu dois voir :
- bot/
- admin-panel/
- deployment/
- tests/
- docker-compose.yml
- Dockerfile
- SHELLIA_GUIDE.md
- README.md
- etc.

---

## ÉTAPE 4: Initialiser Git (première fois seulement)

```cmd
git init
git remote add origin https://github.com/Micka420-collab/shellia-project.git
```

Si Git n'est pas installé :
- Télécharge : https://git-scm.com/download/windows
- Installe avec les options par défaut
- Redémarre le terminal

---

## ÉTAPE 5: Configurer Git (une seule fois)

```cmd
git config user.name "Ton Nom"
git config user.email "ton@email.com"
```

---

## ÉTAPE 6: Ajouter tous les fichiers

```cmd
git add .
```

---

## ÉTAPE 7: Créer le commit

```cmd
git commit -m "🚀 v2.1-PLUS: Système complet avec Marketing & Pré-achat

Fonctionnalités principales:
- 🤖 Bot Discord IA (Gemini) avec génération d'images
- 💰 Paiements Stripe intégrés
- 🦀 OpenClaw Business Automation (MRR, ARPU, promotions auto)
- 🎁 Giveaways automatiques aux paliers avec Grade Winner
- 🛍️ Système de Pré-achat (Early Bird -30%, Founder -20%, Supporter -10%)
- 🎭 7 Rôles Marketing (Ambassadeur, Influenceur, Créateur, Helper, Event Host, Beta Tester, Partenaire)
- 🎊 Ouverture Officielle automatisée avec l'IA (T-7j à T+7j)
- 📊 Récap Hebdomadaire IA (stats complètes tous les lundis)
- 🔐 Sécurité enterprise-grade (9.3/10)
- 📊 Dashboard admin complet

Technical:
- Docker ready
- 15+ schémas SQL
- 35+ tests
- Documentation 100+ pages

Ready for production! 🎉"
```

---

## ÉTAPE 8: Pousser sur GitHub

```cmd
git push -u origin main
```

Si ça demande des identifiants :
- Nom d'utilisateur : ton username GitHub
- Mot de passe : ton Personal Access Token (PAS ton mot de passe GitHub !)

Pour créer un token :
1. Va sur https://github.com/settings/tokens
2. "Generate new token (classic)"
3. Coche "repo"
4. Génère et copie le token
5. Utilise ce token comme mot de passe

---

## ✅ VÉRIFICATION

Va sur :
```
https://github.com/Micka420-collab/shellia-project
```

Tu dois voir tous tes fichiers !

---

## 🆘 SI ÇA MARCHE PAS

### Erreur: "not a git repository"
```cmd
git init
git remote add origin https://github.com/Micka420-collab/shellia-project.git
```

### Erreur: "Permission denied"
- Utilise un Personal Access Token (voir étape 8)
- Ou configure SSH : https://docs.github.com/fr/authentication/connecting-to-github-with-ssh

### Erreur: "failed to push some refs"
```cmd
git pull origin main --allow-unrelated-histories
git push origin main
```

### Erreur: "repository not found"
- Vérifie que le repo existe sur GitHub
- Vérifie l'URL : https://github.com/Micka420-collab/shellia-project.git

---

## 🎉 APRÈS LE PUSH

1. **Vérifie sur GitHub** que tous les fichiers sont là
2. **Copie le message** dans 🚀_FINAL_DEPLOY_GUIDE.md
3. **Envoie à Shellia** sur Discord
4. **Attends le déploiement** 🚀

---

## 💬 MESSAGE POUR SHELLIA

```
@Shellia Hello ! 🎉

J'ai besoin que tu déploies le projet complet sur une VM.

📦 REPOSITORY: https://github.com/Micka420-collab/shellia-project.git

🎯 MISSION: Créer VM + Déployer le bot + Configurer tout

📋 INSTRUCTIONS:
1. Lire le fichier SHELLIA_GUIDE.md (guide complet)
2. Suivre chaque étape du guide
3. Configurer les variables d'environnement (.env)
4. Exécuter les 10 scripts SQL dans deployment/
5. Lancer: docker-compose up -d

🖥️ SPECS VM:
- OS: Ubuntu 22.04 LTS
- CPU: 2-4 vCPU  
- RAM: 4-8 GB
- Disk: 30 GB SSD

🔧 FONCTIONNALITÉS À CONFIGURER:
- Channel #🛍️│pré-achat (pré-achats)
- Channels marketing (#🏆│ambassadeurs, #📢│influenceurs, etc.)
- Date ouverture officielle: 15 Février 2026 18h00
- Channel #📊│admin-recap (récap hebdo)

📖 Le guide SHELLIA_GUIDE.md contient TOUTES les instructions.

Merci beaucoup ! 🦀🚀
```

---

**Une fois poussé, tout sera prêt pour que Shellia déploie !** 🎊
