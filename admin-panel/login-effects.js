/**
 * EFFETS VISUELS - Page de Login Shellia AI
 * Animations et particules pour le fond
 */

// Configuration des particules
const PARTICLE_CONFIG = {
    count: 50,
    minSize: 2,
    maxSize: 4,
    minSpeed: 0.5,
    maxSpeed: 1.5,
    connectionDistance: 150,
    colors: ['#3b82f6', '#7c3aed', '#06b6d4']
};

class ParticleSystem {
    constructor() {
        this.canvas = document.getElementById('particle-canvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: null, y: null };
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        this.resize();
        this.createParticles();
        this.bindEvents();
        this.animate();
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticles() {
        this.particles = [];
        
        for (let i = 0; i < PARTICLE_CONFIG.count; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * (PARTICLE_CONFIG.maxSize - PARTICLE_CONFIG.minSize) + PARTICLE_CONFIG.minSize,
                speedX: (Math.random() - 0.5) * PARTICLE_CONFIG.maxSpeed,
                speedY: (Math.random() - 0.5) * PARTICLE_CONFIG.maxSpeed,
                color: PARTICLE_CONFIG.colors[Math.floor(Math.random() * PARTICLE_CONFIG.colors.length)],
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }
    
    bindEvents() {
        window.addEventListener('resize', () => {
            this.resize();
            this.createParticles();
        });
        
        // Interaction avec la souris
        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.x;
            this.mouse.y = e.y;
        });
        
        window.addEventListener('mouseleave', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Mettre à jour et dessiner les particules
        this.particles.forEach((particle, index) => {
            // Mouvement
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            // Rebond sur les bords
            if (particle.x < 0 || particle.x > this.canvas.width) {
                particle.speedX *= -1;
            }
            if (particle.y < 0 || particle.y > this.canvas.height) {
                particle.speedY *= -1;
            }
            
            // Interaction avec la souris
            if (this.mouse.x !== null && this.mouse.y !== null) {
                const dx = this.mouse.x - particle.x;
                const dy = this.mouse.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    const force = (100 - distance) / 100;
                    particle.x -= dx * force * 0.02;
                    particle.y -= dy * force * 0.02;
                }
            }
            
            // Dessiner la particule
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = particle.color;
            this.ctx.globalAlpha = particle.opacity;
            this.ctx.fill();
            
            // Connexions entre particules proches
            for (let j = index + 1; j < this.particles.length; j++) {
                const other = this.particles[j];
                const dx = particle.x - other.x;
                const dy = particle.y - other.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < PARTICLE_CONFIG.connectionDistance) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(other.x, other.y);
                    this.ctx.strokeStyle = particle.color;
                    this.ctx.globalAlpha = (1 - distance / PARTICLE_CONFIG.connectionDistance) * 0.2;
                    this.ctx.lineWidth = 1;
                    this.ctx.stroke();
                }
            }
        });
        
        this.ctx.globalAlpha = 1;
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// Effet de scanline (optionnel)
function createScanlineEffect() {
    const style = document.createElement('style');
    style.textContent = `
        .scanline {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent);
            animation: scan 8s linear infinite;
            pointer-events: none;
            z-index: 2;
        }
        
        @keyframes scan {
            0% { transform: translateY(-100vh); }
            100% { transform: translateY(100vh); }
        }
    `;
    document.head.appendChild(style);
    
    const scanline = document.createElement('div');
    scanline.className = 'scanline';
    document.body.appendChild(scanline);
}

// Effet de glitch sur le titre (subtil)
function addGlitchEffect() {
    const logo = document.querySelector('.logo-text h1');
    if (!logo) return;
    
    const originalText = logo.textContent;
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    
    let interval;
    
    logo.addEventListener('mouseenter', () => {
        let iteration = 0;
        clearInterval(interval);
        
        interval = setInterval(() => {
            logo.textContent = originalText
                .split('')
                .map((char, index) => {
                    if (index < iteration) {
                        return originalText[index];
                    }
                    return chars[Math.floor(Math.random() * chars.length)];
                })
                .join('');
            
            if (iteration >= originalText.length) {
                clearInterval(interval);
            }
            
            iteration += 1 / 3;
        }, 30);
    });
}

// Animation du timestamp
function updateTimestamp() {
    const timestampEl = document.getElementById('timestamp');
    if (!timestampEl) return;
    
    function update() {
        const now = new Date();
        timestampEl.textContent = now.toLocaleString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    update();
    setInterval(update, 1000);
}

// Détection de l'IP (simulation pour l'affichage)
function displayIP() {
    const ipEl = document.getElementById('ip-display');
    if (!ipEl) return;
    
    // En production, cette info viendrait du serveur
    // Pour l'instant, on affiche un message générique
    fetch('https://api.ipify.org?format=json')
        .then(res => res.json())
        .then(data => {
            if (data.ip) {
                // Masquer les derniers octets pour la sécurité
                const parts = data.ip.split('.');
                if (parts.length === 4) {
                    ipEl.textContent = `IP: ${parts[0]}.${parts[1]}.**.**`;
                }
            }
        })
        .catch(() => {
            ipEl.textContent = 'IP: Masquée';
        });
}

// Anti-screenshot (optionnel, pour les paranoïaques)
function addAntiScreenshot() {
    // Détecter Print Screen
    document.addEventListener('keyup', (e) => {
        if (e.key === 'PrintScreen') {
            showSecurityWarning('Capture d\'écran détectée');
        }
    });
    
    // Détecter DevTools
    let devtoolsOpen = false;
    const threshold = 160;
    
    setInterval(() => {
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;
        
        if (widthThreshold || heightThreshold) {
            if (!devtoolsOpen) {
                devtoolsOpen = true;
                console.log('%c⚠️ Attention', 'color: red; font-size: 20px; font-weight: bold;');
                console.log('%cCette zone est sécurisée. Toute tentative d\'inspection est loguée.', 'color: orange;');
            }
        } else {
            devtoolsOpen = false;
        }
    }, 500);
}

// Message de sécurité
function showSecurityWarning(message) {
    // Créer un toast de sécurité
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(239, 68, 68, 0.9);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = `🛡️ ${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser le système de particules
    const particleSystem = new ParticleSystem();
    
    // Ajouter les effets
    createScanlineEffect();
    addGlitchEffect();
    updateTimestamp();
    displayIP();
    
    // Protection supplémentaire (désactivable)
    // addAntiScreenshot();
    
    // Cleanup avant de quitter
    window.addEventListener('beforeunload', () => {
        particleSystem.destroy();
    });
});

// Empêcher le clic droit sur la page (optionnel)
// document.addEventListener('contextmenu', (e) => {
//     e.preventDefault();
//     showSecurityWarning('Clic droit désactivé pour la sécurité');
// });
