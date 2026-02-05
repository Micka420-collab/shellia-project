/**
 * CONFIGURATION AUTHENTIFICATION - Exemple
 * 
 * 1. Renommez ce fichier en auth-config.js
 * 2. Remplacez VOTRE_CLIENT_ID par votre vrai Client ID Discord
 * 3. Déployez avec le dashboard
 */

(function() {
    'use strict';
    
    // Configuration Discord OAuth
    const AUTH_CONFIG = {
        discordClientId: 'VOTRE_CLIENT_ID_DISCORD_ICI', // Remplacez par votre Client ID
        redirectUri: window.location.origin + window.location.pathname
    };
    
    // Stocker dans sessionStorage
    sessionStorage.setItem('auth_config', JSON.stringify(AUTH_CONFIG));
    
    console.log('🔐 Configuration auth chargée');
})();

/**
 * OBTENIR VOTRE CLIENT ID DISCORD:
 * 
 * 1. Allez sur https://discord.com/developers/applications
 * 2. Créez une nouvelle application (ou utilisez une existante)
 * 3. Allez dans "OAuth2" → "General"
 * 4. Copiez l'"APPLICATION ID" (c'est le Client ID)
 * 5. Collez-le ci-dessus
 * 6. Ajoutez votre Redirect URI dans Discord:
 *    - http://localhost:8080/login.html (développement)
 *    - https://votre-domaine.com/login.html (production)
 */

/**
 * CONFIGURATION SUPABASE (Optionnel - pour développement):
 * 
 * Si vous voulez tester sans Discord OAuth temporairement,
 * décommentez et remplissez ces valeurs:
 */

/*
sessionStorage.setItem('supabase_fallback', JSON.stringify({
    url: 'https://votre-projet.supabase.co',
    key: 'eyJ...votre-clé-service-role...'
}));
*/
