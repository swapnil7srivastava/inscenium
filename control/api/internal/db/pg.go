package db

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/lib/pq"
)

// DB represents database connection and operations
type DB struct {
	*sql.DB
}

// Connect establishes connection to PostgreSQL database
func Connect() (*DB, error) {
	dsn := os.Getenv("POSTGRES_DSN")
	if dsn == "" {
		dsn = "postgresql://inscenium:inscenium@localhost:5432/inscenium?sslmode=disable"
	}

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	// Test connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &DB{db}, nil
}

// RunMigrations applies database migrations
func (db *DB) RunMigrations() error {
	// Check if schema needs to be applied
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'titles'").Scan(&count)
	if err != nil {
		log.Printf("Warning: Could not check for existing schema: %v", err)
	}

	if count == 0 {
		log.Println("Applying database schema...")
		
		// Read schema file
		schemaPath := os.Getenv("SCHEMA_PATH")
		if schemaPath == "" {
			schemaPath = "sgi/sgi_schema.sql"
		}

		if _, err := os.Stat(schemaPath); os.IsNotExist(err) {
			log.Printf("Schema file not found at %s, skipping migrations", schemaPath)
			return nil
		}

		schemaSQL, err := os.ReadFile(schemaPath)
		if err != nil {
			return fmt.Errorf("failed to read schema file: %w", err)
		}

		if _, err := db.Exec(string(schemaSQL)); err != nil {
			return fmt.Errorf("failed to apply schema: %w", err)
		}

		log.Println("✓ Database schema applied successfully")
	} else {
		log.Println("Database schema already exists, skipping migrations")
	}

	return nil
}

// GetPlacementOpportunities retrieves placement opportunities with filtering
func (db *DB) GetPlacementOpportunities(titleID string, minPRS float64, limit, offset int) ([]map[string]interface{}, error) {
	query := `
		SELECT 
			surface_id,
			title_id,
			shot_id,
			start_time,
			end_time,
			(end_time - start_time) as duration,
			surface_type,
			prs_score,
			visibility_score,
			created_at
		FROM surfaces 
		WHERE ($1 = '' OR title_id = $1) 
			AND prs_score >= $2
		ORDER BY prs_score DESC
		LIMIT $3 OFFSET $4
	`

	rows, err := db.Query(query, titleID, minPRS, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query opportunities: %w", err)
	}
	defer rows.Close()

	var opportunities []map[string]interface{}
	for rows.Next() {
		var surfaceID, titleIDResult, shotID, surfaceType sql.NullString
		var startTime, endTime, duration, prsScore, visibilityScore sql.NullFloat64
		var createdAt sql.NullTime

		err := rows.Scan(&surfaceID, &titleIDResult, &shotID, &startTime, &endTime, &duration, &surfaceType, &prsScore, &visibilityScore, &createdAt)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		opportunity := map[string]interface{}{
			"surface_id":       surfaceID.String,
			"title_id":         titleIDResult.String,
			"shot_id":          shotID.String,
			"start_time":       startTime.Float64,
			"end_time":         endTime.Float64,
			"duration":         duration.Float64,
			"surface_type":     surfaceType.String,
			"prs_score":        prsScore.Float64,
			"visibility_score": visibilityScore.Float64,
			"created_at":       createdAt.Time.Format(time.RFC3339),
		}
		opportunities = append(opportunities, opportunity)
	}

	return opportunities, nil
}

// GetPlacementOpportunity retrieves a single placement opportunity by surface ID
func (db *DB) GetPlacementOpportunity(surfaceID string) (map[string]interface{}, error) {
	query := `
		SELECT 
			surface_id,
			title_id,
			shot_id,
			start_time,
			end_time,
			(end_time - start_time) as duration,
			surface_type,
			prs_score,
			visibility_score,
			area_pixels,
			area_world_m2,
			restrictions,
			created_at
		FROM surfaces 
		WHERE surface_id = $1
	`

	row := db.QueryRow(query, surfaceID)

	var titleID, shotID, surfaceType sql.NullString
	var startTime, endTime, duration, prsScore, visibilityScore, areaPixels, areaWorldM2 sql.NullFloat64
	var restrictions sql.NullString
	var createdAt sql.NullTime

	err := row.Scan(&surfaceID, &titleID, &shotID, &startTime, &endTime, &duration, &surfaceType, &prsScore, &visibilityScore, &areaPixels, &areaWorldM2, &restrictions, &createdAt)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil // Not found
		}
		return nil, fmt.Errorf("failed to scan opportunity: %w", err)
	}

	opportunity := map[string]interface{}{
		"surface_id":       surfaceID,
		"title_id":         titleID.String,
		"shot_id":          shotID.String,
		"start_time":       startTime.Float64,
		"end_time":         endTime.Float64,
		"duration":         duration.Float64,
		"surface_type":     surfaceType.String,
		"prs_score":        prsScore.Float64,
		"visibility_score": visibilityScore.Float64,
		"area_pixels":      areaPixels.Float64,
		"area_world_m2":    areaWorldM2.Float64,
		"restrictions":     restrictions.String,
		"created_at":       createdAt.Time.Format(time.RFC3339),
	}

	return opportunity, nil
}

// CreatePlacementBooking creates a new placement booking
func (db *DB) CreatePlacementBooking(booking map[string]interface{}) (string, error) {
	bookingID := fmt.Sprintf("booking_%s_%d", booking["surface_id"], time.Now().Unix())

	query := `
		INSERT INTO placement_bookings (
			booking_id, surface_id, advertiser_id, campaign_id, 
			bid_amount_cpm, estimated_impressions, status,
			booking_time, min_prs_score
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	_, err := db.Exec(query,
		bookingID,
		booking["surface_id"],
		booking["advertiser_id"],
		booking["campaign_id"],
		booking["bid_amount_cpm"],
		booking["max_impressions"],
		"confirmed",
		time.Now(),
		booking["min_prs_score"],
	)

	if err != nil {
		return "", fmt.Errorf("failed to create booking: %w", err)
	}

	return bookingID, nil
}

// GetPlacementBooking retrieves a placement booking by ID
func (db *DB) GetPlacementBooking(bookingID string) (map[string]interface{}, error) {
	query := `
		SELECT 
			booking_id, surface_id, advertiser_id, campaign_id,
			bid_amount_cpm, final_cpm_rate, estimated_impressions, actual_impressions,
			status, booking_time, confirmation_time
		FROM placement_bookings 
		WHERE booking_id = $1
	`

	row := db.QueryRow(query, bookingID)

	var surfaceID, advertiserID, campaignID, status sql.NullString
	var bidAmountCPM, finalCPMRate sql.NullFloat64
	var estimatedImpressions, actualImpressions sql.NullInt64
	var bookingTime, confirmationTime sql.NullTime

	err := row.Scan(&bookingID, &surfaceID, &advertiserID, &campaignID, &bidAmountCPM, &finalCPMRate, &estimatedImpressions, &actualImpressions, &status, &bookingTime, &confirmationTime)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil // Not found
		}
		return nil, fmt.Errorf("failed to scan booking: %w", err)
	}

	booking := map[string]interface{}{
		"booking_id":            bookingID,
		"surface_id":            surfaceID.String,
		"advertiser_id":         advertiserID.String,
		"campaign_id":           campaignID.String,
		"bid_amount_cpm":        bidAmountCPM.Float64,
		"final_cpm_rate":        finalCPMRate.Float64,
		"estimated_impressions": estimatedImpressions.Int64,
		"actual_impressions":    actualImpressions.Int64,
		"status":                status.String,
		"booking_time":          bookingTime.Time.Format(time.RFC3339),
		"confirmation_time":     confirmationTime.Time.Format(time.RFC3339),
	}

	return booking, nil
}

// RecordExposureEvent records a viewer exposure event
func (db *DB) RecordExposureEvent(event map[string]interface{}) (string, error) {
	eventID := fmt.Sprintf("event_%s_%d", event["booking_id"], time.Now().UnixNano())

	query := `
		INSERT INTO exposure_events (
			event_id, booking_id, viewer_id, event_timestamp,
			exposure_duration, screen_coverage_percentage, attention_score,
			device_type, consent_given
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	_, err := db.Exec(query,
		eventID,
		event["booking_id"],
		event["viewer_id"],
		time.Now(),
		event["exposure_duration"],
		event["screen_coverage"],
		event["attention_score"],
		event["device_type"],
		true, // consent_given
	)

	if err != nil {
		return "", fmt.Errorf("failed to record exposure event: %w", err)
	}

	return eventID, nil
}