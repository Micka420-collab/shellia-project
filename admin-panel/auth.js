/**
 * AUTHENTIFICATION DISCORD - Shellia AI Dashboard
 * OAuth2 flow avec Supabase
 */

// Configuration OAuth2 Discord
const DISCORD_CONFIG = {
    clientId: null, // Sera chargé depuis Supabase
    redirectUri: window.location.origin + window.location.pathname,
    scope: 'identify email',
    responseType: 'token'
};

// État de l'authentification
let authState = {
    isAuthenticated: false,
    admin: null,
    sessionToken: null,
    expiresAt: null
};

// Initialisation
async function initAuth() {
    // Charger la config Discord depuis Supabase
    await loadDiscordConfig();
    
    // Vérifier si on revient d'une authentification Discord
    const hash = window.location.hash;
    if (hash.includes('access_token')) {
        // Traiter le callback OAuth
        await handleDiscordCallback(hash);
        // Nettoyer l'URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else {
        // Vérifier session existante
        await checkExistingSession();
    }
    
    updateUI();
}

// Charger la configuration Discord
async function loadDiscordConfig() {
    try {
        // Dans une vraie implémentation, cette config viendrait de Supabase
        // Pour l'instant, on utilise une config par défaut ou localStorage
        const config = localStorage.getItem('discord_oauth_config');
        if (config) {
            const parsed = JSON.parse(config);
            DISCORD_CONFIG.clientId = parsed.clientId;
        }
    } catch (error) {
        console.error('Erreur chargement config OAuth:', error);
    }
}

// Sauvegarder la configuration Discord (à appeler une fois par l'admin)
function saveDiscordConfig(clientId) {
    DISCORD_CONFIG.clientId = clientId;
    localStorage.setItem('discord_oauth_config', JSON.stringify({
        clientId: clientId
    }));
}

// Démarrer l'authentification Discord
function startDiscordAuth() {
    if (!DISCORD_CONFIG.clientId) {
        showToast('❌ Configuration Discord OAuth manquante', 'error');
        showDiscordConfigModal();
        return;
    }
    
    // Générer un state pour la sécurité
    const state = generateRandomState();
    sessionStorage.setItem('oauth_state', state);
    
    // Construire l'URL Discord OAuth
    const params = new URLSearchParams({
        client_id: DISCORD_CONFIG.clientId,
        redirect_uri: DISCORD_CONFIG.redirectUri,
        response_type: 'token',
        scope: DISCORD_CONFIG.scope,
        state: state
    });
    
    const authUrl = `https://discord.com/api/oauth2/authorize?${params.toString()}`;
    
    // Rediriger vers Discord
    window.location.href = authUrl;
}

// Générer un state aléatoire
function generateRandomState() {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Traiter le callback OAuth Discord
async function handleDiscordCallback(hash) {
    const params = new URLSearchParams(hash.substring(1));
    const accessToken = params.get('access_token');
    const state = params.get('state');
    const error = params.get('error');
    
    // Vérifier erreur
    if (error) {
        const errorDescription = params.get('error_description');
        showToast(`❌ Erreur Discord: ${errorDescription || error}`, 'error');
        logAuthAttempt(null, 'failed', errorDescription || error);
        return;
    }
    
    // Vérifier state (protection CSRF)
    const savedState = sessionStorage.getItem('oauth_state');
    if (state !== savedState) {
        showToast('❌ Erreur de sécurité: state invalide', 'error');
        logAuthAttempt(null, 'failed', 'Invalid state');
        return;
    }
    
    sessionStorage.removeItem('oauth_state');
    
    // Récupérer les infos utilisateur Discord
    try {
        const userInfo = await fetchDiscordUserInfo(accessToken);
        
        // Vérifier si l'utilisateur est admin
        const adminInfo = await verifyAdminStatus(userInfo);
        
        if (!adminInfo.isAdmin) {
            showToast('❌ Accès refusé: vous n\'êtes pas administrateur', 'error');
            logAuthAttempt(userInfo.id, 'failed', 'Not an admin');
            return;
        }
        
        // Créer une session
        const session = await createAdminSession(adminInfo);
        
        // Sauvegarder l'état
        authState = {
            isAuthenticated: true,
            admin: adminInfo,
            sessionToken: session.token,
            expiresAt: session.expiresAt
        };
        
        // Stocker dans sessionStorage (plus sécurisé que localStorage)
        sessionStorage.setItem('admin_session', JSON.stringify({
            token: session.token,
            expiresAt: session.expiresAt
        }));
        
        logAuthAttempt(userInfo.id, 'login');
        showToast(`✅ Bienvenue ${adminInfo.username} !`, 'success');
        
    } catch (error) {
        console.error('Erreur authentification:', error);
        showToast('❌ Erreur lors de l\'authentification', 'error');
        logAuthAttempt(null, 'failed', error.message);
    }
}

// Récupérer les infos utilisateur Discord
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

// Vérifier le statut admin dans Supabase
async function verifyAdminStatus(discordUser) {
    if (!supabaseClient) {
        throw new Error('Supabase client not initialized');
    }
    
    // Appeler la fonction RPC pour upsert l'admin
    const { data, error } = await supabaseClient.rpc('upsert_admin', {
        p_discord_id: discordUser.id,
        p_discord_username: discordUser.username,
        p_discord_avatar: discordUser.avatar,
        p_discord_email: discordUser.email
    });
    
    if (error) {
        throw new Error('Failed to verify admin status: ' + error.message);
    }
    
    // Vérifier si l'admin est actif
    const { data: adminData, error: adminError } = await supabaseClient
        .from('admin_users')
        .select('*')
        .eq('discord_id', discordUser.id)
        .single();
    
    if (adminError || !adminData) {
        return { isAdmin: false };
    }
    
    if (!adminData.is_active) {
        return { isAdmin: false, reason: 'Account disabled' };
    }
    
    return {
        isAdmin: true,
        id: adminData.id,
        discordId: adminData.discord_id,
        username: adminData.discord_username,
        avatar: adminData.discord_avatar,
        isSuperAdmin: adminData.is_super_admin
    };
}

// Créer une session admin
async function createAdminSession(adminInfo) {
    // Générer un token de session
    const sessionToken = generateSessionToken();
    
    // Calculer l'expiration (24h)
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + 24);
    
    // Sauvegarder dans Supabase
    const { data, error } = await supabaseClient.rpc('create_session', {
        p_admin_id: adminInfo.id,
        p_session_token: sessionToken,
        p_ip_address: null, // Le serveur peut détecter l'IP
        p_user_agent: navigator.userAgent,
        p_duration_hours: 24
    });
    
    if (error) {
        throw new Error('Failed to create session: ' + error.message);
    }
    
    return {
        token: sessionToken,
        expiresAt: expiresAt.toISOString()
    };
}

// Générer un token de session sécurisé
function generateSessionToken() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Vérifier session existante
async function checkExistingSession() {
    const saved = sessionStorage.getItem('admin_session');
    if (!saved) return;
    
    try {
        const session = JSON.parse(saved);
        
        // Vérifier expiration
        if (new Date(session.expiresAt) < new Date()) {
            sessionStorage.removeItem('admin_session');
            return;
        }
        
        // Vérifier validité avec Supabase
        const { data, error } = await supabaseClient.rpc('verify_session', {
            p_session_token: session.token
        });
        
        if (error || !data || !data.is_valid) {
            sessionStorage.removeItem('admin_session');
            return;
        }
        
        // Restaurer l'état
        authState = {
            isAuthenticated: true,
            admin: {
                id: data.admin_id,
                discordId: data.discord_id,
                username: data.discord_username,
                isSuperAdmin: data.is_super_admin
            },
            sessionToken: session.token,
            expiresAt: session.expiresAt
        };
        
    } catch (error) {
        console.error('Erreur vérification session:', error);
        sessionStorage.removeItem('admin_session');
    }
}

// Déconnexion
async function logout() {
    if (authState.sessionToken) {
        // Révoquer la session côté serveur
        try {
            await supabaseClient.rpc('revoke_session', {
                p_session_token: authState.sessionToken
            });
        } catch (error) {
            console.error('Erreur révocation session:', error);
        }
        
        // Logger
        if (authState.admin) {
            logAuthAttempt(authState.admin.discordId, 'logout');
        }
    }
    
    // Nettoyer le state
    authState = {
        isAuthenticated: false,
        admin: null,
        sessionToken: null,
        expiresAt: null
    };
    
    sessionStorage.removeItem('admin_session');
    
    updateUI();
    showToast('👋 Déconnecté avec succès', 'info');
}

// Logger une tentative d'authentification
async function logAuthAttempt(discordId, action, errorMessage = null) {
    try {
        await supabaseClient.rpc('log_admin_login', {
            p_discord_id: discordId,
            p_action: action,
            p_ip_address: null,
            p_user_agent: navigator.userAgent,
            p_success: !errorMessage,
            p_error_message: errorMessage
        });
    } catch (error) {
        console.error('Erreur logging:', error);
    }
}

// Mettre à jour l'UI selon l'état d'authentification
function updateUI() {
    const loginModal = document.getElementById('login-modal');
    const mainContent = document.querySelector('.main');
    const userInfo = document.querySelector('.user-info');
    
    if (authState.isAuthenticated) {
        // Masquer modal login
        if (loginModal) loginModal.classList.remove('active');
        
        // Afficher contenu principal
        if (mainContent) mainContent.style.display = 'block';
        
        // Afficher info utilisateur
        if (userInfo && authState.admin) {
            userInfo.innerHTML = `
                <img src="https://cdn.discordapp.com/avatars/${authState.admin.discordId}/${authState.admin.avatar}.png" 
                     alt="Avatar" 
                     onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                <span>${authState.admin.username}</span>
                ${authState.admin.isSuperAdmin ? '<span class="super-admin-badge">👑</span>' : ''}
            `;
            userInfo.style.display = 'flex';
        }
        
        // Activer la navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.style.pointerEvents = 'auto';
            item.style.opacity = '1';
        });
        
    } else {
        // Afficher modal login
        if (loginModal) {
            loginModal.classList.add('active');
            // Changer le contenu pour Discord OAuth
            loginModal.innerHTML = `
                <div class="modal-content login-modal">
                    <div class="login-header">
                        <h2>🔐 Connexion Administrateur</h2>
                        <p>Shellia AI Dashboard</p>
                    </div>
                    
                    <div class="login-options">
                        <button onclick="startDiscordAuth()" class="btn-discord">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                            </svg>
                            Se connecter avec Discord
                        </button>
                        
                        <div class="login-divider">
                            <span>ou</span>
                        </div>
                        
                        <button onclick="showSupabaseLogin()" class="btn-secondary">
                            Connexion Supabase (legacy)
                        </button>
                    </div>
                    
                    <div class="login-footer">
                        <p>🔒 Accès réservé aux administrateurs</p>
                        <p class="login-hint">Contactez un super admin pour obtenir l'accès</p>
                    </div>
                </div>
            `;
        }
        
        // Masquer contenu principal
        if (mainContent) mainContent.style.display = 'none';
        
        // Désactiver la navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.style.pointerEvents = 'none';
            item.style.opacity = '0.5';
        });
    }
}

// Afficher le modal de config Discord
function showDiscordConfigModal() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>⚙️ Configuration Discord OAuth</h3>
            <p>Entrez votre Client ID Discord pour activer l'authentification.</p>
            
            <div class="form-group">
                <label>Discord Client ID</label>
                <input type="text" id="discord-client-id" placeholder="1234567890123456789">
                <span class="help-text">
                    <a href="https://discord.com/developers/applications" target="_blank">
                        Créer une application Discord →
                    </a>
                </span>
            </div>
            
            <div class="form-actions">
                <button onclick="saveDiscordClientId()" class="btn-primary">Sauvegarder</button>
                <button onclick="this.closest('.modal').remove()" class="btn-secondary">Annuler</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Sauvegarder le Client ID
function saveDiscordClientId() {
    const clientId = document.getElementById('discord-client-id').value.trim();
    if (!clientId) {
        showToast('Veuillez entrer un Client ID', 'error');
        return;
    }
    
    saveDiscordConfig(clientId);
    document.querySelector('.modal.active').remove();
    showToast('✅ Configuration sauvegardée !', 'success');
}

// Afficher login Supabase (fallback)
function showSupabaseLogin() {
    const loginModal = document.getElementById('login-modal');
    loginModal.innerHTML = `
        <div class="modal-content">
            <h2>🔐 Connexion Supabase</h2>
            <p>Mode legacy - déconseillé</p>
            <input type="url" id="supabase-url" placeholder="URL Supabase">
            <input type="password" id="supabase-key" placeholder="Clé service (service_role)">
            <button onclick="connectSupabase()">Se connecter</button>
            <button onclick="initAuth()" class="btn-secondary" style="margin-top: 10px;">← Retour</button>
        </div>
    `;
}

// Vérifier périodiquement la validité de la session
setInterval(async () => {
    if (authState.isAuthenticated && authState.sessionToken) {
        // Vérifier si la session expire dans moins de 5 minutes
        const expiresAt = new Date(authState.expiresAt);
        const fiveMinutes = 5 * 60 * 1000;
        
        if (expiresAt - new Date() < fiveMinutes) {
            // Rafraîchir la session
            try {
                const { data, error } = await supabaseClient.rpc('verify_session', {
                    p_session_token: authState.sessionToken
                });
                
                if (error || !data.is_valid) {
                    // Session invalide, déconnecter
                    logout();
                    showToast('Session expirée, veuillez vous reconnecter', 'warning');
                }
            } catch (error) {
                console.error('Erreur vérification session:', error);
            }
        }
    }
}, 60000); // Vérifier toutes les minutes

// Initialiser l'authentification au chargement
document.addEventListener('DOMContentLoaded', initAuth);
