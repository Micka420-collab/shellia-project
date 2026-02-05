-- ============================================
-- SHELLIA AI BOT - SUPABASE SCHEMA
-- ============================================

-- Activer RLS (Row Level Security)
ALTER DATABASE postgres SET "app.settings.jwt_secret" TO 'your-jwt-secret';

-- ============================================
-- 1. TABLE: users
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    discriminator VARCHAR(10),
    avatar_url TEXT,
    
    -- Plan
    plan VARCHAR(20) DEFAULT 'free' NOT NULL,
    plan_started_at TIMESTAMP WITH TIME ZONE,
    plan_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Stats
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0,
    
    -- Sécurité
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    ban_expires_at TIMESTAMP WITH TIME ZONE,
    warnings INTEGER DEFAULT 0,
    
    -- Timestamps
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_plan ON users(plan);
CREATE INDEX idx_users_banned ON users(is_banned);

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 2. TABLE: daily_quotas
-- ============================================
CREATE TABLE IF NOT EXISTS daily_quotas (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    messages_used INTEGER DEFAULT 0,
    messages_limit INTEGER DEFAULT 10,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    streak_bonus INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, date)
);

CREATE INDEX idx_quotas_user_date ON daily_quotas(user_id, date);
CREATE INDEX idx_quotas_date ON daily_quotas(date);

-- ============================================
-- 3. TABLE: user_streaks
-- ============================================
CREATE TABLE IF NOT EXISTS user_streaks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_active_date DATE,
    total_days_active INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_streaks_updated_at 
    BEFORE UPDATE ON user_streaks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. TABLE: streak_history
-- ============================================
CREATE TABLE IF NOT EXISTS streak_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    streak_count INTEGER NOT NULL,
    bonus_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_streak_history_user ON streak_history(user_id);
CREATE INDEX idx_streak_history_date ON streak_history(date);

-- ============================================
-- 5. TABLE: user_badges
-- ============================================
CREATE TABLE IF NOT EXISTS user_badges (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    badge_id VARCHAR(50) NOT NULL,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, badge_id)
);

CREATE INDEX idx_badges_user ON user_badges(user_id);

-- ============================================
-- 6. TABLE: referral_codes
-- ============================================
CREATE TABLE IF NOT EXISTS referral_codes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_uses INTEGER DEFAULT 0
);

CREATE INDEX idx_referral_codes_code ON referral_codes(code);

-- ============================================
-- 7. TABLE: referrals
-- ============================================
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_id BIGINT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    code_used VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, cancelled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX idx_referrals_referred ON referrals(referred_id);

-- ============================================
-- 8. TABLE: referral_rewards
-- ============================================
CREATE TABLE IF NOT EXISTS referral_rewards (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    reward_type VARCHAR(50) NOT NULL, -- pro_days, messages, etc.
    reward_value INTEGER NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_referral_rewards_user ON referral_rewards(user_id);
CREATE INDEX idx_referral_rewards_expires ON referral_rewards(expires_at);

-- ============================================
-- 9. TABLE: user_trials
-- ============================================
CREATE TABLE IF NOT EXISTS user_trials (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    trial_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trial_ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    messages_used INTEGER DEFAULT 0,
    converted_to_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 10. TABLE: user_violations
-- ============================================
CREATE TABLE IF NOT EXISTS user_violations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL, -- spam, abuse, etc.
    description TEXT,
    action_taken VARCHAR(50), -- warning, mute, ban, etc.
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_violations_user ON user_violations(user_id);
CREATE INDEX idx_violations_timestamp ON user_violations(timestamp);

-- ============================================
-- 11. TABLE: security_logs
-- ============================================
CREATE TABLE IF NOT EXISTS security_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_security_logs_user ON security_logs(user_id);
CREATE INDEX idx_security_logs_type ON security_logs(event_type);
CREATE INDEX idx_security_logs_timestamp ON security_logs(timestamp);

-- ============================================
-- 12. TABLE: message_history
-- ============================================
CREATE TABLE IF NOT EXISTS message_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,
    message_content TEXT,
    ai_response TEXT,
    model_used VARCHAR(50),
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_message_history_user ON message_history(user_id);
CREATE INDEX idx_message_history_created ON message_history(created_at);

-- ============================================
-- 13. TABLE: payments
-- ============================================
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    stripe_payment_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    plan VARCHAR(20) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed, refunded
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_stripe ON payments(stripe_payment_id);

-- ============================================
-- FONCTIONS RPC
-- ============================================

-- Fonction: incrémenter le quota
CREATE OR REPLACE FUNCTION increment_quota(
    p_user_id BIGINT,
    p_date DATE,
    p_tokens INTEGER,
    p_cost DECIMAL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_quotas (user_id, date, messages_used, tokens_used, cost_usd)
    VALUES (p_user_id, p_date, 1, p_tokens, p_cost)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        messages_used = daily_quotas.messages_used + 1,
        tokens_used = daily_quotas.tokens_used + p_tokens,
        cost_usd = daily_quotas.cost_usd + p_cost,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Fonction: incrémenter les stats utilisateur
CREATE OR REPLACE FUNCTION increment_user_stats(
    p_user_id BIGINT,
    p_tokens INTEGER,
    p_cost DECIMAL
) RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET total_messages = total_messages + 1,
        total_tokens = total_tokens + p_tokens,
        total_cost_usd = total_cost_usd + p_cost,
        last_active_at = NOW()
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Fonction: ajouter bonus de streak
CREATE OR REPLACE FUNCTION add_streak_bonus(
    p_user_id BIGINT,
    p_date DATE,
    p_bonus INTEGER
) RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_quotas (user_id, date, streak_bonus)
    VALUES (p_user_id, p_date, p_bonus)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        streak_bonus = daily_quotas.streak_bonus + p_bonus,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Fonction: incrémenter warnings
CREATE OR REPLACE FUNCTION increment_warnings(
    p_user_id BIGINT
) RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET warnings = warnings + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Fonction: leaderboard
CREATE OR REPLACE FUNCTION get_leaderboard(
    period TEXT,
    limit_count INTEGER DEFAULT 10
) RETURNS TABLE (
    rank BIGINT,
    user_id BIGINT,
    username TEXT,
    messages BIGINT
) AS $$
DECLARE
    start_date DATE;
BEGIN
    IF period = 'day' THEN
        start_date := CURRENT_DATE;
    ELSIF period = 'week' THEN
        start_date := CURRENT_DATE - INTERVAL '7 days';
    ELSIF period = 'month' THEN
        start_date := CURRENT_DATE - INTERVAL '30 days';
    ELSE
        start_date := '2000-01-01'::DATE;
    END IF;

    RETURN QUERY
    SELECT 
        ROW_NUMBER() OVER (ORDER BY SUM(dq.messages_used) DESC)::BIGINT as rank,
        u.user_id,
        u.username::TEXT,
        SUM(dq.messages_used)::BIGINT as messages
    FROM users u
    JOIN daily_quotas dq ON u.user_id = dq.user_id
    WHERE dq.date >= start_date
    GROUP BY u.user_id, u.username
    ORDER BY messages DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- POLITIQUES RLS (Row Level Security)
-- ============================================

-- Activer RLS sur toutes les tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_streaks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_trials ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Politique: service_role peut tout faire (pour le bot)
CREATE POLICY service_all ON users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON daily_quotas FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON user_streaks FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON user_badges FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON referral_codes FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON referrals FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON referral_rewards FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON user_trials FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON user_violations FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON security_logs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON message_history FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY service_all ON payments FOR ALL TO service_role USING (true) WITH CHECK (true);
