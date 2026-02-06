# 🤝 Guide de Contribution - Shellia AI

Merci de votre intérêt pour contribuer à Shellia AI ! Ce document vous guidera dans le processus de contribution.

---

## Code de conduite

### Nos valeurs

- **Respect** : Traitez tous les contributeurs avec respect
- **Patience** : Nous avons tous différents niveaux d'expérience
- **Collaboration** : Les meilleures idées émergent du dialogue
- **Excellence** : Visons la qualité, pas la perfection

### Comportements inacceptables

- Harcèlement sous quelque forme que ce soit
- Discrimination ou langage offensant
- Trolling ou commentaires désobligeants
- Doxing ou menaces

---

## Comment contribuer

### Signaler un bug

1. **Vérifiez** si le bug n'a pas déjà été signalé
2. **Ouvrez une issue** avec le label `bug`
3. **Décrivez** :
   - Ce que vous attendiez
   - Ce qui s'est passé
   - Étapes pour reproduire
   - Environnement (OS, navigateur, etc.)

### Proposer une fonctionnalité

1. **Vérifiez** si la fonctionnalité n'a pas été proposée
2. **Ouvrez une issue** avec le label `enhancement`
3. **Expliquez** :
   - Le problème que cela résout
   - La solution proposée
   - Alternatives envisagées

### Soumettre du code

#### Fork et clone

```bash
# Fork le repo sur GitHub
# Puis clonez votre fork
git clone https://github.com/votre-username/shellia-ai.git
cd shellia-ai
```

#### Branche

```bash
# Créez une branche pour votre contribution
git checkout -b feature/nom-de-la-feature
# ou
git checkout -b fix/description-du-bug
```

#### Commits

Utilisez les conventions de commit :

```
feat: ajout d'une nouvelle fonctionnalité
fix: correction d'un bug
docs: modification de la documentation
style: formatage (pas de changement de code)
refactor: refactorisation du code
test: ajout de tests
chore: maintenance (dépendances, etc.)
```

Exemple :
```bash
git commit -m "feat: ajout du système de notifications email"
```

#### Pull Request

1. **Poussez** votre branche
2. **Ouvrez une PR** vers `main`
3. **Décrivez** vos changements
4. **Attendez** la review (48-72h)

---

## Standards de code

### Python

```python
# Format : Black
# Longueur max : 100 caractères
# Imports triés : isort

# Exemple
def calculate_total(price: float, quantity: int) -> float:
    """
    Calcule le total avec TVA.
    
    Args:
        price: Prix unitaire HT
        quantity: Quantité
        
    Returns:
        Total TTC
    """
    return price * quantity * 1.20
```

### JavaScript

```javascript
// ESLint + Prettier
// ES6+
// Async/await préféré

// Exemple
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) throw new Error('User not found');
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch user:', error);
        throw error;
    }
}
```

### HTML/CSS

```html
<!-- BEM naming convention -->
<div class="card card--featured">
    <h2 class="card__title">Titre</h2>
    <p class="card__description">Description</p>
</div>
```

---

## Tests

### Exécuter les tests

```bash
# Python
pytest

# JavaScript
npm test
```

### Couverture minimale

- Backend : 80%
- Frontend : 70%

---

## Documentation

### Mettre à jour la doc

Si vous modifiez :
- Une API → Mettez à jour `API_DOCUMENTATION.md`
- Une commande → Mettez à jour `USER_GUIDE.md`
- La sécurité → Mettez à jour `SECURITY_GUIDE.md`

### Docstrings

Toutes les fonctions publiques doivent avoir une docstring.

---

## Sécurité

### Signaler une vulnérabilité

**Ne créez pas une issue publique !**

1. Envoyez un email à security@shellia.ai
2. Chiffrez avec notre clé PGP si possible
3. Attendez notre réponse (48h max)
4. Nous coordonnerons la divulgation

### Programme de bug bounty

Nous récompensons les chercheurs en sécurité :

| Sévérité | Récompense |
|----------|------------|
| Critique | 1000-5000 EUR |
| Élevée | 500-1000 EUR |
| Moyenne | 100-500 EUR |
| Faible | 50-100 EUR |

---

## Questions fréquentes

### Puis-je contribuer si je débute ?

Oui ! Recherchez les issues avec le label `good-first-issue`.

### Combien de temps prend une review ?

- Petites PR : 24-48h
- Grandes PR : 3-5 jours

### Puis-je contribuer sans coder ?

Oui ! Vous pouvez :
- Améliorer la documentation
- Traduire les textes
- Reporter des bugs
- Aider la communauté Discord

---

## Contact

**Discord dev :** https://discord.gg/shellia-dev  
**Email :** contribute@shellia.ai  
**Twitter :** @ShelliaAI

---

**Merci de contribuer à Shellia AI ! 🚀**

**© 2026 Shellia AI - Open Source**
