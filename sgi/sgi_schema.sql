-- Inscenium Scene Graph Intelligence Database Schema
-- =================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis" CASCADE;

-- Titles table (video content)
CREATE TABLE IF NOT EXISTS titles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    duration_seconds REAL NOT NULL,
    resolution VARCHAR(20), -- e.g., "1920x1080"
    fps REAL,
    file_path TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shots table (shot boundaries within titles)
CREATE TABLE IF NOT EXISTS shots (
    id SERIAL PRIMARY KEY,
    title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
    shot_id VARCHAR(50) NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL DEFAULT 1.0,
    content_analysis JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(title_id, shot_id)
);

-- Surfaces table (placement opportunities within shots)
CREATE TABLE IF NOT EXISTS surfaces (
    id SERIAL PRIMARY KEY,
    surface_id VARCHAR(100) NOT NULL UNIQUE,
    title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
    shot_id INTEGER NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
    
    -- Temporal bounds
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    
    -- Spatial geometry (PostGIS)
    geometry GEOMETRY(POLYGON, 4326),
    bounds_3d JSONB, -- 3D bounding box as JSON
    
    -- Surface properties
    surface_type VARCHAR(50), -- "wall", "table", "screen", etc.
    area_pixels REAL,
    area_world_m2 REAL,
    normal_vector JSONB, -- Surface normal as [x, y, z]
    
    -- Quality metrics
    prs_score REAL DEFAULT 0,
    visibility_score REAL DEFAULT 0,
    stability_score REAL DEFAULT 0,
    
    -- Uncertainty metrics
    occlusion_probability REAL DEFAULT 0,
    depth_confidence REAL DEFAULT 0,
    tracking_stability REAL DEFAULT 0,
    geometric_consistency REAL DEFAULT 0,
    
    -- Metadata and restrictions
    restrictions JSONB DEFAULT '[]',
    capabilities JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Surface tracking across shots (for identity persistence)
CREATE TABLE IF NOT EXISTS surface_tracks (
    id SERIAL PRIMARY KEY,
    track_id UUID DEFAULT uuid_generate_v4(),
    title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
    
    -- Surfaces belonging to this track
    surface_ids INTEGER[] DEFAULT '{}',
    
    -- Track properties
    first_appearance_time REAL NOT NULL,
    last_appearance_time REAL NOT NULL,
    total_duration REAL DEFAULT 0,
    
    -- Aggregated metrics
    avg_prs_score REAL DEFAULT 0,
    max_prs_score REAL DEFAULT 0,
    total_area_time REAL DEFAULT 0, -- Area × time product
    
    -- Track metadata
    surface_type VARCHAR(50),
    is_stable BOOLEAN DEFAULT false,
    track_confidence REAL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rights and restrictions ledger
CREATE TABLE IF NOT EXISTS rights_ledger (
    id SERIAL PRIMARY KEY,
    surface_id VARCHAR(100) NOT NULL REFERENCES surfaces(surface_id) ON DELETE CASCADE,
    
    -- Rights information
    rights_holder VARCHAR(255),
    license_type VARCHAR(100), -- "exclusive", "non-exclusive", "royalty-free"
    usage_restrictions JSONB DEFAULT '{}',
    geographic_restrictions VARCHAR[] DEFAULT '{}',
    content_restrictions VARCHAR[] DEFAULT '{}',
    
    -- Temporal validity
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    
    -- Legal compliance
    requires_disclosure BOOLEAN DEFAULT true,
    disclosure_text TEXT,
    compliance_jurisdiction VARCHAR(10) DEFAULT 'US', -- ISO country code
    
    -- Audit trail
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approval_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Placement bookings
CREATE TABLE IF NOT EXISTS placement_bookings (
    id SERIAL PRIMARY KEY,
    booking_id VARCHAR(100) NOT NULL UNIQUE,
    surface_id VARCHAR(100) NOT NULL REFERENCES surfaces(surface_id) ON DELETE CASCADE,
    
    -- Booking details
    advertiser_id VARCHAR(100) NOT NULL,
    campaign_id VARCHAR(100) NOT NULL,
    creative_asset_id VARCHAR(100),
    
    -- Financial terms
    bid_amount_cpm DECIMAL(10, 2) NOT NULL,
    final_cpm_rate DECIMAL(10, 2),
    estimated_impressions INTEGER DEFAULT 0,
    actual_impressions INTEGER DEFAULT 0,
    
    -- Booking lifecycle
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, active, completed, cancelled
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmation_time TIMESTAMP,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    
    -- Creative requirements
    min_prs_score REAL DEFAULT 70.0,
    min_visibility_duration REAL DEFAULT 2.0,
    require_perspective_correction BOOLEAN DEFAULT false,
    require_lighting_adaptation BOOLEAN DEFAULT false,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exposure events (for measurement)
CREATE TABLE IF NOT EXISTS exposure_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL UNIQUE,
    booking_id VARCHAR(100) NOT NULL REFERENCES placement_bookings(booking_id) ON DELETE CASCADE,
    
    -- Viewer information (anonymized)
    viewer_id VARCHAR(100) NOT NULL, -- Anonymous hash
    session_id VARCHAR(100),
    
    -- Temporal information
    event_timestamp TIMESTAMP NOT NULL,
    exposure_duration REAL NOT NULL, -- seconds
    content_position REAL, -- position within video
    
    -- Viewing context
    viewing_angle_azimuth REAL,
    viewing_angle_elevation REAL,
    viewing_distance_meters REAL,
    screen_coverage_percentage REAL,
    attention_score REAL, -- 0-1 from eye tracking
    
    -- Quality at exposure time
    instantaneous_prs REAL,
    occlusion_level REAL,
    lighting_quality REAL,
    
    -- Device and environment
    device_type VARCHAR(50), -- mobile, desktop, tv, etc.
    player_version VARCHAR(50),
    viewport_size VARCHAR(20), -- WxH
    connection_type VARCHAR(20), -- wifi, cellular, etc.
    
    -- Privacy and compliance
    consent_given BOOLEAN DEFAULT false,
    jurisdiction VARCHAR(10) DEFAULT 'US',
    privacy_flags JSONB DEFAULT '{}',
    
    -- Geospatial (optional, privacy-respecting)
    country_code VARCHAR(2),
    region_code VARCHAR(10),
    timezone VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_shots_title_id ON shots(title_id);
CREATE INDEX IF NOT EXISTS idx_shots_time_range ON shots(title_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_surfaces_shot_id ON surfaces(shot_id);
CREATE INDEX IF NOT EXISTS idx_surfaces_prs_score ON surfaces(prs_score DESC);
CREATE INDEX IF NOT EXISTS idx_surfaces_time_range ON surfaces(title_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_surfaces_type ON surfaces(surface_type);
CREATE INDEX IF NOT EXISTS idx_surface_tracks_title_id ON surface_tracks(title_id);
CREATE INDEX IF NOT EXISTS idx_surface_tracks_time_range ON surface_tracks(first_appearance_time, last_appearance_time);
CREATE INDEX IF NOT EXISTS idx_rights_ledger_surface_id ON rights_ledger(surface_id);
CREATE INDEX IF NOT EXISTS idx_rights_ledger_validity ON rights_ledger(valid_from, valid_until);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON placement_bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_surface_id ON placement_bookings(surface_id);
CREATE INDEX IF NOT EXISTS idx_bookings_advertiser ON placement_bookings(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_bookings_time_range ON placement_bookings(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_exposure_events_booking_id ON exposure_events(booking_id);
CREATE INDEX IF NOT EXISTS idx_exposure_events_timestamp ON exposure_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_exposure_events_viewer_id ON exposure_events(viewer_id);

-- Spatial index for surface geometry (PostGIS)
CREATE INDEX IF NOT EXISTS idx_surfaces_geometry ON surfaces USING GIST(geometry);

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_titles_updated_at BEFORE UPDATE ON titles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_surfaces_updated_at BEFORE UPDATE ON surfaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_surface_tracks_updated_at BEFORE UPDATE ON surface_tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_rights_ledger_updated_at BEFORE UPDATE ON rights_ledger
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_placement_bookings_updated_at BEFORE UPDATE ON placement_bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW placement_opportunities AS
SELECT 
    s.surface_id,
    s.title_id,
    t.title,
    sh.shot_id,
    s.start_time,
    s.end_time,
    s.end_time - s.start_time as duration,
    s.surface_type,
    s.prs_score,
    s.visibility_score,
    s.area_world_m2,
    s.occlusion_probability,
    s.restrictions,
    s.capabilities,
    CASE 
        WHEN EXISTS(SELECT 1 FROM placement_bookings pb WHERE pb.surface_id = s.surface_id AND pb.status IN ('confirmed', 'active'))
        THEN false 
        ELSE true 
    END as available
FROM surfaces s
JOIN titles t ON s.title_id = t.id
JOIN shots sh ON s.shot_id = sh.id
WHERE s.prs_score > 0;

COMMENT ON TABLE titles IS 'Video content titles and metadata';
COMMENT ON TABLE shots IS 'Shot boundaries within video content';  
COMMENT ON TABLE surfaces IS 'Placement surfaces identified within shots';
COMMENT ON TABLE surface_tracks IS 'Tracks surfaces across multiple shots for identity persistence';
COMMENT ON TABLE rights_ledger IS 'Rights, restrictions and legal compliance for surfaces';
COMMENT ON TABLE placement_bookings IS 'Commercial bookings for surface placements';
COMMENT ON TABLE exposure_events IS 'Individual viewer exposure events for measurement';
COMMENT ON VIEW placement_opportunities IS 'Available placement opportunities with key metrics';