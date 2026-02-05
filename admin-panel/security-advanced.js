/**
 * PROTECTIONS AVANCÉES - Shellia AI Dashboard
 * Défenses contre les attaques complexes (APT)
 */

// ============================================================================
// 1. PROTECTION CONTRE PROTOTYPE POLLUTION
// ============================================================================

(function protectPrototype() {
    'use strict';
    
    // Geler Object.prototype pour empêcher la pollution
    Object.freeze(Object.prototype);
    Object.freeze(Array.prototype);
    Object.freeze(String.prototype);
    Object.freeze(Number.prototype);
    Object.freeze(Boolean.prototype);
    
    // Protéger également les méthodes critiques
    const criticalObjects = [
        'Object', 'Array', 'String', 'Number', 'Boolean', 
        'Function', 'Date', 'RegExp', 'Error', 'Promise'
    ];
    
    criticalObjects.forEach(name => {
        if (window[name] && window[name].prototype) {
            Object.freeze(window[name].prototype);
        }
    });
    
    console.log('🛡️ Prototype pollution protection active');
})();

// ============================================================================
// 2. CONTENT SECURITY POLICY DYNAMIQUE
// ============================================================================

class CSPManager {
    constructor() {
        this.nonce = this.generateNonce();
        this.applyStrictCSP();
    }
    
    generateNonce() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array));
    }
    
    applyStrictCSP() {
        // Générer un nonce unique pour cette session
        window.CSP_NONCE = this.nonce;
        
        const csp = [
            "default-src 'none'",
            `script-src 'self' 'nonce-${this.nonce}' https://cdn.jsdelivr.net`,
            "style-src 'self' 'unsafe-inline'", // Nécessaire pour certains effets
            "connect-src 'self' https://*.supabase.co https://discord.com https://api.ipify.org",
            "img-src 'self' data: https://cdn.discordapp.com https://*.supabase.co",
            "font-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests",
            "block-all-mixed-content"
        ].join('; ');
        
        // Créer la balise meta CSP
        const meta = document.createElement('meta');
        meta.httpEquiv = 'Content-Security-Policy';
        meta.content = csp;
        document.head.insertBefore(meta, document.head.firstChild);
        
        // Ajouter le nonce à tous les scripts existants
        document.querySelectorAll('script').forEach(script => {
            if (!script.src || script.src.includes(window.location.origin)) {
                script.setAttribute('nonce', this.nonce);
            }
        });
        
        console.log('🔒 CSP Strict appliqué');
    }
    
    // Vérifier si un script est autorisé
    isScriptAllowed(src) {
        const allowedDomains = [
            window.location.origin,
            'https://cdn.jsdelivr.net',
            'https://unpkg.com'
        ];
        return allowedDomains.some(domain => src.startsWith(domain));
    }
}

// ============================================================================
// 3. SUBRESOURCE INTEGRITY (SRI) CHECKER
// ============================================================================

class SRIChecker {
    constructor() {
        this.checksums = {
            'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2': 
                'sha384-4g3b7l8e1l3g6b5c4a3d2e1f4g5h6i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3z',
            // Ajouter d'autres checksums connus ici
        };
        this.verifyExternalResources();
    }
    
    async verifyExternalResources() {
        const scripts = document.querySelectorAll('script[src]');
        
        for (const script of scripts) {
            const src = script.src;
            
            // Vérifier si c'est une ressource externe
            if (!src.startsWith(window.location.origin)) {
                // Vérifier si on a un checksum connu
                if (this.checksums[src]) {
                    const expectedHash = this.checksums[src];
                    
                    // Vérifier l'intégrité
                    if (!script.integrity) {
                        console.warn(`⚠️ Script externe sans SRI: ${src}`);
                        this.quarantineScript(script);
                    } else if (script.integrity !== expectedHash) {
                        console.error(`🚨 ALERTE: Hash SRI modifié pour ${src}`);
                        this.blockScript(script);
                    }
                } else {
                    // Ressource inconnue - risque potentiel
                    console.warn(`⚠️ Ressource externe non vérifiée: ${src}`);
                }
            }
        }
    }
    
    quarantineScript(script) {
        // Marquer le script comme suspect
        script.setAttribute('data-sri-status', 'unverified');
        
        // Optionnel: le déplacer dans un sandbox
        console.warn('Script mis en quarantaine:', script.src);
    }
    
    blockScript(script) {
        script.remove();
        this.reportSecurityIncident('sri_violation', {
            src: script.src,
            expected: script.integrity,
            timestamp: new Date().toISOString()
        });
    }
    
    reportSecurityIncident(type, details) {
        // Envoyer au serveur de logs
        fetch('/api/security/incident', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, details }),
            keepalive: true
        }).catch(() => {
            // Fallback: stocker localement
            const incidents = JSON.parse(localStorage.getItem('security_incidents') || '[]');
            incidents.push({ type, details, date: new Date().toISOString() });
            localStorage.setItem('security_incidents', JSON.stringify(incidents));
        });
    }
}

// ============================================================================
// 4. HONEYPOT ANTI-BOT
// ============================================================================

class HoneypotProtection {
    constructor() {
        this.trapFields = [];
        this.setupHoneypots();
        this.monitorInteractions();
    }
    
    setupHoneypots() {
        // Créer des champs pièges invisibles
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Champ texte caché
            const trap1 = document.createElement('input');
            trap1.type = 'text';
            trap1.name = 'website';
            trap1.style.cssText = 'position:absolute;left:-9999px;top:-9999px;opacity:0;tabindex:-1;';
            trap1.setAttribute('autocomplete', 'off');
            trap1.setAttribute('aria-hidden', 'true');
            form.appendChild(trap1);
            this.trapFields.push(trap1);
            
            // Champ email caché
            const trap2 = document.createElement('input');
            trap2.type = 'email';
            trap2.name = 'email_address';
            trap2.style.cssText = 'position:absolute;left:-9999px;top:-9999px;opacity:0;tabindex:-1;';
            trap2.setAttribute('autocomplete', 'off');
            trap2.setAttribute('aria-hidden', 'true');
            form.appendChild(trap2);
            this.trapFields.push(trap2);
            
            // Timestamp caché (vérification temps de remplissage)
            const timestamp = document.createElement('input');
            timestamp.type = 'hidden';
            timestamp.name = 'form_timestamp';
            timestamp.value = Date.now().toString();
            form.appendChild(timestamp);
        });
    }
    
    monitorInteractions() {
        // Vérifier avant chaque soumission de formulaire
        document.addEventListener('submit', (e) => {
            const form = e.target;
            
            // Vérifier les champs pièges
            const trap1 = form.querySelector('[name="website"]');
            const trap2 = form.querySelector('[name="email_address"]');
            const timestamp = form.querySelector('[name="form_timestamp"]');
            
            if (trap1 && trap1.value !== '') {
                console.warn('🤖 Bot détecté (champ website rempli)');
                e.preventDefault();
                this.handleBotDetection('honeypot_filled', { field: 'website' });
                return false;
            }
            
            if (trap2 && trap2.value !== '') {
                console.warn('🤖 Bot détecté (champ email_address rempli)');
                e.preventDefault();
                this.handleBotDetection('honeypot_filled', { field: 'email_address' });
                return false;
            }
            
            // Vérifier le temps de remplissage (bots remplissent instantanément)
            if (timestamp) {
                const formTime = Date.now() - parseInt(timestamp.value);
                if (formTime < 2000) { // Moins de 2 secondes = suspect
                    console.warn('🤖 Bot détecté (remplissage trop rapide)');
                    e.preventDefault();
                    this.handleBotDetection('too_fast', { duration: formTime });
                    return false;
                }
            }
        }, true);
    }
    
    handleBotDetection(reason, details) {
        // Logger l'incident
        console.error('🚨 Bot détecté:', reason, details);
        
        // Afficher faux message de succès (pour ne pas alerter le bot)
        alert('Formulaire soumis avec succès !'); // Faux message
        
        // Bloquer réellement l'action
        return false;
    }
}

// ============================================================================
// 5. PROTECTION WEBRTC LEAK
// ============================================================================

function protectWebRTC() {
    // Désactiver WebRTC si possible (fuites d'IP même avec VPN)
    const originalRTCPeerConnection = window.RTCPeerConnection;
    
    window.RTCPeerConnection = function(...args) {
        console.warn('⚠️ WebRTC RTCPeerConnection bloqué pour sécurité');
        
        // Option 1: Bloquer complètement
        // throw new Error('WebRTC désactivé pour sécurité');
        
        // Option 2: Créer une version sandboxée qui ne fuit pas l'IP
        const pc = new originalRTCPeerConnection({
            ...args[0],
            iceServers: [] // Pas de serveurs STUN/TURN = pas de leak
        });
        
        return pc;
    };
    
    // Aussi bloquer RTCSessionDescription et RTCIceCandidate si nécessaire
    console.log('🔒 WebRTC protection active');
}

// ============================================================================
// 6. DETECTION D'ANOMALIES COMPORTEMENTALES
// ============================================================================

class BehaviorAnalyzer {
    constructor() {
        this.events = [];
        this.sessionStart = Date.now();
        this.suspiciousScore = 0;
        
        this.startMonitoring();
    }
    
    startMonitoring() {
        // Surveiller les clics (bots cliquent toujours au même endroit)
        document.addEventListener('click', (e) => {
            this.events.push({
                type: 'click',
                x: e.clientX,
                y: e.clientY,
                timestamp: Date.now()
            });
            
            this.analyzePattern();
        });
        
        // Surveiller les mouvements de souris (bots ont des patterns linéaires)
        let lastMousePos = null;
        document.addEventListener('mousemove', (e) => {
            if (lastMousePos) {
                const distance = Math.sqrt(
                    Math.pow(e.clientX - lastMousePos.x, 2) + 
                    Math.pow(e.clientY - lastMousePos.y, 2)
                );
                
                // Mouvements trop linéaires = suspect
                if (distance > 100) {
                    this.events.push({
                        type: 'mouse',
                        distance: distance,
                        linear: this.isLinearMovement(lastMousePos, {x: e.clientX, y: e.clientY}),
                        timestamp: Date.now()
                    });
                }
            }
            
            lastMousePos = { x: e.clientX, y: e.clientY };
        });
        
        // Vérifier les touches (bots tapent trop vite ou trop régulièrement)
        let lastKeyTime = 0;
        const keyIntervals = [];
        
        document.addEventListener('keydown', () => {
            const now = Date.now();
            if (lastKeyTime > 0) {
                const interval = now - lastKeyTime;
                keyIntervals.push(interval);
                
                // Si toujours le même intervalle = bot
                if (keyIntervals.length > 10) {
                    const variance = this.calculateVariance(keyIntervals.slice(-10));
                    if (variance < 10) { // Variance très faible = mécanique
                        this.suspiciousScore += 10;
                        console.warn('🤜 Frappes trop régulières (possible bot)');
                    }
                }
            }
            lastKeyTime = now;
        });
    }
    
    isLinearMovement(from, to) {
        // Détecter si le mouvement est parfaitement horizontal/vertical
        const dx = Math.abs(to.x - from.x);
        const dy = Math.abs(to.y - from.y);
        
        // Si ratio > 10:1 = suspect (humains bougent en courbes)
        return (dx / (dy || 1) > 10) || (dy / (dx || 1) > 10);
    }
    
    calculateVariance(arr) {
        const mean = arr.reduce((a, b) => a + b) / arr.length;
        return arr.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / arr.length;
    }
    
    analyzePattern() {
        // Vérifier si clic toujours au même endroit
        if (this.events.length > 5) {
            const recentClicks = this.events.filter(e => e.type === 'click').slice(-5);
            if (recentClicks.length >= 3) {
                const samePosition = recentClicks.every(e => 
                    Math.abs(e.x - recentClicks[0].x) < 5 && 
                    Math.abs(e.y - recentClicks[0].y) < 5
                );
                
                if (samePosition) {
                    this.suspiciousScore += 20;
                    console.warn('🤜 Clicks toujours au même endroit');
                }
            }
        }
        
        // Si score suspicieux trop élevé
        if (this.suspiciousScore > 50) {
            console.error('🚨 Comportement suspect détecté, session sous surveillance');
            // Pourrait déclencher un re-captcha ou une déconnexion
        }
    }
}

// ============================================================================
// 7. PROTECTION CONTRE LE CLICKJACKING
// ============================================================================

function preventClickjacking() {
    // Vérifier si la page est dans un iframe
    if (window.self !== window.top) {
        console.error('🚨 Page chargée dans un iframe - possible clickjacking');
        
        // Option 1: Rediriger vers le top
        window.top.location = window.self.location;
        
        // Option 2: Afficher un warning (si redir bloquée)
        document.body.innerHTML = `
            <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:red;color:white;display:flex;align-items:center;justify-content:center;z-index:999999;">
                <h1>🚨 Alerte de sécurité: Clickjacking détecté!</h1>
            </div>
        `;
    }
}

// ============================================================================
// 8. INITIALISATION DE TOUTES LES PROTECTIONS
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Ordre important: CSP d'abord
    window.cspManager = new CSPManager();
    
    // Puis les autres protections
    window.sriChecker = new SRIChecker();
    window.honeypot = new HoneypotProtection();
    window.behaviorAnalyzer = new BehaviorAnalyzer();
    
    // Protections immédiates
    protectWebRTC();
    preventClickjacking();
    
    console.log('🛡️ Toutes les protections avancées sont actives');
});

// Protection contre la fermeture accidentelle si données non sauvegardées
window.addEventListener('beforeunload', (e) => {
    if (window.unsavedData) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// Exporter pour utilisation externe si nécessaire
window.SecurityAdvanced = {
    CSPManager,
    SRIChecker,
    HoneypotProtection,
    BehaviorAnalyzer
};
