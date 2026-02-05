-- ============================================================
-- SCHÉMA DE SÉCURITÉ AVANCÉ - Shellia AI Bot
-- Tables pour rate limiting persistant, logs de sécurité, audit
-- ============================================================

-- ============================================================
-- 1. RATE LIMITING PERSISTANT (Fallback Redis)
-- ============================================================

CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    period VARCHAR(20) NOT NULL CHECK (period IN ('minute', 'hour', 'day')),
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    count INTEGER DEFAULT 1,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, period, window_start)
);

CREATE INDEX idx_rate_limits_user ON rate_limits(user_id);
CREATE INDEX idx_rate_limits_expires ON rate_limits(expires_at);
CREATE INDEX idx_rate_limits_window ON rate_limits(user_id, period, window_start);

-- Fonction pour incrémenter atomiquement
CREATE OR REPLACE FUNCTION increment_rate_limit(
    p_user_id BIGINT,
    p_period VARCHAR,
    p_window_start TIMESTAMP WITH TIME ZONE,
    p_expires_at TIMESTAMP WITH TIME ZONE
) RETURNS TABLE(count INTEGER) AS $$
BEGIN
    INSERT INTO rate_limits (user_id, period, window_start, expires_at, count)
    VALUES (p_user_id, p_period, p_window_start, p_expires_at, 1)
    ON CONFLICT (user_id, period, window_start)
    DO UPDATE SET count = rate_limits.count + 1
    RETURNING rate_limits.count INTO count;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Nettoyage automatique des entrées expirées (à exécuter périodiquement)
CREATE OR REPLACE FUNCTION cleanup_expired_rate_limits()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rate_limits WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 2. HISTORIQUE DE CONVERSATION PERSISTANT
-- ============================================================

CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'model', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    compression VARCHAR(10) DEFAULT NULL
);

CREATE INDEX idx_conversation_user ON conversation_history(user_id);
CREATE INDEX idx_conversation_timestamp ON conversation_history(timestamp);
CREATE INDEX idx_conversation_user_time ON conversation_history(user_id, timestamp DESC);

-- Table d'archive pour vieilles conversations
CREATE TABLE IF NOT EXISTS conversation_archive (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    conversation_data TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    date_from TIMESTAMP WITH TIME ZONE,
    date_to TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_archive_user ON conversation_archive(user_id);
CREATE INDEX idx_archive_date ON conversation_archive(archived_at);

-- Fonction pour archiver les vieilles conversations
CREATE OR REPLACE FUNCTION archive_old_conversations(
    max_age_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER := 0;
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT DISTINCT user_id
        FROM conversation_history
        WHERE timestamp < NOW() - INTERVAL '1 day' * max_age_days
    LOOP
        -- Insérer dans archive (simplifié - en pratique compresser)
        INSERT INTO conversation_archive (
            user_id, 
            conversation_data, 
            message_count,
            date_from,
            date_to
        )
        SELECT 
            user_id,
            jsonb_agg(
                jsonb_build_object(
                    'role', role,
                    'content', content,
                    'timestamp', timestamp
                )
            )::text,
            COUNT(*),
            MIN(timestamp),
            MAX(timestamp)
        FROM conversation_history
        WHERE user_id = rec.user_id
        AND timestamp < NOW() - INTERVAL '1 day' * max_age_days
        GROUP BY user_id;
        
        -- Supprimer de l'historique
        DELETE FROM conversation_history
        WHERE user_id = rec.user_id
        AND timestamp < NOW() - INTERVAL '1 day' * max_age_days;
        
        archived_count := archived_count + 1;
    END LOOP;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 3. LOGS DE WEBHOOKS STRIPE
-- ============================================================

CREATE TABLE IF NOT EXISTS webhook_logs (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100),
    event_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('processed', 'error', 'ignored', 'invalid')),
    stripe_signature VARCHAR(200),
    result TEXT,
    error TEXT,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET
);

CREATE INDEX idx_webhook_logs_event ON webhook_logs(event_id);
CREATE INDEX idx_webhook_logs_type ON webhook_logs(event_type);
CREATE INDEX idx_webhook_logs_status ON webhook_logs(status);
CREATE INDEX idx_webhook_logs_time ON webhook_logs(processed_at);

-- ============================================================
-- 4. AUDIT LOGS (Actions admin)
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id BIGINT NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_user_id BIGINT,
    target_type VARCHAR(50), -- 'user', 'payment', 'config', etc.
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_admin ON audit_logs(admin_user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_target ON audit_logs(target_user_id);
CREATE INDEX idx_audit_time ON audit_logs(created_at);

-- Fonction helper pour logguer une action
CREATE OR REPLACE FUNCTION log_audit_action(
    p_admin_user_id BIGINT,
    p_action VARCHAR,
    p_target_user_id BIGINT DEFAULT NULL,
    p_target_type VARCHAR DEFAULT NULL,
    p_old_value JSONB DEFAULT NULL,
    p_new_value JSONB DEFAULT NULL,
    p_reason TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO audit_logs (
        admin_user_id, action, target_user_id, target_type,
        old_value, new_value, reason
    ) VALUES (
        p_admin_user_id, p_action, p_target_user_id, p_target_type,
        p_old_value, p_new_value, p_reason
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 5. SECURITY LOGS ÉTENDUS
-- ============================================================

CREATE TABLE IF NOT EXISTS security_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL DEFAULT 0,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    event_data JSONB,
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_security_user ON security_logs(user_id);
CREATE INDEX idx_security_event ON security_logs(event_type);
CREATE INDEX idx_security_severity ON security_logs(severity);
CREATE INDEX idx_security_time ON security_logs(timestamp);

-- ============================================================
-- 6. BANS ET SUSPENSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS user_bans (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    banned_by BIGINT NOT NULL, -- Admin qui a banni
    reason TEXT NOT NULL,
    banned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- NULL = permanent
    is_active BOOLEAN DEFAULT TRUE,
    unbanned_by BIGINT,
    unbanned_at TIMESTAMP WITH TIME ZONE,
    unban_reason TEXT
);

CREATE INDEX idx_bans_user ON user_bans(user_id);
CREATE INDEX idx_bans_active ON user_bans(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_bans_expires ON user_bans(expires_at);

-- Vue pour les bans actifs
CREATE OR REPLACE VIEW active_bans AS
SELECT 
    b.*,
    u.username as banned_username,
    a.username as admin_username
FROM user_bans b
LEFT JOIN users u ON b.user_id = u.user_id
LEFT JOIN users a ON b.banned_by = a.user_id
WHERE b.is_active = TRUE
AND (b.expires_at IS NULL OR b.expires_at > NOW());

-- Fonction pour vérifier si un user est banni
CREATE OR REPLACE FUNCTION is_user_banned(p_user_id BIGINT)
RETURNS TABLE(is_banned BOOLEAN, reason TEXT, expires_at TIMESTAMP WITH TIME ZONE) AS $$
BEGIN
    RETURN QUERY
    SELECT TRUE, b.reason, b.expires_at
    FROM user_bans b
    WHERE b.user_id = p_user_id
    AND b.is_active = TRUE
    AND (b.expires_at IS NULL OR b.expires_at > NOW())
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::TEXT, NULL::TIMESTAMP WITH TIME ZONE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 7. CIRCUIT BREAKER STATE (pour distribution)
-- ============================================================

CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    id SERIAL PRIMARY KEY,
    circuit_name VARCHAR(100) NOT NULL UNIQUE,
    state VARCHAR(20) NOT NULL CHECK (state IN ('closed', 'open', 'half_open')),
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_circuit_name ON circuit_breaker_state(circuit_name);

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_circuit_breaker_updated_at
    BEFORE UPDATE ON circuit_breaker_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 8. IP RATE LIMITING (Protection DDoS)
-- ============================================================

CREATE TABLE IF NOT EXISTS ip_rate_limits (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    UNIQUE(ip_address, endpoint, window_start)
);

CREATE INDEX idx_ip_rate ON ip_rate_limits(ip_address);
CREATE INDEX idx_ip_rate_expires ON ip_rate_limits(expires_at);

-- Fonction pour vérifier limite IP
CREATE OR REPLACE FUNCTION check_ip_rate_limit(
    p_ip INET,
    p_endpoint VARCHAR,
    p_max_requests INTEGER DEFAULT 100
) RETURNS TABLE(allowed BOOLEAN, current_count INTEGER, reset_at TIMESTAMP WITH TIME ZONE) AS $$
DECLARE
    v_count INTEGER;
    v_window TIMESTAMP WITH TIME ZONE;
BEGIN
    v_window := DATE_TRUNC('hour', NOW());
    
    -- Récupérer ou créer le compteur
    SELECT request_count INTO v_count
    FROM ip_rate_limits
    WHERE ip_address = p_ip
    AND endpoint = p_endpoint
    AND window_start = v_window;
    
    IF v_count IS NULL THEN
        v_count := 0;
    END IF;
    
    -- Vérifier limite
    IF v_count >= p_max_requests THEN
        allowed := FALSE;
    ELSE
        allowed := TRUE;
        -- Incrémenter
        INSERT INTO ip_rate_limits (ip_address, endpoint, window_start, expires_at, request_count)
        VALUES (p_ip, p_endpoint, v_window, v_window + INTERVAL '1 hour', 1)
        ON CONFLICT (ip_address, endpoint, window_start)
        DO UPDATE SET request_count = ip_rate_limits.request_count + 1;
    END IF;
    
    current_count := v_count;
    reset_at := v_window + INTERVAL '1 hour';
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 9. CONFIGURATION SÉCURISÉE (pour secrets chiffrés)
-- ============================================================

CREATE TABLE IF NOT EXISTS secure_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    encrypted_value TEXT NOT NULL,
    encrypted_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_secure_config_key ON secure_config(config_key);

-- Trigger pour updated_at
CREATE TRIGGER update_secure_config_updated_at
    BEFORE UPDATE ON secure_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 10. METRICS DE SÉCURITÉ
-- ============================================================

CREATE TABLE IF NOT EXISTS security_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    metric_type VARCHAR(50) NOT NULL,
    metric_value INTEGER DEFAULT 0,
    details JSONB,
    
    UNIQUE(metric_date, metric_type)
);

CREATE INDEX idx_security_metrics_date ON security_metrics(metric_date);
CREATE INDEX idx_security_metrics_type ON security_metrics(metric_type);

-- Vue pour statistiques journalières
CREATE OR REPLACE VIEW daily_security_stats AS
SELECT 
    DATE_TRUNC('day', timestamp) as day,
    event_type,
    COUNT(*) as count,
    COUNT(DISTINCT user_id) as unique_users
FROM security_logs
GROUP BY DATE_TRUNC('day', timestamp), event_type
ORDER BY day DESC, count DESC;

-- ============================================================
-- POLITIQUES RLS (Row Level Security)
-- ============================================================

-- Activer RLS sur toutes les tables
ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_archive ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_bans ENABLE ROW LEVEL SECURITY;
ALTER TABLE circuit_breaker_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE secure_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_metrics ENABLE ROW LEVEL SECURITY;

-- Politiques pour service_role (bot)
CREATE POLICY service_rate_limits ON rate_limits
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_conversation ON conversation_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_webhook_logs ON webhook_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_audit_logs ON audit_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_security_logs ON security_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_user_bans ON user_bans
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_circuit_breaker ON circuit_breaker_state
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_ip_rate_limits ON ip_rate_limits
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_secure_config ON secure_config
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_security_metrics ON security_metrics
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Politiques pour authenticated (lecture seule pour users)
CREATE POLICY user_own_conversation ON conversation_history
    FOR SELECT TO authenticated USING (user_id = auth.uid()::bigint);

-- Politiques pour anon (aucun accès)
-- Par défaut, anon n'a aucun accès grâce à RLS

-- ============================================================
-- COMMENTAIRES ET DOCUMENTATION
-- ============================================================

COMMENT ON TABLE rate_limits IS 'Rate limiting persistant fallback pour Redis';
COMMENT ON TABLE conversation_history IS 'Historique des messages utilisateur/bot';
COMMENT ON TABLE webhook_logs IS 'Logs des webhooks Stripe reçus';
COMMENT ON TABLE audit_logs IS 'Audit trail des actions administrateurs';
COMMENT ON TABLE security_logs IS 'Logs de sécurité et événements suspects';
COMMENT ON TABLE user_bans IS 'Liste des utilisateurs bannis';
COMMENT ON TABLE circuit_breaker_state IS 'État des circuit breakers pour HA';
COMMENT ON TABLE ip_rate_limits IS 'Rate limiting par IP pour protection DDoS';
