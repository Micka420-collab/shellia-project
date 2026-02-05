-- ===========================================
-- 🛍️ PREORDER SCHEMA - Système de Pré-achat
-- ===========================================

-- Table: Items en pré-achat
CREATE TABLE preorder_items (
    id VARCHAR(8) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL,
    image_url TEXT,
    stock_limit INTEGER,
    preorder_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preorder_end TIMESTAMP WITH TIME ZONE NOT NULL,
    delivery_date TIMESTAMP WITH TIME ZONE NOT NULL,
    benefits JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_preorder_items_status ON preorder_items(status) WHERE status = 'active';
CREATE INDEX idx_preorder_items_end ON preorder_items(preorder_end);

-- Table: Achats en pré-achat
CREATE TABLE preorder_purchases (
    id VARCHAR(8) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id VARCHAR(8) REFERENCES preorder_items(id),
    tier VARCHAR(20) NOT NULL,
    price_paid DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    payment_intent_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_preorder_purchases_user ON preorder_purchases(user_id);
CREATE INDEX idx_preorder_purchases_item ON preorder_purchases(item_id);
CREATE INDEX idx_preorder_purchases_status ON preorder_purchases(status);

-- Table: Stats de pré-achat
CREATE TABLE preorder_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id VARCHAR(8) REFERENCES preorder_items(id),
    tier VARCHAR(20) NOT NULL,
    count INTEGER DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_preorder_stats_item ON preorder_stats(item_id);

-- ===========================================
-- 🔒 RLS Policies
-- ===========================================

ALTER TABLE preorder_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE preorder_purchases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Preorder items are viewable by everyone"
    ON preorder_items FOR SELECT USING (true);

CREATE POLICY "Only admins can modify preorder items"
    ON preorder_items FOR ALL USING (is_admin_user(auth.uid()));

CREATE POLICY "Users can view own purchases"
    ON preorder_purchases FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Bot can manage purchases"
    ON preorder_purchases FOR ALL USING (is_bot_user(auth.uid()));

-- ===========================================
-- 🔄 Functions
-- ===========================================

-- Fonction: Stats par item
CREATE OR REPLACE FUNCTION get_preorder_item_stats(item_id VARCHAR)
RETURNS TABLE (
    tier VARCHAR,
    count BIGINT,
    revenue DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.tier,
        COUNT(*)::BIGINT,
        COALESCE(SUM(p.price_paid), 0)::DECIMAL
    FROM preorder_purchases p
    WHERE p.item_id = item_id
    AND p.status != 'cancelled'
    GROUP BY p.tier;
END;
$$ LANGUAGE plpgsql;
