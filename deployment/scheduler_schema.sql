-- ============================================================================
-- SCHÉMA PLANIFICATEUR DE TÂCHES - Shellia AI Dashboard
-- Gestion des tâches répétitives et planifiées
-- ============================================================================

-- ============================================================================
-- 1. TABLE DES TÂCHES PLANIFIÉES
-- ============================================================================

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL, -- 'backup', 'cleanup', 'report', 'notification', 'custom'
    
    -- Configuration cron (format standard)
    cron_expression VARCHAR(100) NOT NULL, -- ex: '0 2 * * *' pour 2h du matin quotidien
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Paramètres de la tâche (JSON)
    parameters JSONB DEFAULT '{}',
    
    -- État
    is_active BOOLEAN DEFAULT TRUE,
    is_running BOOLEAN DEFAULT FALSE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- Métadonnées
    created_by UUID REFERENCES admin_users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Limite d'exécution
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600 -- 1 heure par défaut
);

CREATE INDEX idx_scheduled_tasks_active ON scheduled_tasks(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_at);
CREATE INDEX idx_scheduled_tasks_type ON scheduled_tasks(task_type);

-- Vue des tâches actives avec prochaine exécution
CREATE OR REPLACE VIEW upcoming_tasks AS
SELECT 
    id,
    name,
    task_type,
    cron_expression,
    next_run_at,
    is_running,
    CASE 
        WHEN next_run_at < NOW() THEN 'overdue'
        WHEN next_run_at < NOW() + INTERVAL '1 hour' THEN 'soon'
        ELSE 'scheduled'
    END as status
FROM scheduled_tasks
WHERE is_active = TRUE
ORDER BY next_run_at ASC;

-- ============================================================================
-- 2. TABLE DES EXÉCUTIONS DE TÂCHES
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES scheduled_tasks(id) ON DELETE CASCADE,
    
    -- Statut
    status VARCHAR(20) NOT NULL, -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Résultats
    output TEXT, -- Logs de sortie
    error_message TEXT,
    result_data JSONB, -- Données de résultat
    
    -- Retry
    retry_count INTEGER DEFAULT 0,
    is_retry BOOLEAN DEFAULT FALSE,
    original_execution_id UUID REFERENCES task_executions(id),
    
    -- Métadonnées
    triggered_by VARCHAR(50) DEFAULT 'scheduler', -- 'scheduler', 'manual', 'api'
    executed_by UUID REFERENCES admin_users(id), -- Si exécution manuelle
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_task_executions_task ON task_executions(task_id);
CREATE INDEX idx_task_executions_status ON task_executions(status);
CREATE INDEX idx_task_executions_created ON task_executions(created_at DESC);

-- Vue des exécutions récentes
CREATE OR REPLACE VIEW recent_task_executions AS
SELECT 
    te.*,
    st.name as task_name,
    st.task_type
FROM task_executions te
JOIN scheduled_tasks st ON te.task_id = st.id
ORDER BY te.created_at DESC;

-- ============================================================================
-- 3. TABLE DES TEMPLATES DE TÂCHES
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    
    -- Configuration par défaut
    default_cron VARCHAR(100),
    default_parameters JSONB DEFAULT '{}',
    default_timeout INTEGER DEFAULT 3600,
    
    -- Script/commande à exécuter
    script_content TEXT,
    script_language VARCHAR(20), -- 'sql', 'python', 'bash', 'javascript'
    
    -- Métadonnées
    is_system BOOLEAN DEFAULT FALSE, -- Ne peut pas être supprimé
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insertion des templates par défaut
INSERT INTO task_templates (name, description, task_type, default_cron, default_parameters, script_content, script_language, is_system) VALUES
('backup_database', 'Sauvegarde complète de la base de données', 'backup', '0 2 * * *', '{}', 
 'SELECT pg_dump($1) INTO OUTFILE $2', 'sql', TRUE),

('cleanup_old_logs', 'Nettoyage des logs de plus de 90 jours', 'cleanup', '0 3 * * 0', '{"days": 90}', 
 'DELETE FROM security_logs WHERE timestamp < NOW() - INTERVAL ''$1 days'';', 'sql', TRUE),

('cleanup_rate_limits', 'Nettoyage des rate limits expirés', 'cleanup', '0 */6 * * *', '{}', 
 'SELECT cleanup_expired_rate_limits();', 'sql', TRUE),

('archive_conversations', 'Archivage des conversations de plus de 30 jours', 'cleanup', '0 4 * * *', '{"days": 30}', 
 'SELECT archive_old_conversations($1);', 'sql', TRUE),

('generate_daily_report', 'Rapport quotidien d''activité', 'report', '0 8 * * *', '{}', 
 'SELECT * FROM generate_daily_stats();', 'sql', TRUE),

('notify_low_quota', 'Notification aux utilisateurs avec quota faible', 'notification', '0 18 * * *', '{"threshold": 0.2}', 
 'SELECT notify_low_quota_users($1);', 'sql', TRUE),

('cleanup_sessions', 'Nettoyage des sessions expirées', 'cleanup', '0 */12 * * *', '{}', 
 'SELECT cleanup_expired_sessions();', 'sql', TRUE)

ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 4. FONCTIONS RPC
-- ============================================================================

-- Créer une nouvelle tâche planifiée
CREATE OR REPLACE FUNCTION create_scheduled_task(
    p_name VARCHAR,
    p_description TEXT,
    p_task_type VARCHAR,
    p_cron_expression VARCHAR,
    p_parameters JSONB DEFAULT '{}',
    p_timezone VARCHAR DEFAULT 'UTC',
    p_created_by UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_task_id UUID;
    v_next_run TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Calculer la prochaine exécution
    -- Note: En production, utilisez une extension comme pg_cron ou un service externe
    v_next_run := NOW() + INTERVAL '1 hour'; -- Simplifié
    
    INSERT INTO scheduled_tasks (
        name, description, task_type, cron_expression, timezone,
        parameters, next_run_at, created_by
    ) VALUES (
        p_name, p_description, p_task_type, p_cron_expression, p_timezone,
        p_parameters, v_next_run, p_created_by
    )
    RETURNING id INTO v_task_id;
    
    RETURN v_task_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Mettre à jour une tâche
CREATE OR REPLACE FUNCTION update_scheduled_task(
    p_task_id UUID,
    p_name VARCHAR DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_cron_expression VARCHAR DEFAULT NULL,
    p_parameters JSONB DEFAULT NULL,
    p_is_active BOOLEAN DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE scheduled_tasks
    SET
        name = COALESCE(p_name, name),
        description = COALESCE(p_description, description),
        cron_expression = COALESCE(p_cron_expression, cron_expression),
        parameters = COALESCE(p_parameters, parameters),
        is_active = COALESCE(p_is_active, is_active),
        updated_at = NOW()
    WHERE id = p_task_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Supprimer une tâche
CREATE OR REPLACE FUNCTION delete_scheduled_task(
    p_task_id UUID
) RETURNS BOOLEAN AS $$
BEGIN
    -- Vérifier que ce n'est pas une tâche système
    IF EXISTS (SELECT 1 FROM scheduled_tasks WHERE id = p_task_id AND is_system = TRUE) THEN
        RETURN FALSE;
    END IF;
    
    DELETE FROM scheduled_tasks WHERE id = p_task_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Exécuter une tâche manuellement
CREATE OR REPLACE FUNCTION execute_task_now(
    p_task_id UUID,
    p_executed_by UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_execution_id UUID;
BEGIN
    -- Marquer la tâche comme running
    UPDATE scheduled_tasks 
    SET is_running = TRUE, last_run_at = NOW()
    WHERE id = p_task_id;
    
    -- Créer une entrée d'exécution
    INSERT INTO task_executions (
        task_id, status, started_at, triggered_by, executed_by
    ) VALUES (
        p_task_id, 'running', NOW(), 'manual', p_executed_by
    )
    RETURNING id INTO v_execution_id;
    
    RETURN v_execution_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Compléter une exécution
CREATE OR REPLACE FUNCTION complete_task_execution(
    p_execution_id UUID,
    p_status VARCHAR,
    p_output TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_result_data JSONB DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_task_id UUID;
    v_duration INTEGER;
BEGIN
    -- Récupérer la tâche associée
    SELECT task_id INTO v_task_id 
    FROM task_executions 
    WHERE id = p_execution_id;
    
    -- Calculer la durée
    SELECT EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER 
    INTO v_duration
    FROM task_executions
    WHERE id = p_execution_id;
    
    -- Mettre à jour l'exécution
    UPDATE task_executions
    SET
        status = p_status,
        completed_at = NOW(),
        duration_seconds = v_duration,
        output = p_output,
        error_message = p_error_message,
        result_data = p_result_data
    WHERE id = p_execution_id;
    
    -- Mettre à jour la tâche
    UPDATE scheduled_tasks
    SET
        is_running = FALSE,
        last_run_at = NOW(),
        next_run_at = NOW() + INTERVAL '1 day' -- Simplifié, devrait parser le cron
    WHERE id = v_task_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Obtenir les statistiques des tâches
CREATE OR REPLACE FUNCTION get_task_statistics(
    p_task_id UUID DEFAULT NULL,
    p_days INTEGER DEFAULT 7
) RETURNS TABLE(
    total_executions BIGINT,
    successful_executions BIGINT,
    failed_executions BIGINT,
    avg_duration_seconds INTEGER,
    last_execution_status VARCHAR,
    last_execution_time TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_executions,
        COUNT(*) FILTER (WHERE status = 'completed')::BIGINT as successful_executions,
        COUNT(*) FILTER (WHERE status = 'failed')::BIGINT as failed_executions,
        AVG(duration_seconds)::INTEGER as avg_duration_seconds,
        (SELECT status FROM task_executions WHERE task_id = COALESCE(p_task_id, task_executions.task_id) ORDER BY created_at DESC LIMIT 1) as last_execution_status,
        (SELECT created_at FROM task_executions WHERE task_id = COALESCE(p_task_id, task_executions.task_id) ORDER BY created_at DESC LIMIT 1) as last_execution_time
    FROM task_executions
    WHERE (p_task_id IS NULL OR task_id = p_task_id)
    AND created_at > NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 5. POLITIQUES RLS
-- ============================================================================

ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_templates ENABLE ROW LEVEL SECURITY;

-- Politiques pour service_role
CREATE POLICY service_scheduled_tasks ON scheduled_tasks
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_task_executions ON task_executions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY service_task_templates ON task_templates
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================================
-- 6. TRIGGERS
-- ============================================================================

-- Mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_scheduled_tasks_updated_at
    BEFORE UPDATE ON scheduled_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 7. COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE scheduled_tasks IS 'Tâches planifiées récurrentes';
COMMENT ON TABLE task_executions IS 'Historique des exécutions de tâches';
COMMENT ON TABLE task_templates IS 'Templates prédéfinis de tâches';
