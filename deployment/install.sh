#!/bin/bash
# ============================================
# SHELLIA AI BOT - SCRIPT D'INSTALLATION
# ============================================
# Usage: curl -fsSL https://.../install.sh | bash
# OU: sudo bash install.sh
# ============================================

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="/opt/shellia"
USER="shellia"
REPO_URL="https://github.com/your-username/shellia-bot.git"

# Fonctions
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           🤖 SHELLIA AI BOT - INSTALLATION                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Ce script doit être exécuté en root (sudo)"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "OS non supporté"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        print_error "OS non supporté. Ubuntu ou Debian requis."
        exit 1
    fi
    
    print_success "OS compatible: $PRETTY_NAME"
}

install_dependencies() {
    print_info "Installation des dépendances..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        nginx \
        ufw \
        fail2ban \
        htop \
        ncdu \
        logrotate
    
    print_success "Dépendances installées"
}

create_user() {
    print_info "Création de l'utilisateur $USER..."
    
    if id "$USER" &>/dev/null; then
        print_info "Utilisateur $USER existe déjà"
    else
        useradd -m -s /bin/bash "$USER"
        print_success "Utilisateur $USER créé"
    fi
}

setup_directory() {
    print_info "Configuration du répertoire d'installation..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/backups"
    mkdir -p "$INSTALL_DIR/scripts"
    
    chown -R "$USER:$USER" "$INSTALL_DIR"
    
    print_success "Répertoire configuré: $INSTALL_DIR"
}

clone_repo() {
    print_info "Téléchargement du code..."
    
    cd "$INSTALL_DIR"
    
    if [[ -d ".git" ]]; then
        print_info "Mise à jour du repository..."
        sudo -u "$USER" git pull
    else
        print_info "Clonage du repository..."
        sudo -u "$USER" git clone "$REPO_URL" .
    fi
    
    print_success "Code téléchargé"
}

setup_venv() {
    print_info "Configuration de l'environnement virtuel Python..."
    
    cd "$INSTALL_DIR"
    
    if [[ ! -d "venv" ]]; then
        sudo -u "$USER" python3 -m venv venv
    fi
    
    sudo -u "$USER" bash -c "source venv/bin/activate && pip install --upgrade pip"
    sudo -u "$USER" bash -c "source venv/bin/activate && pip install -r bot/requirements.txt"
    
    print_success "Environnement virtuel configuré"
}

setup_env() {
    print_info "Configuration des variables d'environnement..."
    
    if [[ ! -f "$INSTALL_DIR/bot/.env" ]]; then
        cat > "$INSTALL_DIR/bot/.env" << 'EOF'
# ============================================
# SHELLIA AI BOT - CONFIGURATION
# ============================================

# Discord Bot Token (https://discord.com/developers/applications)
DISCORD_TOKEN=your_discord_bot_token_here

# Discord Guild ID (Server ID)
GUILD_ID=your_guild_id_here

# Supabase Configuration (https://supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key_here

# Google Gemini API Key (https://aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here

# Stripe Configuration (Optional)
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Admin Panel Configuration
ADMIN_PANEL_PORT=8080
ADMIN_PANEL_SECRET=your_admin_panel_secret_here

# Bot Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
        
        chown "$USER:$USER" "$INSTALL_DIR/bot/.env"
        chmod 600 "$INSTALL_DIR/bot/.env"
        
        print_info "Fichier .env créé. Veuillez l'éditer avec vos clés:"
        print_info "  nano $INSTALL_DIR/bot/.env"
    else
        print_info "Fichier .env existe déjà"
    fi
}

setup_systemd() {
    print_info "Configuration du service systemd..."
    
    cp "$INSTALL_DIR/deployment/shellia-bot.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable shellia-bot
    
    print_success "Service systemd configuré"
}

setup_firewall() {
    print_info "Configuration du firewall..."
    
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8080/tcp
    
    echo "y" | ufw enable
    
    print_success "Firewall configuré"
}

setup_logrotate() {
    print_info "Configuration de logrotate..."
    
    cat > /etc/logrotate.d/shellia-bot << 'EOF'
/opt/shellia/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 shellia shellia
    sharedscripts
    postrotate
        systemctl reload shellia-bot > /dev/null 2>&1 || true
    endscript
}
EOF
    
    print_success "Logrotate configuré"
}

create_scripts() {
    print_info "Création des scripts utilitaires..."
    
    # Healthcheck script
    cat > "$INSTALL_DIR/scripts/healthcheck.sh" << 'EOF'
#!/bin/bash
BOT_STATUS=$(systemctl is-active shellia-bot)
if [ "$BOT_STATUS" != "active" ]; then
    echo "$(date): Bot is DOWN, restarting..." >> /opt/shellia/logs/health.log
    systemctl restart shellia-bot
fi
EOF
    
    # Backup script
    cat > "$INSTALL_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/shellia/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup .env
cp /opt/shellia/bot/.env "$BACKUP_DIR/env_backup_$DATE"

# Backup logs
tar -czf "$BACKUP_DIR/logs_backup_$DATE.tar.gz" -C /opt/shellia logs/

# Cleanup old backups (keep 14 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +14 -delete
find "$BACKUP_DIR" -name "env_backup_*" -mtime +14 -delete

echo "$(date): Backup completed" >> /opt/shellia/logs/backup.log
EOF
    
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    chown -R "$USER:$USER" "$INSTALL_DIR/scripts"
    
    print_success "Scripts créés"
}

setup_cron() {
    print_info "Configuration des tâches cron..."
    
    # Crontab pour root
    cat > /tmp/shellia-cron << 'EOF'
# Shellia Bot - Cron Jobs

# Healthcheck toutes les 5 minutes
*/5 * * * * /opt/shellia/scripts/healthcheck.sh

# Backup quotidien à 3h du matin
0 3 * * * /opt/shellia/scripts/backup.sh

# Nettoyage hebdomadaire
0 0 * * 0 find /opt/shellia/logs -name "*.log" -mtime +30 -delete
EOF
    
    crontab /tmp/shellia-cron
    rm /tmp/shellia-cron
    
    print_success "Cron jobs configurés"
}

print_final_instructions() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              ✅ INSTALLATION TERMINÉE                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${YELLOW}Prochaines étapes:${NC}"
    echo ""
    echo "1. Configurer les variables d'environnement:"
    echo "   nano $INSTALL_DIR/bot/.env"
    echo ""
    echo "2. Configurer Supabase:"
    echo "   - Créer un projet sur https://supabase.com"
    echo "   - Exécuter le schema SQL: deployment/supabase_schema.sql"
    echo ""
    echo "3. Démarrer le bot:"
    echo "   systemctl start shellia-bot"
    echo ""
    echo "4. Vérifier le statut:"
    echo "   systemctl status shellia-bot"
    echo "   journalctl -u shellia-bot -f"
    echo ""
    echo -e "${BLUE}Documentation complète:${NC}"
    echo "   $INSTALL_DIR/documentation/IA_SHELLIA_GUIDE.md"
    echo ""
    echo -e "${GREEN}Bon chat avec Shellia! 🤖${NC}"
}

# Main
main() {
    print_header
    
    check_root
    check_os
    
    print_info "Début de l'installation..."
    
    install_dependencies
    create_user
    setup_directory
    clone_repo
    setup_venv
    setup_env
    setup_systemd
    setup_firewall
    setup_logrotate
    create_scripts
    setup_cron
    
    print_final_instructions
}

# Exécuter
main "$@"
