-- ===========================================
-- 🎊 GRAND OPENING SCHEMA - Ouverture Officielle
-- ===========================================

-- Table: Configuration ouverture
CREATE TABLE grand_opening_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL UNIQUE,
    opening_date TIMESTAMP WITH TIME ZONE NOT NULL,
    announcement_channel_id BIGINT,
    phase VARCHAR(20) DEFAULT 'prelaunch',
    is_launched BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    launched_at TIMESTAMP WITH TIME ZONE
);

-- Table: Milestones (étapes)
CREATE TABLE opening_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES grand_opening_config(id),
    name VARCHAR(50) NOT NULL,
    description TEXT,
    milestone_date TIMESTAMP WITH TIME ZONE NOT NULL,
    template_type VARCHAR(50),
    announced BOOLEAN DEFAULT FALSE,
    announced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_opening_milestones_config ON opening_milestones(config_id);
CREATE INDEX idx_opening_milestones_date ON opening_milestones(milestone_date);

-- Table: Early adopters (pour remerciements)
CREATE TABLE early_adopters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    thanked BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, guild_id)
);

CREATE INDEX idx_early_adopters_guild ON early_adopters(guild_id);

-- Table: Historique des ouvertures
CREATE TABLE opening_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    member_count_at_opening INTEGER,
    total_members_joined_first_day INTEGER,
    revenue_first_day DECIMAL(10, 2),
    notes TEXT
);

-- ===========================================
-- 🔒 RLS
-- ===========================================

ALTER TABLE grand_opening_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE opening_milestones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Opening config admin only"
    ON grand_opening_config FOR ALL USING (is_admin_user(auth.uid()));

CREATE POLICY "Opening milestones viewable"
    ON opening_milestones FOR SELECT USING (true);

-- ===========================================
-- 🔄 Functions
-- ===========================================

-- Fonction: Prochain milestone
CREATE OR REPLACE FUNCTION get_next_opening_milestone(guild_id BIGINT)
RETURNS TABLE (
    name VARCHAR,
    description TEXT,
    milestone_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        om.name,
        om.description,
        om.milestone_date
    FROM opening_milestones om
    JOIN grand_opening_config goc ON om.config_id = goc.id
    WHERE goc.guild_id = guild_id
    AND om.announced = FALSE
    ORDER BY om.milestone_date ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;
