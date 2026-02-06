-- ===========================================
-- 🎫 TICKETS SCHEMA - Système de Tickets Support
-- ===========================================

-- Table: Tickets
CREATE TABLE tickets (
    id VARCHAR(8) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    plan_at_creation VARCHAR(20) DEFAULT 'free',
    
    -- Gestion
    assigned_to BIGINT,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    closed_by BIGINT,
    close_reason TEXT,
    
    -- Métadonnées
    first_response_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    satisfaction_rating INTEGER CHECK (satisfaction_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_tickets_user ON tickets(user_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_assigned ON tickets(assigned_to);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);

-- Table: Messages des tickets
CREATE TABLE ticket_messages (
    id VARCHAR(12) PRIMARY KEY,
    ticket_id VARCHAR(8) REFERENCES tickets(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,  -- Message interne (admin only)
    attachments JSONB,  -- URLs des pièces jointes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ticket_messages_ticket ON ticket_messages(ticket_id);
CREATE INDEX idx_ticket_messages_author ON ticket_messages(author_id);
CREATE INDEX idx_ticket_messages_internal ON ticket_messages(is_internal);

-- Table: Historique des actions (audit trail)
CREATE TABLE ticket_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(8) REFERENCES tickets(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,  -- created, updated, assigned, closed, etc.
    performed_by BIGINT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ticket_audit_ticket ON ticket_audit_log(ticket_id);
CREATE INDEX idx_ticket_audit_action ON ticket_audit_log(action);

-- Table: Catégories personnalisables
CREATE TABLE ticket_categories (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    emoji VARCHAR(10),
    auto_assign_to BIGINT,  -- Admin assigné automatiquement
    response_time_sla INTEGER,  -- SLA en heures
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Catégories par défaut
INSERT INTO ticket_categories (id, name, description, emoji, response_time_sla) VALUES
('general', 'Général', 'Questions générales', '❓', 48),
('billing', 'Facturation', 'Problèmes de paiement et factures', '💳', 24),
('technical', 'Support Technique', 'Problèmes techniques', '🔧', 24),
('feature_request', 'Demande de Fonctionnalité', 'Suggestions d\'améliorations', '💡', 72),
('bug', 'Bug', 'Signalement de bugs', '🐛', 12),
('account', 'Compte', 'Gestion de compte', '👤', 24);

-- ===========================================
-- 🔒 RLS Policies (Row Level Security)
-- ===========================================

ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_audit_log ENABLE ROW LEVEL SECURITY;

-- Users can only see their own tickets
CREATE POLICY "Users can view own tickets" 
    ON tickets FOR SELECT 
    USING (auth.uid() = user_id OR is_admin_user(auth.uid()));

-- Users can only create tickets for themselves
CREATE POLICY "Users can create own tickets"
    ON tickets FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own open tickets
CREATE POLICY "Users can update own open tickets"
    ON tickets FOR UPDATE
    USING (auth.uid() = user_id AND status NOT IN ('closed', 'resolved'))
    OR is_admin_user(auth.uid());

-- Admins can manage all tickets
CREATE POLICY "Admins can manage all tickets"
    ON tickets FOR ALL
    USING (is_admin_user(auth.uid()));

-- Messages policies
CREATE POLICY "Users can view messages of their tickets"
    ON ticket_messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM tickets t 
            WHERE t.id = ticket_messages.ticket_id 
            AND (t.user_id = auth.uid() OR is_admin_user(auth.uid()))
        )
        AND (NOT is_internal OR is_admin_user(auth.uid()))
    );

CREATE POLICY "Users can add messages to their tickets"
    ON ticket_messages FOR INSERT
    WITH CHECK (
        auth.uid() = author_id
        AND EXISTS (
            SELECT 1 FROM tickets t 
            WHERE t.id = ticket_messages.ticket_id 
            AND t.user_id = auth.uid()
            AND t.status NOT IN ('closed', 'resolved')
        )
    );

CREATE POLICY "Admins can manage all messages"
    ON ticket_messages FOR ALL
    USING (is_admin_user(auth.uid()));

-- ===========================================
-- 📊 Views et Functions
-- ===========================================

-- Vue: Stats des tickets
CREATE VIEW ticket_stats AS
SELECT 
    COUNT(*) as total_tickets,
    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tickets,
    COUNT(CASE WHEN status = 'waiting_user' THEN 1 END) as waiting_user_tickets,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_tickets,
    COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_tickets,
    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_priority_tickets,
    AVG(EXTRACT(EPOCH FROM (COALESCE(resolved_at, closed_at) - created_at))/3600) as avg_resolution_hours
FROM tickets
WHERE created_at > NOW() - INTERVAL '30 days';

-- Vue: Performance des agents (admins)
CREATE VIEW agent_performance AS
SELECT 
    assigned_to as agent_id,
    COUNT(*) as total_assigned,
    COUNT(CASE WHEN status IN ('resolved', 'closed') THEN 1 END) as resolved_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(resolved_at, closed_at) - created_at))/3600) as avg_resolution_hours,
    AVG(satisfaction_rating) as avg_satisfaction
FROM tickets
WHERE assigned_to IS NOT NULL
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY assigned_to;

-- Function: Créer un ticket avec log d'audit
CREATE OR REPLACE FUNCTION create_ticket_with_audit(
    p_user_id BIGINT,
    p_guild_id BIGINT,
    p_subject VARCHAR,
    p_description TEXT,
    p_category VARCHAR DEFAULT 'general',
    p_priority VARCHAR DEFAULT 'medium',
    p_plan VARCHAR DEFAULT 'free'
)
RETURNS VARCHAR AS $$
DECLARE
    v_ticket_id VARCHAR;
BEGIN
    -- Générer ID
    v_ticket_id := substr(gen_random_uuid()::text, 1, 8);
    
    -- Créer le ticket
    INSERT INTO tickets (id, user_id, guild_id, subject, description, 
                        category, priority, plan_at_creation, created_by)
    VALUES (v_ticket_id, p_user_id, p_guild_id, p_subject, p_description,
           p_category, p_priority, p_plan, p_user_id);
    
    -- Log d'audit
    INSERT INTO ticket_audit_log (ticket_id, action, performed_by, new_value)
    VALUES (v_ticket_id, 'created', p_user_id, 
           jsonb_build_object('subject', p_subject, 'category', p_category));
    
    RETURN v_ticket_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Mettre à jour statut avec audit
CREATE OR REPLACE FUNCTION update_ticket_status(
    p_ticket_id VARCHAR,
    p_new_status VARCHAR,
    p_user_id BIGINT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_status VARCHAR;
BEGIN
    -- Récupérer ancien statut
    SELECT status INTO v_old_status FROM tickets WHERE id = p_ticket_id;
    
    IF v_old_status IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Mettre à jour
    UPDATE tickets 
    SET status = p_new_status, 
        updated_at = NOW(),
        resolved_at = CASE WHEN p_new_status = 'resolved' THEN NOW() ELSE resolved_at END,
        closed_at = CASE WHEN p_new_status = 'closed' THEN NOW() ELSE closed_at END
    WHERE id = p_ticket_id;
    
    -- Audit
    INSERT INTO ticket_audit_log (ticket_id, action, performed_by, old_value, new_value)
    VALUES (p_ticket_id, 'status_changed', p_user_id,
           jsonb_build_object('status', v_old_status),
           jsonb_build_object('status', p_new_status));
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_ticket_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ticket_timestamp
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_ticket_timestamp();
