-- =============================================================================
-- Enerji Verimliliği ve Sürdürülebilirlik Platformu
-- Database Schema - PostgreSQL 15+
-- =============================================================================
-- Modüller: User Management | Facility & Energy Sources | Energy Consumption
--           Carbon Footprint (Scope 1-2-3) | Alerts | AI Action Engine
-- =============================================================================
--
-- VERİ AKIŞI (Optimize Edilmiş Yapı):
--
--   users (1)
--      │
--      └──▶ facilities (N)
--              │
--              ├──▶ energy_consumption (N) ── (Tüketim verisi girişi)
--              │       ├──▶ carbon_footprint_items (1) ◀── energy_sources (Ref)
--              │       │       │      (Her tüketim → anlık karbon hesabı)
--              │       │       └──────▶ carbon_footprints (1) (AGGREGASYON)
--              │       │                  (items'dan periyodik toplanır)
--              │       │
--              │       └──▶ alerts (N) ── (Tetikleyen tüketim kaydına bağlı)
--              │
--              └──▶ actions (N) ── (AI tasarruf önerileri, tesise bağlı)
--
-- =============================================================================

--# ---------------------------------------------------------------------------
--# ENUM TYPES
--# ---------------------------------------------------------------------------

CREATE TYPE user_type_enum AS ENUM ('individual', 'business');
CREATE TYPE user_role_enum AS ENUM ('admin', 'viewer', 'operator');

CREATE TYPE energy_category_enum AS ENUM (
    'electricity',       -- Elektrik (şebeke)
    'natural_gas',       -- Doğalgaz
    'fuel_oil',          -- Fuel oil / akaryakıt
    'coal',              -- Kömür
    'lpg',               -- LPG
    'diesel',            -- Dizel (araç filosu)
    'gasoline',          -- Benzin
    'biomass',           -- Biyokütle
    'solar',             -- Güneş enerjisi
    'wind',              -- Rüzgar enerjisi
    'geothermal'         -- Jeotermal
);

CREATE TYPE consumption_source_enum AS ENUM (
    'manual',            -- Elle girilen veri
    'iot_sensor',        -- IoT sensör / akıllı sayaç
    'api_integration',   -- 3. parti API (örn. EPİAŞ, TEDAŞ)
    'bulk_import'        -- Toplu veri yükleme (CSV/Excel)
);

CREATE TYPE carbon_scope_enum AS ENUM ('scope_1', 'scope_2', 'scope_3');

CREATE TYPE carbon_status_enum AS ENUM ('draft', 'confirmed', 'audited');

CREATE TYPE alert_severity_enum AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE alert_status_enum AS ENUM ('new', 'acknowledged', 'resolved', 'dismissed');
CREATE TYPE alert_category_enum AS ENUM (
    'anomaly',            -- Anomali tespiti
    'threshold_breach',   -- Eşik ihlali
    'efficiency_gap',     -- Verimlilik açığı
    'maintenance'         -- Bakım uyarısı
);

CREATE TYPE action_priority_enum AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE action_status_enum AS ENUM (
    'pending',           -- Değerlendirilmeyi bekliyor
    'approved',          -- Onaylandı
    'in_progress',       -- Uygulanıyor
    'implemented',       -- Uygulandı
    'rejected'           -- Reddedildi
);
CREATE TYPE action_category_enum AS ENUM (
    'equipment_upgrade',        -- Ekipman yenileme
    'behavioral',               -- Davranışsal değişiklik
    'maintenance',              -- Bakım iyileştirmesi
    'process_optimization',     -- Süreç optimizasyonu
    'renewable_energy',         -- Yenilenebilir enerji geçişi
    'insulation_hvac'           -- Yalıtım / HVAC
);


--# ---------------------------------------------------------------------------
--# TABLES
--# ---------------------------------------------------------------------------

-- 1. KULLANICILAR (Users)
--    Bireysel ve kurumsal kullanıcıları tek tabloda tutuyoruz.
--    Kurumsal kullanıcılar için company_name ve tax_id alanları devreye girer.
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(150) NOT NULL,
    phone               VARCHAR(20),
    avatar_url          TEXT,

    -- Kurumsal alanlar
    company_name        VARCHAR(255),
    tax_id              VARCHAR(50),
    sector              VARCHAR(100),           -- Sanayi, ticaret, konut, kamu...
    country             VARCHAR(100) DEFAULT 'Türkiye',
    city                VARCHAR(100),
    district            VARCHAR(100),

    user_type           user_type_enum NOT NULL DEFAULT 'individual',
    role                user_role_enum NOT NULL DEFAULT 'viewer',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified_at   TIMESTAMPTZ,
    last_login_at       TIMESTAMPTZ,

    -- Audit fields
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_email UNIQUE (email)
);

-- 2. KULLANICI HESAP AYARLARI (User Preferences)
--    Bildirim tercihleri, dil, zaman dilimi gibi ayarlar.
CREATE TABLE user_preferences (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language            VARCHAR(10) DEFAULT 'tr',
    timezone            VARCHAR(50) DEFAULT 'Europe/Istanbul',
    energy_unit         VARCHAR(20) DEFAULT 'kWh',    -- kWh, MWh, GJ
    currency            VARCHAR(10) DEFAULT 'TRY',
    daily_digest        BOOLEAN DEFAULT FALSE,

    -- Bildirim kanalı tercihleri
    email_alerts        BOOLEAN DEFAULT TRUE,
    push_alerts         BOOLEAN DEFAULT FALSE,
    alert_categories    JSONB DEFAULT '["anomaly","threshold_breach"]'::JSONB,

    -- Haftalık rapor / hedef
    weekly_report       BOOLEAN DEFAULT TRUE,
    monthly_goal_co2    DECIMAL(12,2),               -- Aylık CO2 hedefi (kg)

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_prefs UNIQUE (user_id)
);

-- 3. TESİSLER (Facilities)
--    Kullanıcının birden çok tesisi olabilir (fabrika, ofis, depo, ev...).
CREATE TABLE facilities (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    facility_type       VARCHAR(50) DEFAULT 'office',  -- office, factory, warehouse, retail, home, other

    address             TEXT,
    city                VARCHAR(100),
    district            VARCHAR(100),
    postal_code         VARCHAR(20),
    country             VARCHAR(100) DEFAULT 'Türkiye',

    -- Fiziksel özellikler
    area_sqm            DECIMAL(12,2),               -- Toplam alan (m²)
    heated_area_sqm     DECIMAL(12,2),               -- Isıtılan alan
    num_floors          INTEGER,
    num_occupants       INTEGER,                     -- Tahmini kişi sayısı
    operating_hours     DECIMAL(4,2),                -- Günlük çalışma saati

    -- Koordinatlar
    latitude            DECIMAL(10,7),
    longitude           DECIMAL(10,7),

    -- Durum
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    logo_url            TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_facilities_user_id ON facilities(user_id);

-- 4. ENERJİ KAYNAKLARI (Energy Sources)
--    Referans tablosu: her enerji kaynağının birim CO2 emisyon faktörünü tutar.
--    GHG Protocol / IPCC / EPA verilerine göre doldurulur.
CREATE TABLE energy_sources (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(150) NOT NULL,
    name_tr             VARCHAR(150),               -- Türkçe görünen ad
    category            energy_category_enum NOT NULL,
    unit                VARCHAR(20) NOT NULL,        -- kWh, m³, kg, litre

    -- Karbon emisyon faktörleri (kg CO2e / birim)
    -- Scope 1: Doğrudan emisyonlar (yakıt yakma, araç filosu)
    co2_factor_scope_1  DECIMAL(12,6),              -- kg CO2e / unit
    -- Scope 2: Dolaylı emisyonlar (satın alınan elektrik, buhar)
    co2_factor_scope_2  DECIMAL(12,6),              -- kg CO2e / kWh (şebeke faktörü)
    co2_factor_source   VARCHAR(255),               -- Kaynak referansı (IPCC, EPA, TÜİK...)
    factor_year         INTEGER,                    -- Faktörün geçerli olduğu yıl

    is_renewable        BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_energy_source_name UNIQUE (name)
);

-- 5. ENERJİ TÜKETİM KAYITLARI (Energy Consumption) ⭐ Ana Zaman-Serisi
CREATE TABLE energy_consumption (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id         UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    energy_source_id    UUID NOT NULL REFERENCES energy_sources(id) ON DELETE RESTRICT,

    -- Zaman bilgisi
    recorded_at         TIMESTAMPTZ NOT NULL,        -- Okuma zamanı (dakika hassasiyeti)
    period_start        TIMESTAMPTZ,                 -- Periyot başlangıcı (opsiyonel)
    period_end          TIMESTAMPTZ,                 -- Periyot bitişi (opsiyonel)

    -- Tüketim verisi
    consumption_value   DECIMAL(14,4) NOT NULL,      -- Tüketim miktarı
    unit                VARCHAR(20) NOT NULL,        -- kWh, m³, kg, litre
    cost                DECIMAL(12,4),               -- Tahmini maliyet (opsiyonel)

    -- Metadata
    source              consumption_source_enum NOT NULL DEFAULT 'manual',
    is_estimated        BOOLEAN DEFAULT FALSE,       -- Tahmini veri mi?
    notes               TEXT,
    external_id         VARCHAR(255),                -- API/Sensör referans ID'si

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Zaman serisi sorgulamaları için kompozit index (en kritik index)
CREATE INDEX idx_consumption_facility_time
    ON energy_consumption(facility_id, recorded_at DESC);

CREATE INDEX idx_consumption_recorded_at
    ON energy_consumption(recorded_at DESC);

CREATE INDEX idx_consumption_source
    ON energy_consumption(energy_source_id);

-- 6. KARBON AYAK İZİ KALEMLERİ (Carbon Footprint Items) ⭐ Yeni Yapı
--    HER BİR enerji tüketim kaydının karbon karşılığını hesaplar.
--    energy_consumption oluştuğunda (trigger/arkaplan işlemiyle) bu tabloya
--    karbon hesaplaması yazılır. 1 tüketim → en fazla 1 karbon kalemi.
--    Böylece hangi tüketim anının ne kadar CO2 ürettiği birebir izlenebilir.
CREATE TABLE carbon_footprint_items (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    energy_consumption_id   UUID NOT NULL
                            REFERENCES energy_consumption(id) ON DELETE CASCADE,
    energy_source_id        UUID NOT NULL REFERENCES energy_sources(id) ON DELETE RESTRICT,
    scope                   carbon_scope_enum NOT NULL,

    consumption_amount      DECIMAL(14,4) NOT NULL,
    consumption_unit        VARCHAR(20) NOT NULL,
    co2_factor_used         DECIMAL(12,6) NOT NULL,
    calculated_co2_kg       DECIMAL(14,4) NOT NULL,
    factor_source           VARCHAR(255),

    calculated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Her tüketim kaydının en fazla BİR karbon kalemi olabilir
    CONSTRAINT uq_cfi_consumption UNIQUE (energy_consumption_id),
    CONSTRAINT chk_non_negative_co2 CHECK (calculated_co2_kg >= 0)
);

CREATE INDEX idx_cfi_energy_consumption ON carbon_footprint_items(energy_consumption_id);
CREATE INDEX idx_cfi_energy_source ON carbon_footprint_items(energy_source_id);


-- 7. KARBON AYAK İZİ ÖZETLERİ (Carbon Footprints) — AGGREGASYON TABLOSU
--    carbon_footprint_items + energy_consumption verilerinden periyodik
--    olarak (aylık/yıllık) aggrege edilir. Bir "materialized view"
--    mantığıyla çalışır:
--      - Items: her tüketim anında hesaplanan ham karbon verisi
--      - Footprints: belirli dönemlerin özet raporu (items'dan türetilir)
--    Bu sayede hem gerçek zamanlı (items üzerinden) hem periyodik
--    (footprints üzerinden) sorgulama yapılabilir.
CREATE TABLE carbon_footprints (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id         UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,

    calculation_start   DATE NOT NULL,
    calculation_end     DATE NOT NULL,
    calculation_year    INTEGER NOT NULL,
    calculation_month   INTEGER,
    calculation_quarter INTEGER,

    total_co2_kg        DECIMAL(14,2) NOT NULL,
    scope_1_co2_kg      DECIMAL(14,2),
    scope_2_co2_kg      DECIMAL(14,2),
    scope_3_co2_kg      DECIMAL(14,2),

    intensity_per_area  DECIMAL(10,4),
    intensity_per_revenue DECIMAL(10,4),

    methodology         VARCHAR(50) DEFAULT 'ghg_protocol',
    status              carbon_status_enum NOT NULL DEFAULT 'draft',

    notes               TEXT,
    calculated_by_user  UUID REFERENCES users(id) ON DELETE SET NULL,
    calculated_at       TIMESTAMPTZ DEFAULT NOW(),
    confirmed_at        TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_footprint_dates CHECK (calculation_end > calculation_start),
    CONSTRAINT uq_footprint_period UNIQUE (facility_id, calculation_start, calculation_end, calculation_year)
);

CREATE INDEX idx_cf_facility_date ON carbon_footprints(facility_id, calculation_start DESC);
CREATE INDEX idx_cf_year ON carbon_footprints(calculation_year);


-- 8. UYARILAR (Alerts)
--    Anomali tespiti, eşik ihlalleri, verimlilik uyarıları.
--    İsteğe bağlı olarak belirli bir tüketim kaydına bağlanabilir.
CREATE TABLE alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id         UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    energy_consumption_id UUID               -- Hangi tüketim kaydı tetikledi?
                        REFERENCES energy_consumption(id) ON DELETE SET NULL,
    energy_source_id    UUID REFERENCES energy_sources(id) ON DELETE SET NULL,

    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    severity            alert_severity_enum NOT NULL DEFAULT 'medium',
    category            alert_category_enum NOT NULL,
    status              alert_status_enum NOT NULL DEFAULT 'new',

    detected_value      DECIMAL(14,4),
    expected_value      DECIMAL(14,4),
    threshold_value     DECIMAL(14,4),
    deviation_percent   DECIMAL(6,2),
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    recommendation_text TEXT,
    resolved_at         TIMESTAMPTZ,
    resolved_by         UUID REFERENCES users(id) ON DELETE SET NULL,

    parent_alert_id     UUID REFERENCES alerts(id) ON DELETE SET NULL,
    is_auto_generated   BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_facility_status ON alerts(facility_id, status);
CREATE INDEX idx_alerts_severity ON alerts(severity) WHERE status = 'new';
CREATE INDEX idx_alerts_category_time ON alerts(facility_id, category, detected_at DESC);
CREATE INDEX idx_alerts_detected_at ON alerts(detected_at DESC);


-- 9. AKSİYON MOTORU ÖNERİLERİ (Actions)
--    AI destekli tasarruf önerileri, tesise bağlı.
CREATE TABLE actions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id         UUID NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,

    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    category            action_category_enum NOT NULL,
    priority            action_priority_enum NOT NULL DEFAULT 'medium',
    status              action_status_enum NOT NULL DEFAULT 'pending',

    -- Finansal / çevresel etki
    estimated_saving_co2_kg     DECIMAL(12,2),       -- Tahmini CO2 tasarrufu (yıllık)
    estimated_saving_cost       DECIMAL(12,2),       -- Tahmini maliyet tasarrufu (yıllık)
    estimated_investment_cost   DECIMAL(12,2),       -- Tahmini yatırım maliyeti
    roi_estimate                DECIMAL(6,2),        -- Geri dönüş süresi (yıl)
    payback_months              INTEGER,             -- Geri ödeme süresi (ay)

    -- AI / kaynak bilgisi
    is_ai_generated     BOOLEAN DEFAULT TRUE,
    ai_confidence_score DECIMAL(4,2),                -- 0.00 - 1.00
    source_data_summary TEXT,                         -- AI'nin hangi veriye dayandığı

    -- Uygulama takibi
    assigned_to         UUID REFERENCES users(id) ON DELETE SET NULL,
    implementation_notes TEXT,
    implementation_date DATE,
    implemented_by      UUID REFERENCES users(id) ON DELETE SET NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_actions_facility_status ON actions(facility_id, status);
CREATE INDEX idx_actions_priority ON actions(facility_id, priority) WHERE status = 'pending';
