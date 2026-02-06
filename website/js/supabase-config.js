// ========================================
// SUPABASE CONFIGURATION - Discord OAuth
// ========================================

// Configuration Supabase - Remplacez par vos vraies valeurs
const SUPABASE_URL = 'https://votre-projet.supabase.co';
const SUPABASE_ANON_KEY = 'votre-clé-anon-publique';

// Initialisation du client Supabase
let supabaseClient = null;

function initSupabase() {
    if (typeof supabase === 'undefined') {
        console.error('Supabase library not loaded');
        return null;
    }
    
    supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true
        }
    });
    
    return supabaseClient;
}

function getSupabase() {
    if (!supabaseClient) {
        return initSupabase();
    }
    return supabaseClient;
}

// Connexion avec Discord
async function signInWithDiscord() {
    const supabase = getSupabase();
    if (!supabase) return;
    
    const REDIRECT_URL = window.location.origin + '/auth/callback.html';
    
    try {
        const { data, error } = await supabase.auth.signInWithOAuth({
            provider: 'discord',
            options: {
                redirectTo: REDIRECT_URL,
                scopes: 'identify email guilds'
            }
        });
        
        if (error) {
            showNotification('Erreur de connexion: ' + error.message, 'error');
            return;
        }
        
        if (data?.url) {
            window.location.href = data.url;
        }
        
    } catch (err) {
        showNotification('Une erreur est survenue', 'error');
    }
}

// Déconnexion
async function signOut() {
    const supabase = getSupabase();
    if (!supabase) return;
    
    await supabase.auth.signOut();
    window.location.href = '/';
}

// Récupérer l'utilisateur
async function getCurrentUser() {
    const supabase = getSupabase();
    if (!supabase) return null;
    
    try {
        const { data: { user }, error } = await supabase.auth.getUser();
        
        if (error || !user) return null;
        
        return {
            ...user,
            discord: {
                id: user.user_metadata?.provider_id,
                username: user.user_metadata?.name || user.user_metadata?.user_name,
                avatar: user.user_metadata?.avatar_url,
                email: user.email
            }
        };
        
    } catch (err) {
        return null;
    }
}

// Vérifier authentification
async function isAuthenticated() {
    const user = await getCurrentUser();
    return !!user;
}

// Protéger une route
async function requireAuth() {
    const isAuth = await isAuthenticated();
    
    if (!isAuth) {
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = '/login.html';
        return false;
    }
    
    return true;
}

// Notification
function showNotification(message, type = 'info') {
    const notif = document.createElement('div');
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        color: white;
        font-weight: 500;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        ${type === 'error' ? 'background: #ef4444;' : 'background: #10b981;'}
    `;
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => notif.remove(), 3000);
}

// Mettre à jour UI
async function updateUserUI() {
    const user = await getCurrentUser();
    
    const usernameElements = document.querySelectorAll('[data-user-name]');
    const avatarElements = document.querySelectorAll('[data-user-avatar]');
    
    if (user) {
        const displayName = user.discord?.username || 'Utilisateur';
        const avatarUrl = user.discord?.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png';
        
        usernameElements.forEach(el => el.textContent = displayName);
        avatarElements.forEach(el => {
            el.src = avatarUrl;
            el.alt = displayName;
        });
        
        document.querySelectorAll('.show-if-logged-out').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.show-if-logged-in').forEach(el => el.style.display = 'flex');
    } else {
        document.querySelectorAll('.show-if-logged-out').forEach(el => el.style.display = 'flex');
        document.querySelectorAll('.show-if-logged-in').forEach(el => el.style.display = 'none');
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    initSupabase();
    await updateUserUI();
});

window.SupabaseAuth = {
    signInWithDiscord,
    signOut,
    getCurrentUser,
    isAuthenticated,
    requireAuth
};
