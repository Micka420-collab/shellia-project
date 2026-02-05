-- ===========================================
-- 🎁 Schéma pour le système de Giveaways Automatiques
-- ===========================================

-- Table: Paliers de giveaways configurés
CREATE TABLE giveaway_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    milestone INTEGER NOT NULL,
    reward_config JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guild_id, milestone)
);

-- Index pour recherche rapide
CREATE INDEX idx_giveaway_milestones_guild ON giveaway_milestones(guild_id);
CREATE INDEX idx_giveaway_milestones_count ON giveaway_milestones(milestone);

-- Table: Paliers déjà atteints
CREATE TABLE completed_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    milestone INTEGER NOT NULL,
    giveaway_id UUID,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guild_id, milestone)
);

CREATE INDEX idx_completed_milestones_guild ON completed_milestones(guild_id);

-- Table: Giveaways actifs
CREATE TABLE active_giveaways (
    id VARCHAR(8) PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    milestone INTEGER NOT NULL,
    reward JSONB NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT,
    host_id BIGINT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    entries JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'active',
    winners BIGINT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_active_giveaways_guild ON active_giveaways(guild_id);
CREATE INDEX idx_active_giveaways_status ON active_giveaways(status);
CREATE INDEX idx_active_giveaways_ends ON active_giveaways(ends_at);

-- Table: Giveaways terminés (archive)
CREATE TABLE ended_giveaways (
    id VARCHAR(8) PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    milestone INTEGER NOT NULL,
    reward JSONB NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT,
    host_id BIGINT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    entries JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20),
    winners BIGINT[] DEFAULT '{}',
    ended_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ended_giveaways_guild ON ended_giveaways(guild_id);
CREATE INDEX idx_ended_giveaways_ended ON ended_giveaways(ended_at);

-- Table: Économie virtuelle (pour les récompenses)
CREATE TABLE user_economy (
    user_id BIGINT PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    last_daily TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_economy_balance ON user_economy(balance DESC);

-- Table: Transactions économiques
CREATE TABLE economy_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'giveaway_win', 'daily', 'purchase', etc.
    description TEXT,
    giveaway_id VARCHAR(8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_economy_transactions_user ON economy_transactions(user_id);
CREATE INDEX idx_economy_transactions_type ON economy_transactions(type);
CREATE INDEX idx_economy_transactions_giveaway ON economy_transactions(giveaway_id);

-- Table: Statistiques de giveaways
CREATE TABLE giveaway_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    total_giveaways INTEGER DEFAULT 0,
    total_participants INTEGER DEFAULT 0,
    total_winners INTEGER DEFAULT 0,
    total_currency_given INTEGER DEFAULT 0,
    biggest_giveaway_id VARCHAR(8),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guild_id)
);

-- ===========================================
-- 🔒 RLS Policies
-- ===========================================

-- Enable RLS
ALTER TABLE giveaway_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE completed_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_giveaways ENABLE ROW LEVEL SECURITY;
ALTER TABLE ended_giveaways ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_economy ENABLE ROW LEVEL SECURITY;
ALTER TABLE economy_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE giveaway_stats ENABLE ROW LEVEL SECURITY;

-- Policies: giveaway_milestones
CREATE POLICY "Giveaway milestones are viewable by everyone" 
    ON giveaway_milestones FOR SELECT USING (true);

CREATE POLICY "Only admins can modify milestones" 
    ON giveaway_milestones FOR ALL 
    USING (is_admin_user(auth.uid()));

-- Policies: active_giveaways
CREATE POLICY "Active giveaways are viewable by everyone" 
    ON active_giveaways FOR SELECT USING (true);

CREATE POLICY "Only bot can modify active giveaways" 
    ON active_giveaways FOR ALL 
    USING (is_bot_user(auth.uid()));

-- Policies: user_economy
CREATE POLICY "Users can view own economy" 
    ON user_economy FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Bot can modify economy" 
    ON user_economy FOR ALL 
    USING (is_bot_user(auth.uid()));

-- Policies: economy_transactions
CREATE POLICY "Users can view own transactions" 
    ON economy_transactions FOR SELECT 
    USING (auth.uid() = user_id);

-- ===========================================
-- 🔄 Triggers
-- ===========================================

-- Trigger: Mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_giveaway_milestones_updated_at
    BEFORE UPDATE ON giveaway_milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_economy_updated_at
    BEFORE UPDATE ON user_economy
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Mettre à jour les stats quand un giveaway se termine
CREATE OR REPLACE FUNCTION update_giveaway_stats()
RETURNS TRIGGER AS $$
DECLARE
    participant_count INTEGER;
    winner_count INTEGER;
    currency_amount INTEGER;
BEGIN
    -- Calculer les stats
    participant_count := jsonb_array_length(NEW.entries);
    winner_count := array_length(NEW.winners, 1);
    IF winner_count IS NULL THEN winner_count := 0; END IF;
    
    currency_amount := (NEW.reward->>'currency_reward')::INTEGER * winner_count;
    IF currency_amount IS NULL THEN currency_amount := 0; END IF;
    
    -- Insérer ou mettre à jour les stats
    INSERT INTO giveaway_stats (
        guild_id, 
        total_giveaways, 
        total_participants, 
        total_winners,
        total_currency_given,
        biggest_giveaway_id
    )
    VALUES (
        NEW.guild_id, 
        1, 
        participant_count, 
        winner_count,
        currency_amount,
        NEW.id
    )
    ON CONFLICT (guild_id) DO UPDATE SET
        total_giveaways = giveaway_stats.total_giveaways + 1,
        total_participants = giveaway_stats.total_participants + participant_count,
        total_winners = giveaway_stats.total_winners + winner_count,
        total_currency_given = giveaway_stats.total_currency_given + currency_amount,
        biggest_giveaway_id = CASE 
            WHEN participant_count > (
                SELECT jsonb_array_length(entries) 
                FROM ended_giveaways 
                WHERE id = giveaway_stats.biggest_giveaway_id
            ) THEN NEW.id
            ELSE giveaway_stats.biggest_giveaway_id
        END,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_giveaway_stats
    AFTER INSERT ON ended_giveaways
    FOR EACH ROW EXECUTE FUNCTION update_giveaway_stats();

-- Trigger: Créer une transaction quand un giveaway est gagné
CREATE OR REPLACE FUNCTION create_economy_transaction()
RETURNS TRIGGER AS $$
DECLARE
    winner_id BIGINT;
    currency_reward INTEGER;
BEGIN
    currency_reward := (NEW.reward->>'currency_reward')::INTEGER;
    
    IF currency_reward > 0 THEN
        FOREACH winner_id IN ARRAY NEW.winners
        LOOP
            INSERT INTO economy_transactions (
                user_id,
                amount,
                type,
                description,
                giveaway_id
            )
            VALUES (
                winner_id,
                currency_reward,
                'giveaway_win',
                'Gagné au giveaway du palier ' || NEW.milestone || ' membres',
                NEW.id
            );
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_economy_transaction
    AFTER INSERT ON ended_giveaways
    FOR EACH ROW EXECUTE FUNCTION create_economy_transaction();

-- ===========================================
-- 📊 Views
-- ===========================================

-- Vue: Leaderboard des plus riches
CREATE VIEW economy_leaderboard AS
SELECT 
    user_id,
    balance,
    total_earned,
    RANK() OVER (ORDER BY balance DESC) as rank
FROM user_economy
WHERE balance > 0
ORDER BY balance DESC;

-- Vue: Historique des giveaways d'un serveur
CREATE VIEW guild_giveaway_history AS
SELECT 
    g.*,
    jsonb_array_length(g.entries) as participant_count,
    array_length(g.winners, 1) as winner_count
FROM ended_giveaways g
ORDER BY g.ended_at DESC;

-- ===========================================
-- 🔧 Functions RPC
-- ===========================================

-- Fonction: Récupérer les stats d'un utilisateur
CREATE OR REPLACE FUNCTION get_user_giveaway_stats(user_id BIGINT)
RETURNS TABLE (
    giveaways_won INTEGER,
    total_earned INTEGER,
    participation_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT g.id)::INTEGER as giveaways_won,
        COALESCE(SUM(t.amount), 0)::INTEGER as total_earned,
        (
            SELECT COUNT(*)::INTEGER 
            FROM ended_giveaways 
            WHERE entries @> jsonb_build_array(jsonb_build_object('user_id', user_id))
        ) as participation_count
    FROM ended_giveaways g
    LEFT JOIN economy_transactions t ON t.giveaway_id = g.id AND t.user_id = user_id
    WHERE user_id = ANY(g.winners);
END;
$$ LANGUAGE plpgsql;

-- Fonction: Récupérer les prochains paliers
CREATE OR REPLACE FUNCTION get_upcoming_milestones(guild_id BIGINT, current_count INTEGER)
RETURNS TABLE (
    milestone INTEGER,
    members_needed INTEGER,
    reward_preview TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        gm.milestone,
        gm.milestone - current_count as members_needed,
        gm.reward_config->>'description' as reward_preview
    FROM giveaway_milestones gm
    WHERE gm.guild_id = guild_id
      AND gm.milestone > current_count
    ORDER BY gm.milestone ASC;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Statistiques globales des giveaways
CREATE OR REPLACE FUNCTION get_global_giveaway_stats()
RETURNS TABLE (
    total_giveaways INTEGER,
    total_participants INTEGER,
    total_winners INTEGER,
    total_currency_given INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(total_giveaways), 0)::INTEGER,
        COALESCE(SUM(total_participants), 0)::INTEGER,
        COALESCE(SUM(total_winners), 0)::INTEGER,
        COALESCE(SUM(total_currency_given), 0)::INTEGER
    FROM giveaway_stats;
END;
$$ LANGUAGE plpgsql;
