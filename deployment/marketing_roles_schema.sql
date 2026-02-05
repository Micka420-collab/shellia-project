-- ===========================================
-- 🎭 MARKETING ROLES SCHEMA - Rôles Marketing
-- ===========================================

-- Table: Rôles marketing disponibles
CREATE TABLE marketing_roles (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color INTEGER DEFAULT 0,
    permissions JSONB DEFAULT '[]'::jsonb,
    benefits JSONB DEFAULT '[]'::jsonb,
    requirements JSONB DEFAULT '{}'::jsonb,
    max_slots INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: Attributions de rôles
CREATE TABLE user_marketing_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    role_id VARCHAR(50) REFERENCES marketing_roles(id),
    granted_by BIGINT,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_marketing_roles_user ON user_marketing_roles(user_id);
CREATE INDEX idx_user_marketing_roles_role ON user_marketing_roles(role_id);

-- Table: Candidatures
CREATE TABLE marketing_role_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    role_id VARCHAR(50) REFERENCES marketing_roles(id),
    application_text TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by BIGINT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_marketing_applications_user ON marketing_role_applications(user_id);
CREATE INDEX idx_marketing_applications_status ON marketing_role_applications(status) WHERE status = 'pending';

-- Table: Révocations
CREATE TABLE marketing_role_revocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    role_id VARCHAR(50),
    revoked_by BIGINT,
    reason TEXT,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- 🔒 RLS
-- ===========================================

ALTER TABLE marketing_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_marketing_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_role_applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Marketing roles are viewable by everyone"
    ON marketing_roles FOR SELECT USING (true);

CREATE POLICY "Only admins can modify marketing roles"
    ON marketing_roles FOR ALL USING (is_admin_user(auth.uid()));

CREATE POLICY "Users can view own roles"
    ON user_marketing_roles FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Bot can manage user roles"
    ON user_marketing_roles FOR ALL USING (is_bot_user(auth.uid()));

CREATE POLICY "Users can view own applications"
    ON marketing_role_applications FOR SELECT USING (auth.uid() = user_id);

-- ===========================================
-- 📊 Views
-- ===========================================

CREATE VIEW marketing_role_stats AS
SELECT 
    mr.id,
    mr.name,
    mr.max_slots,
    COUNT(umr.user_id) as current_count,
    mr.max_slots - COUNT(umr.user_id) as remaining_slots
FROM marketing_roles mr
LEFT JOIN user_marketing_roles umr ON mr.id = umr.role_id AND umr.revoked_at IS NULL
WHERE mr.is_active = TRUE
GROUP BY mr.id, mr.name, mr.max_slots;
