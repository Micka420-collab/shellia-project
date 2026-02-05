/**
 * AUTHENTIFICATION SÉCURISÉE - Page de Login Shellia AI
 * OAuth2 Discord avec protection renforcée
 */

// Configuration sécurisée
const AUTH_CONFIG = {
    // Ces valeurs devraient être chargées depuis une config serveur
    discordClientId: null,
    redirectUri: window.location.origin + '/callback.html',
    scope: 'identify email',
    stateLength: 32,
    pkceEnabled: true
};

// Stockage sécurisé en mémoire (pas dans localStorage)
let secureState = {
    oauthState: null,
    codeVerifier: null,
    codeChallenge: null,
    sessionData: null
};

// Générateur de nombres aléatoires sécurisé
function generateSecureString(length) {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Générer un code verifier PKCE
function generateCodeVerifier() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return base64URLEncode(array);
}

// Encoder en base64URL
function base64URLEncode(str) {
    return btoa(String.fromCharCode.apply(null, str))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}

// Hacher avec SHA-256
async function sha256(plain) {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return base64URLEncode(new Uint8Array(hash));
}

// Initialisation
async function initLogin() {
    // Charger la config depuis une source sécurisée
    await loadAuthConfig();
    
    // Vérifier si on revient d'une authentification
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    
    if (hashParams.has('access_token') || urlParams.has('code')) {
        await handleAuthCallback();
    } else {
        // Vérifier si déjà authentifié
        await checkExistingAuth();
    }
}

// Charger la configuration d'authentification
async function loadAuthConfig() {
    try {
        // En production, cette config devrait venir du serveur
        // Pour l'instant, on la stocke de manière sécurisée
        const savedConfig = sessionStorage.getItem('auth_config');
        if (savedConfig) {
            const config = JSON.parse(savedConfig);
            AUTH_CONFIG.discordClientId = config.discordClientId;
        }
    } catch (error) {
        console.error('Erreur chargement config:', error);
    }
}

// Sauvegarder la config (à appeler une fois)
function saveAuthConfig(clientId) {
    AUTH_CONFIG.discordClientId = clientId;
    sessionStorage.setItem('auth_config', JSON.stringify({
        discordClientId: clientId,
        savedAt: Date.now()
    }));
}

// Démarrer l'authentification Discord
async function startDiscordAuth() {
    if (!AUTH_CONFIG.discordClientId) {
        showError('Configuration Discord manquante');
        return;
    }
    
    // Générer le state et PKCE
    secureState.oauthState = generateSecureString(AUTH_CONFIG.stateLength);
    
    if (AUTH_CONFIG.pkceEnabled) {
        secureState.codeVerifier = generateCodeVerifier();
        secureState.codeChallenge = await sha256(secureState.codeVerifier);
    }
    
    // Stocker temporairement (session uniquement)
    sessionStorage.setItem('oauth_state', secureState.oauthState);
    if (AUTH_CONFIG.pkceEnabled) {
        sessionStorage.setItem('pkce_verifier', secureState.codeVerifier);
    }
    
    // Construire l'URL Discord OAuth
    const params = new URLSearchParams({
        client_id: AUTH_CONFIG.discordClientId,
        redirect_uri: window.location.origin + window.location.pathname,
        response_type: 'token',
        scope: AUTH_CONFIG.scope,
        state: secureState.oauthState
    });
    
    if (AUTH_CONFIG.pkceEnabled && secureState.codeChallenge) {
        params.append('code_challenge', secureState.codeChallenge);
        params.append('code_challenge_method', 'S256');
    }
    
    // Rediriger vers Discord
    window.location.href = `https://discord.com/api/oauth2/authorize?${params.toString()}`;
}

// Gérer le retour d'authentification
async function handleAuthCallback() {
    showLoading('Vérification de l\'authentification...');
    
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    
    const accessToken = params.get('access_token');
    const state = params.get('state');
    const error = params.get('error');
    
    // Vérifier les erreurs
    if (error) {
        showError(`Erreur Discord: ${params.get('error_description') || error}`);
        return;
    }
    
    // Vérifier le state (protection CSRF)
    const savedState = sessionStorage.getItem('oauth_state');
    if (!state || state !== savedState) {
        showError('Erreur de sécurité: state invalide');
        logSecurityEvent('invalid_state', 'CSRF attempt detected');
        return;
    }
    
    // Nettoyer
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('pkce_verifier');
    
    try {
        // Récupérer les infos utilisateur
        const userInfo = await fetchDiscordUserInfo(accessToken);
        
        // Vérifier si admin
        const adminInfo = await verifyAdminStatus(userInfo);
        
        if (!adminInfo.isAdmin) {
            showError('Accès refusé: vous n\'êtes pas administrateur');
            logSecurityEvent('unauthorized_access', `User ${userInfo.id} attempted login`);
            return;
        }
        
        // Créer une session sécurisée
        const session = await createSecureSession(adminInfo, accessToken);
        
        // Stocker de manière sécurisée
        secureState.sessionData = {
            admin: adminInfo,
            token: session.token,
            expiresAt: session.expiresAt
        };
        
        // Stocker dans sessionStorage avec encryption simple
        const encryptedSession = await encryptSession(secureState.sessionData);
        sessionStorage.setItem('admin_session', encryptedSession);
        
        // Rediriger vers le dashboard
        window.location.href = 'index.html';
        
    } catch (error) {
        console.error('Erreur authentification:', error);
        showError('Erreur lors de l\'authentification');
    }
}

// Récupérer les infos Discord
async function fetchDiscordUserInfo(accessToken) {
    const response = await fetch('https://discord.com/api/v10/users/@me', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    if (!response.ok) {
        throw new Error('Failed to fetch user info');
    }
    
    return await response.json();
}

// Vérifier le statut admin (cette fonction serait connectée à Supabase)
async function verifyAdminStatus(discordUser) {
    // Simulation - en production, appeler Supabase
    // const { data, error } = await supabaseClient.rpc('verify_admin', {...});
    
    // Pour l'instant, simulation
    return {
        isAdmin: true, // À remplacer par vraie vérification
        id: 'admin-id',
        discordId: discordUser.id,
        username: discordUser.username,
        avatar: discordUser.avatar,
        isSuperAdmin: false
    };
}

// Créer une session sécurisée
async function createSecureSession(adminInfo, accessToken) {
    const sessionToken = generateSecureString(32);
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24h
    
    // En production, envoyer au serveur pour stockage
    // await supabaseClient.rpc('create_session', {...});
    
    return {
        token: sessionToken,
        expiresAt: expiresAt.toISOString()
    };
}

// Chiffrement simple de session (à améliorer en production)
async function encryptSession(data) {
    // Utiliser une clé dérivée du navigateur
    const key = await deriveKey();
    
    const encoder = new TextEncoder();
    const encoded = encoder.encode(JSON.stringify(data));
    
    // Chiffrement AES-GCM
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        key,
        encoded
    );
    
    // Retourner IV + données chiffrées en base64
    const result = new Uint8Array(iv.length + encrypted.byteLength);
    result.set(iv);
    result.set(new Uint8Array(encrypted), iv.length);
    
    return btoa(String.fromCharCode.apply(null, result));
}

// Dériver une clé du navigateur
async function deriveKey() {
    // Utiliser des caractéristiques du navigateur comme sel
    const browserData = navigator.userAgent + navigator.language + screen.width + screen.height;
    
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        encoder.encode(browserData),
        'PBKDF2',
        false,
        ['deriveKey']
    );
    
    return await crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: encoder.encode('shellia-salt'),
            iterations: 100000,
            hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
    );
}

// Vérifier si déjà authentifié
async function checkExistingAuth() {
    const savedSession = sessionStorage.getItem('admin_session');
    if (!savedSession) return;
    
    try {
        // Décrypter et vérifier
        const session = await decryptSession(savedSession);
        
        if (new Date(session.expiresAt) > new Date()) {
            // Session valide, rediriger
            window.location.href = 'index.html';
        } else {
            // Expirée, supprimer
            sessionStorage.removeItem('admin_session');
        }
    } catch (error) {
        console.error('Erreur vérification session:', error);
        sessionStorage.removeItem('admin_session');
    }
}

// Décrypter la session
async function decryptSession(encryptedData) {
    const key = await deriveKey();
    
    const data = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
    const iv = data.slice(0, 12);
    const ciphertext = data.slice(12);
    
    const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
    );
    
    const decoder = new TextDecoder();
    return JSON.parse(decoder.decode(decrypted));
}

// =====================
// UI FUNCTIONS
// =====================

function showLoading(message) {
    document.getElementById('auth-methods').style.display = 'none';
    document.getElementById('emergency-access').style.display = 'none';
    document.getElementById('error-state').style.display = 'none';
    
    const loading = document.getElementById('loading-state');
    loading.style.display = 'block';
    loading.querySelector('p').textContent = message;
}

function showError(message) {
    document.getElementById('auth-methods').style.display = 'none';
    document.getElementById('emergency-access').style.display = 'none';
    document.getElementById('loading-state').style.display = 'none';
    
    const error = document.getElementById('error-state');
    error.style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

function resetAuth() {
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('auth-methods').style.display = 'flex';
    document.getElementById('emergency-access').style.display = 'none';
}

function showEmergencyAccess() {
    document.getElementById('auth-methods').style.display = 'none';
    document.getElementById('emergency-access').style.display = 'block';
}

function hideEmergencyAccess() {
    document.getElementById('emergency-access').style.display = 'none';
    document.getElementById('auth-methods').style.display = 'flex';
}

async function verifyEmergencyAccess() {
    const key = document.getElementById('emergency-key').value;
    const code2fa = document.getElementById('emergency-2fa').value;
    
    if (!key) {
        alert('Veuillez entrer la clé d\'accès');
        return;
    }
    
    showLoading('Vérification des identifiants...');
    
    // En production, vérifier contre Supabase
    // Pour l'instant, simulation
    setTimeout(() => {
        showError('Accès d\'urgence désactivé dans cette version');
    }, 1000);
}

// Logger les événements de sécurité
function logSecurityEvent(type, details) {
    const event = {
        type,
        details,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        ip: 'unknown' // Le serveur loggerait la vraie IP
    };
    
    console.warn('[SECURITY]', event);
    
    // En production, envoyer au serveur
    // fetch('/api/security/log', { method: 'POST', body: JSON.stringify(event) });
}

// =====================
// INITIALIZATION
// =====================

document.addEventListener('DOMContentLoaded', initLogin);

// Empêcher la navigation arrière après déconnexion
window.addEventListener('pageshow', (e) => {
    if (e.persisted) {
        window.location.reload();
    }
});
