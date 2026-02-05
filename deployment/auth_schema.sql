-- ============================================================================
-- SCHÉMA D'AUTHENTIFICATION DISCORD - Shellia AI Dashboard
-- OAuth2 avec Supabase Auth
-- ============================================================================

-- ============================================================================
-- 1. TABLE DES ADMINS
-- ============================================================================

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    discord_id TEXT UNIQUE NOT NULL,
    discord_username TEXT NOT NULL,
    discord_avatar TEXT,
    discord_email TEXT,
    is_super_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_admin_discord_id ON admin_users(discord_id);
CREATE INDEX idx_admin_active ON admin_users(is_active) WHERE is_active = TRUE;

-- Vue des admins actifs
CREATE OR REPLACE VIEW active_admins AS
SELECT * FROM admin_users WHERE is_active = TRUE;

-- ============================================================================
-- 2. TABLE DES SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS admin_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_session_token ON admin_sessions(session_token);
CREATE INDEX idx_session_admin ON admin_sessions(admin_id);
CREATE INDEX idx_session_expires ON admin_sessions(expires_at);

-- Nettoyage automatique des sessions expirées
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM admin_sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. TABLE DES LOGS DE CONNEXION
-- ============================================================================

CREATE TABLE IF NOT EXISTS admin_login_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admin_users(id) ON DELETE SET NULL,
    discord_id TEXT,
    action VARCHAR(50) NOT NULL, -- 'login', 'logout', 'failed', 'refresh'
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_login_logs_admin ON admin_login_logs(admin_id);
CREATE INDEX idx_login_logs_action ON admin_login_logs(action);
CREATE INDEX idx_login_logs_created ON admin_login_logs(created_at);

-- Vue des tentatives de connexion échouées récentes
CREATE OR REPLACE VIEW recent_failed_logins AS
SELECT 
    discord_id,
    COUNT(*) as failed_attempts,
    MAX(created_at) as last_attempt
FROM admin_login_logs
WHERE action = 'failed'
AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY discord_id
HAVING COUNT(*) >= 5;

-- ============================================================================
-- 4. FONCTIONS RPC
-- ============================================================================

-- Créer ou mettre à jour un admin
CREATE OR REPLACE FUNCTION upsert_admin(
    p_discord_id TEXT,
    p_discord_username TEXT,
    p_discord_avatar TEXT DEFAULT NULL,
    p_discord_email TEXT DEFAULT NULL
) RETURNS TABLE(id UUID, is_new BOOLEAN) AS $$
DECLARE
    v_id UUID;
    v_is_new BOOLEAN := FALSE;
BEGIN
    -- Vérifier si l'admin existe
    SELECT id INTO v_id FROM admin_users WHERE discord_id = p_discord_id;
    
    IF v_id IS NULL THEN
        -- Créer nouveau admin
        INSERT INTO admin_users (discord_id, discord_username, discord_avatar, discord_email)
        VALUES (p_discord_id, p_discord_username, p_discord_avatar, p_discord_email)
        RETURNING admin_users.id INTO v_id;
        v_is_new := TRUE;
    ELSE
        -- Mettre à jour les infos
        UPDATE admin_users 
        SET 
            discord_username = p_discord_username,
            discord_avatar = COALESCE(p_discord_avatar, discord_avatar),
            discord_email = COALESCE(p_discord_email, discord_email),
            last_login_at = NOW(),
            updated_at = NOW()
        WHERE id = v_id;
    END IF;
    
    RETURN QUERY SELECT v_id, v_is_new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Créer une session
CREATE OR REPLACE FUNCTION create_session(
    p_admin_id UUID,
    p_session_token TEXT,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_duration_hours INTEGER DEFAULT 24
) RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    -- Nettoyer les anciennes sessions de cet admin
    DELETE FROM admin_sessions 
    WHERE admin_id = p_admin_id 
    AND created_at < NOW() - INTERVAL '7 days';
    
    -- Créer nouvelle session
    INSERT INTO admin_sessions (
        admin_id, 
        session_token, 
        ip_address, 
        user_agent, 
        expires_at
    ) VALUES (
        p_admin_id,
        p_session_token,
        p_ip_address,
        p_user_agent,
        NOW() + (p_duration_hours || ' hours')::INTERVAL
    )
    RETURNING id INTO v_session_id;
    
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Vérifier une session
CREATE OR REPLACE FUNCTION verify_session(
    p_session_token TEXT
) RETURNS TABLE(
    is_valid BOOLEAN,
    admin_id UUID,
    discord_id TEXT,
    discord_username TEXT,
    is_super_admin BOOLEAN
) AS $$
BEGIN
    -- Nettoyer sessions expirées d'abord
    PERFORM cleanup_expired_sessions();
    
    RETURN QUERY
    SELECT 
        TRUE,
        au.id,
        au.discord_id,
        au.discord_username,
        au.is_super_admin
    FROM admin_sessions s
    JOIN admin_users au ON s.admin_id = au.id
    WHERE s.session_token = p_session_token
    AND s.expires_at > NOW()
    AND au.is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::TEXT, NULL::TEXT, FALSE::BOOLEAN;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Révoquer une session
CREATE OR REPLACE FUNCTION revoke_session(
    p_session_token TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM admin_sessions WHERE session_token = p_session_token;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Révoquer toutes les sessions d'un admin
CREATE OR REPLACE FUNCTION revoke_all_admin_sessions(
    p_admin_id UUID
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM admin_sessions WHERE admin_id = p_admin_id;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Logger une tentative de connexion
CREATE OR REPLACE FUNCTION log_admin_login(
    p_discord_id TEXT,
    p_action VARCHAR,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO admin_login_logs (
        admin_id,
        discord_id,
        action,
        ip_address,
        user_agent,
        success,
        error_message
    ) VALUES (
        (SELECT id FROM admin_users WHERE discord_id = p_discord_id),
        p_discord_id,
        p_action,
        p_ip_address,
        p_user_agent,
        p_success,
        p_error_message
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Vérifier si une IP est bannie (rate limiting)
CREATE OR REPLACE FUNCTION is_ip_banned(
    p_ip_address INET
) RETURNS BOOLEAN AS $$
DECLARE
    v_failed_attempts INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_failed_attempts
    FROM admin_login_logs
    WHERE ip_address = p_ip_address
    AND action = 'failed'
    AND created_at > NOW() - INTERVAL '1 hour';
    
    RETURN v_failed_attempts >= 10;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 5. POLITIQUES RLS
-- ============================================================================

-- Activer RLS
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_login_logs ENABLE ROW LEVEL SECURITY;

-- Politiques pour service_role (bot)
CREATE POLICY service_admin_users ON admin_users
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_admin_sessions ON admin_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_admin_login_logs ON admin_login_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Politiques pour authenticated (lecture seule pour les admins eux-mêmes)
CREATE POLICY admin_read_self ON admin_users
    FOR SELECT TO authenticated 
    USING (discord_id = auth.jwt() ->> 'sub');

-- ============================================================================
-- 6. DONNÉES INITIALES
-- ============================================================================

-- Premier super admin (à personnaliser avec votre Discord ID)
-- INSERT INTO admin_users (discord_id, discord_username, is_super_admin, is_active)
-- VALUES ('VOTRE_DISCORD_ID', 'VotrePseudo', TRUE, TRUE)
-- ON CONFLICT (discord_id) DO UPDATE SET is_super_admin = TRUE;

-- ============================================================================
-- 7. COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE admin_users IS 'Administrateurs du dashboard';
COMMENT ON TABLE admin_sessions IS 'Sessions actives des admins';
COMMENT ON TABLE admin_login_logs IS 'Historique des connexions';

-- ============================================================================
-- 8. CRON JOB (nécessite pg_cron extension)
-- ============================================================================

-- Nettoyage quotidien des sessions expirées (si pg_cron disponible)
-- SELECT cron.schedule('cleanup-sessions', '0 0 * * *', 'SELECT cleanup_expired_sessions();');
