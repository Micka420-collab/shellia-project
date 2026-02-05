-- ===========================================
-- 📊 WEEKLY RECAP SCHEMA - Récap Hebdomadaire
-- ===========================================

-- Table: Configuration récap
CREATE TABLE weekly_recap_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL UNIQUE,
    admin_channel_id BIGINT NOT NULL,
    recap_day INTEGER DEFAULT 0,  -- 0=Lundi, 6=Dimanche
    recap_hour INTEGER DEFAULT 9,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: Historique des récaps
CREATE TABLE weekly_recaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    
    -- Communauté
    new_members INTEGER DEFAULT 0,
    total_members INTEGER DEFAULT 0,
    active_members INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    
    -- Économie
    revenue DECIMAL(10, 2) DEFAULT 0,
    mrr DECIMAL(10, 2) DEFAULT 0,
    new_subscriptions INTEGER DEFAULT 0,
    churned_subscriptions INTEGER DEFAULT 0,
    
    -- Giveaways
    giveaways_completed INTEGER DEFAULT 0,
    giveaway_participants INTEGER DEFAULT 0,
    giveaway_cost DECIMAL(10, 2) DEFAULT 0,
    giveaway_roi DECIMAL(5, 2) DEFAULT 0,
    
    -- Marketing
    promotions_sent INTEGER DEFAULT 0,
    promotions_converted INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    
    -- Contenu
    images_generated INTEGER DEFAULT 0,
    ai_requests INTEGER DEFAULT 0,
    api_cost DECIMAL(10, 2) DEFAULT 0,
    
    -- Modération
    warns_issued INTEGER DEFAULT 0,
    bans_issued INTEGER DEFAULT 0,
    tickets_resolved INTEGER DEFAULT 0,
    
    -- Analyse IA
    analysis_summary JSONB,
    strengths JSONB,
    weaknesses JSONB,
    recommendations JSONB,
    
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_weekly_recaps_guild ON weekly_recaps(guild_id);
CREATE INDEX idx_weekly_recaps_week ON weekly_recaps(week_start DESC);

-- Table: Daily stats (pour agrégation hebdo)
CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    date DATE NOT NULL,
    new_members INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    images_generated INTEGER DEFAULT 0,
    ai_requests INTEGER DEFAULT 0,
    api_cost DECIMAL(10, 2) DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    UNIQUE(guild_id, date)
);

CREATE INDEX idx_daily_stats_guild_date ON daily_stats(guild_id, date DESC);

-- ===========================================
-- 🔒 RLS
-- ===========================================

ALTER TABLE weekly_recap_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_recaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Weekly recap config admin only"
    ON weekly_recap_config FOR ALL USING (is_admin_user(auth.uid()));

CREATE POLICY "Weekly recaps admin only"
    ON weekly_recaps FOR ALL USING (is_admin_user(auth.uid()));

CREATE POLICY "Daily stats admin only"
    ON daily_stats FOR ALL USING (is_admin_user(auth.uid()));

-- ===========================================
-- 🔄 Functions
-- ===========================================

-- Fonction: Agréger les stats journalières en hebdomadaires
CREATE OR REPLACE FUNCTION aggregate_weekly_stats(
    p_guild_id BIGINT,
    p_week_start DATE
)
RETURNS VOID AS $$
DECLARE
    v_week_end DATE;
BEGIN
    v_week_end := p_week_start + INTERVAL '6 days';
    
    INSERT INTO weekly_recaps (
        guild_id, week_start, week_end,
        new_members, messages_sent, images_generated, ai_requests, api_cost, revenue
    )
    SELECT 
        p_guild_id,
        p_week_start,
        v_week_end,
        COALESCE(SUM(new_members), 0),
        COALESCE(SUM(messages_sent), 0),
        COALESCE(SUM(images_generated), 0),
        COALESCE(SUM(ai_requests), 0),
        COALESCE(SUM(api_cost), 0),
        COALESCE(SUM(revenue), 0)
    FROM daily_stats
    WHERE guild_id = p_guild_id
    AND date >= p_week_start
    AND date <= v_week_end
    ON CONFLICT (guild_id, week_start) DO UPDATE SET
        new_members = EXCLUDED.new_members,
        messages_sent = EXCLUDED.messages_sent,
        images_generated = EXCLUDED.images_generated,
        ai_requests = EXCLUDED.ai_requests,
        api_cost = EXCLUDED.api_cost,
        revenue = EXCLUDED.revenue;
END;
$$ LANGUAGE plpgsql;
