-- ===========================================
-- 🦀 OPENCLAW SCHEMA - Gestion Business Automatisée
-- ===========================================

-- Table: Métriques business
CREATE TABLE business_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mrr DECIMAL(10, 2) DEFAULT 0,
    arpu DECIMAL(10, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 4) DEFAULT 0,
    churn_rate DECIMAL(5, 4) DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    paying_users INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    api_cost DECIMAL(10, 2) DEFAULT 0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_business_metrics_date ON business_metrics(recorded_at DESC);
CREATE INDEX idx_business_metrics_mrr ON business_metrics(mrr);

-- Table: Configuration OpenClaw
CREATE TABLE openclaw_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL UNIQUE,
    target_mrr DECIMAL(10, 2) DEFAULT 5000,
    target_conversion DECIMAL(5, 4) DEFAULT 0.05,
    max_cac DECIMAL(10, 2) DEFAULT 50,
    enable_auto_promotions BOOLEAN DEFAULT TRUE,
    max_discount_percent INTEGER DEFAULT 30,
    promotion_cooldown_days INTEGER DEFAULT 7,
    max_giveaway_budget_percent DECIMAL(4, 4) DEFAULT 0.10,
    giveaway_roi_target DECIMAL(4, 2) DEFAULT 2.0,
    churn_threshold_days INTEGER DEFAULT 7,
    winback_discount INTEGER DEFAULT 40,
    winner_plan_duration_days INTEGER DEFAULT 3,
    winner_plan_type VARCHAR(20) DEFAULT 'pro',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: Parcours utilisateurs
CREATE TABLE user_journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL UNIQUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_message_at TIMESTAMP WITH TIME ZONE,
    first_purchase_at TIMESTAMP WITH TIME ZONE,
    last_active_at TIMESTAMP WITH TIME ZONE,
    total_spent DECIMAL(10, 2) DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    engagement_score DECIMAL(5, 2) DEFAULT 0,
    churn_risk BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_journeys_churn ON user_journeys(churn_risk) WHERE churn_risk = TRUE;
CREATE INDEX idx_user_journeys_engagement ON user_journeys(engagement_score DESC);

-- Table: Promotions
CREATE TABLE user_promotions (
    id VARCHAR(8) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    discount_percent INTEGER NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    max_uses INTEGER DEFAULT 1,
    used_count INTEGER DEFAULT 0,
    message TEXT,
    auto_generated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_promotions_user ON user_promotions(user_id);
CREATE INDEX idx_user_promotions_valid ON user_promotions(valid_until) WHERE valid_until > NOW();
CREATE INDEX idx_user_promotions_code ON user_promotions(code);

-- Table: Statistiques de promotions
CREATE TABLE promotion_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id VARCHAR(8) REFERENCES user_promotions(id),
    user_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    discount_percent INTEGER NOT NULL,
    revenue_generated DECIMAL(10, 2) DEFAULT 0,
    converted_to_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_promotion_stats_type ON promotion_stats(type);

-- Table: ROI des giveaways
CREATE TABLE giveaway_roi_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    giveaway_id VARCHAR(8) NOT NULL,
    cost DECIMAL(10, 2) DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10, 2) DEFAULT 0,
    engagement_increase DECIMAL(5, 2) DEFAULT 0,
    roi_ratio DECIMAL(5, 2) DEFAULT 0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_giveaway_roi_giveaway ON giveaway_roi_analysis(giveaway_id);
CREATE INDEX idx_giveaway_roi_ratio ON giveaway_roi_analysis(roi_ratio);

-- Table: Grades Winner
CREATE TABLE winner_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    giveaway_id VARCHAR(8) NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    plan_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    plan_ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, giveaway_id)
);

CREATE INDEX idx_winner_rewards_user ON winner_rewards(user_id);
CREATE INDEX idx_winner_rewards_status ON winner_rewards(status) WHERE status = 'active';
CREATE INDEX idx_winner_rewards_expiry ON winner_rewards(plan_ends_at);

-- Table: Événements milestones
CREATE TABLE milestone_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    value DECIMAL(10, 2) NOT NULL,
    celebrated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_milestone_events_guild ON milestone_events(guild_id);
CREATE INDEX idx_milestone_events_type ON milestone_events(event_type);

-- Table: Paniers abandonnés
CREATE TABLE abandoned_carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    items JSONB NOT NULL,
    total_value DECIMAL(10, 2) NOT NULL,
    abandoned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recovered BOOLEAN DEFAULT FALSE,
    recovery_promo_id VARCHAR(8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_abandoned_carts_user ON abandoned_carts(user_id);
CREATE INDEX idx_abandoned_carts_abandoned ON abandoned_carts(abandoned_at);

-- Table: Subscriptions utilisateurs (complète user_trials)
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    monthly_value DECIMAL(10, 2) DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancel_reason TEXT,
    UNIQUE(user_id, plan) WHERE status = 'active'
);

CREATE INDEX idx_user_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_expires ON user_subscriptions(expires_at);

-- ===========================================
-- 🔒 RLS Policies
-- ===========================================

ALTER TABLE business_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE openclaw_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_journeys ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_promotions ENABLE ROW LEVEL SECURITY;
ALTER TABLE winner_rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestone_events ENABLE ROW LEVEL SECURITY;

-- Policies business_metrics (admin only)
CREATE POLICY "Business metrics admin only"
    ON business_metrics FOR ALL
    USING (is_admin_user(auth.uid()));

-- Policies openclaw_config (admin only)
CREATE POLICY "OpenClaw config admin only"
    ON openclaw_config FOR ALL
    USING (is_admin_user(auth.uid()));

-- Policies user_journeys
CREATE POLICY "Users can view own journey"
    ON user_journeys FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Bot can modify journeys"
    ON user_journeys FOR ALL
    USING (is_bot_user(auth.uid()));

-- Policies user_promotions
CREATE POLICY "Users can view own promotions"
    ON user_promotions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Bot can manage promotions"
    ON user_promotions FOR ALL
    USING (is_bot_user(auth.uid()));

-- Policies winner_rewards
CREATE POLICY "Users can view own winner status"
    ON winner_rewards FOR SELECT
    USING (auth.uid() = user_id);

-- ===========================================
-- 🔄 Triggers
-- ===========================================

-- Trigger: Mise à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_journeys_updated_at
    BEFORE UPDATE ON user_journeys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_openclaw_config_updated_at
    BEFORE UPDATE ON openclaw_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Calcul engagement score
CREATE OR REPLACE FUNCTION calculate_engagement_score()
RETURNS TRIGGER AS $$
DECLARE
    days_since_join INTEGER;
    messages_per_day DECIMAL(10, 2);
    purchase_bonus INTEGER;
BEGIN
    days_since_join := EXTRACT(DAY FROM (NOW() - NEW.joined_at));
    
    IF days_since_join > 0 THEN
        messages_per_day := NEW.messages_sent::DECIMAL / days_since_join;
    ELSE
        messages_per_day := NEW.messages_sent;
    END IF;
    
    purchase_bonus := CASE WHEN NEW.total_spent > 0 THEN 20 ELSE 0 END;
    
    -- Score: messages/jour * 10 + bonus achat + activité récente
    NEW.engagement_score := LEAST(100, (messages_per_day * 10) + purchase_bonus + 
        CASE WHEN NEW.last_active_at > NOW() - INTERVAL '7 days' THEN 10 ELSE 0 END);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_engagement
    BEFORE INSERT OR UPDATE ON user_journeys
    FOR EACH ROW EXECUTE FUNCTION calculate_engagement_score();

-- Trigger: Détecter risque de churn
CREATE OR REPLACE FUNCTION detect_churn_risk()
RETURNS TRIGGER AS $$
DECLARE
    threshold_days INTEGER;
BEGIN
    -- Récupérer le seuil depuis la config
    SELECT churn_threshold_days INTO threshold_days FROM openclaw_config LIMIT 1;
    IF threshold_days IS NULL THEN threshold_days := 7; END IF;
    
    -- Marquer comme churn risk si inactif
    IF NEW.last_active_at < NOW() - (threshold_days || ' days')::INTERVAL THEN
        NEW.churn_risk := TRUE;
    ELSE
        NEW.churn_risk := FALSE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_detect_churn_risk
    BEFORE UPDATE ON user_journeys
    FOR EACH ROW EXECUTE FUNCTION detect_churn_risk();

-- Trigger: Marquer promotion comme utilisée
CREATE OR REPLACE FUNCTION mark_promotion_used()
RETURNS TRIGGER AS $$
BEGIN
    NEW.used_count := NEW.used_count + 1;
    NEW.used_at := NOW();
    
    -- Si max uses atteint, supprimer (ou marquer comme expirée)
    IF NEW.used_count >= NEW.max_uses THEN
        NEW.valid_until := NOW(); -- Expire immédiatement
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- 📊 Views
-- ===========================================

-- Vue: Dashboard OpenClaw
CREATE VIEW openclaw_dashboard AS
SELECT 
    bm.id,
    bm.mrr,
    bm.arpu,
    bm.conversion_rate * 100 as conversion_percent,
    bm.churn_rate * 100 as churn_percent,
    bm.active_users,
    bm.paying_users,
    bm.recorded_at,
    -- Tendances
    bm.mrr - LAG(bm.mrr) OVER (ORDER BY bm.recorded_at) as mrr_change,
    bm.conversion_rate - LAG(bm.conversion_rate) OVER (ORDER BY bm.recorded_at) as conversion_change
FROM business_metrics bm
ORDER BY bm.recorded_at DESC;

-- Vue: Utilisateurs à risque
CREATE VIEW churn_risk_users AS
SELECT 
    uj.*,
    u.username,
    s.plan as current_plan,
    s.monthly_value
FROM user_journeys uj
JOIN users u ON uj.user_id = u.user_id
LEFT JOIN user_subscriptions s ON uj.user_id = s.user_id AND s.status = 'active'
WHERE uj.churn_risk = TRUE
ORDER BY uj.engagement_score DESC;

-- Vue: Promotions performantes
CREATE VIEW top_performing_promotions AS
SELECT 
    p.type,
    AVG(p.discount_percent) as avg_discount,
    COUNT(*) as total_sent,
    COUNT(CASE WHEN ps.converted_to_paid THEN 1 END) as conversions,
    SUM(ps.revenue_generated) as total_revenue,
    (COUNT(CASE WHEN ps.converted_to_paid THEN 1 END)::DECIMAL / COUNT(*)) * 100 as conversion_rate
FROM user_promotions p
LEFT JOIN promotion_stats ps ON p.id = ps.promotion_id
WHERE p.created_at > NOW() - INTERVAL '30 days'
GROUP BY p.type
ORDER BY conversion_rate DESC;

-- ===========================================
-- 🔧 Functions RPC
-- ===========================================

-- Fonction: Stats business du jour
CREATE OR REPLACE FUNCTION get_today_business_stats()
RETURNS TABLE (
    mrr DECIMAL,
    new_users INTEGER,
    conversions INTEGER,
    churned INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COALESCE(SUM(monthly_value), 0) FROM user_subscriptions WHERE status = 'active'),
        (SELECT COUNT(*)::INTEGER FROM users WHERE created_at > CURRENT_DATE),
        (SELECT COUNT(*)::INTEGER FROM user_subscriptions WHERE status = 'active' AND started_at > CURRENT_DATE),
        (SELECT COUNT(*)::INTEGER FROM user_subscriptions WHERE status = 'cancelled' AND cancelled_at > CURRENT_DATE);
END;
$$ LANGUAGE plpgsql;

-- Fonction: ROI moyen des giveaways
CREATE OR REPLACE FUNCTION get_average_giveaway_roi(days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    total_giveaways BIGINT,
    avg_roi DECIMAL,
    total_cost DECIMAL,
    total_revenue DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        AVG(roi_ratio)::DECIMAL(5,2),
        SUM(cost)::DECIMAL(10,2),
        SUM(revenue_generated)::DECIMAL(10,2)
    FROM giveaway_roi_analysis
    WHERE recorded_at > NOW() - (days_back || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Prédiction MRR
CREATE OR REPLACE FUNCTION predict_mrr_growth()
RETURNS TABLE (
    predicted_mrr DECIMAL,
    growth_rate DECIMAL,
    confidence DECIMAL
) AS $$
DECLARE
    current_mrr DECIMAL;
    avg_growth DECIMAL;
BEGIN
    -- MRR actuel
    SELECT COALESCE(SUM(monthly_value), 0) INTO current_mrr 
    FROM user_subscriptions WHERE status = 'active';
    
    -- Croissance moyenne sur 7 jours
    SELECT AVG(mrr_change) INTO avg_growth
    FROM (
        SELECT mrr - LAG(mrr) OVER (ORDER BY recorded_at) as mrr_change
        FROM business_metrics
        WHERE recorded_at > NOW() - INTERVAL '7 days'
        ORDER BY recorded_at DESC
        LIMIT 7
    ) growth;
    
    -- Prédiction (croissance * 30 jours)
    predicted_mrr := current_mrr + (COALESCE(avg_growth, 0) * 30);
    growth_rate := CASE WHEN current_mrr > 0 
        THEN ((predicted_mrr - current_mrr) / current_mrr) * 100 
        ELSE 0 END;
    confidence := 0.75; -- Simplifié
    
    RETURN QUERY SELECT predicted_mrr, growth_rate::DECIMAL(5,2), confidence::DECIMAL(3,2);
END;
$$ LANGUAGE plpgsql;
