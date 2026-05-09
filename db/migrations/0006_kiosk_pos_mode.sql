-- 0006_kiosk_pos_mode.sql
-- Adds kiosk POS support with custom items and cash/zelle payments.

BEGIN;

CREATE TABLE IF NOT EXISTS kiosk_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_name TEXT NOT NULL,
    default_price NUMERIC(12,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_custom BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kiosk_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    preferred_payment_method TEXT CHECK (preferred_payment_method IN ('cash', 'zelle')),
    created_from_kiosk BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (normalized_name)
);

CREATE TABLE IF NOT EXISTS kiosk_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_date DATE NOT NULL,
    order_status TEXT NOT NULL DEFAULT 'open' CHECK (order_status IN ('open', 'paid', 'cancelled')),
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS kiosk_order_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kiosk_order_id UUID NOT NULL REFERENCES kiosk_orders(id) ON DELETE CASCADE,
    kiosk_item_id UUID REFERENCES kiosk_items(id),
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    line_total NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
    is_custom_line BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kiosk_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kiosk_order_id UUID NOT NULL UNIQUE REFERENCES kiosk_orders(id) ON DELETE CASCADE,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('cash', 'zelle')),
    amount_paid NUMERIC(12,2) NOT NULL CHECK (amount_paid >= 0),
    cash_received NUMERIC(12,2),
    cash_change NUMERIC(12,2),
    zelle_customer_id UUID REFERENCES kiosk_customers(id),
    zelle_customer_name TEXT,
    transaction_reference TEXT,
    paid_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (payment_method = 'cash' AND cash_received IS NOT NULL) OR
        (payment_method = 'zelle' AND zelle_customer_name IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS kiosk_events (
    id BIGSERIAL PRIMARY KEY,
    kiosk_order_id UUID REFERENCES kiosk_orders(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('order_created', 'line_added', 'line_updated', 'line_removed', 'payment_recorded', 'order_closed', 'customer_created')),
    actor_user_id UUID REFERENCES users(id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kiosk_items_active_name ON kiosk_items(is_active, item_name);
CREATE INDEX IF NOT EXISTS idx_kiosk_orders_date_status ON kiosk_orders(service_date, order_status);
CREATE INDEX IF NOT EXISTS idx_kiosk_order_lines_order ON kiosk_order_lines(kiosk_order_id);
CREATE INDEX IF NOT EXISTS idx_kiosk_payments_method_created ON kiosk_payments(payment_method, created_at);
CREATE INDEX IF NOT EXISTS idx_kiosk_customers_normalized_name ON kiosk_customers(normalized_name);
CREATE INDEX IF NOT EXISTS idx_kiosk_events_order_time ON kiosk_events(kiosk_order_id, created_at);

COMMIT;
