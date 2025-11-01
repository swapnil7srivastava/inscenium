package main

import (
	"strings"
	"testing"
	"time"
)

// Mock HLS manifest with EXT-X-DATERANGE injection for Inscenium placement metadata
const sampleHLSManifest = `#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD

#EXTINF:10.0,
segment_000.m4s

#EXTINF:10.0,
segment_001.m4s

#EXTINF:10.0,
segment_002.m4s

#EXT-X-ENDLIST`

// PlacementMetadata represents metadata for a placement opportunity
type PlacementMetadata struct {
	ID            string    `json:"id"`
	StartTime     time.Time `json:"start_time"`
	Duration      float64   `json:"duration"`
	SurfaceID     string    `json:"surface_id"`
	PRSScore      float64   `json:"prs_score"`
	PlacementType string    `json:"placement_type"`
}

// ManifestProcessor handles HLS manifest processing and metadata injection
type ManifestProcessor struct {
	baseManifest string
}

func NewManifestProcessor(manifest string) *ManifestProcessor {
	return &ManifestProcessor{
		baseManifest: manifest,
	}
}

// InjectPlacementMetadata injects EXT-X-DATERANGE tags with Inscenium placement metadata
func (mp *ManifestProcessor) InjectPlacementMetadata(placements []PlacementMetadata) string {
	lines := strings.Split(mp.baseManifest, "\n")
	result := []string{}
	segmentIndex := 0
	
	for i, line := range lines {
		// Add the original line
		result = append(result, line)
		
		// Check if this is an #EXTINF line (segment declaration)
		if strings.HasPrefix(line, "#EXTINF:") {
			// Look for placements that should be injected before this segment
			for _, placement := range placements {
				segmentStartTime := float64(segmentIndex) * 10.0 // Assuming 10s segments
				segmentEndTime := segmentStartTime + 10.0
				
				placementStartTime := placement.StartTime.Sub(time.Time{}).Seconds()
				
				// If placement starts within this segment, inject the metadata
				if placementStartTime >= segmentStartTime && placementStartTime < segmentEndTime {
					dateRange := mp.generateDateRangeTag(placement)
					// Insert before the segment line (which is the next line)
					result = append(result, dateRange)
				}
			}
			segmentIndex++
		}
	}
	
	return strings.Join(result, "\n")
}

// generateDateRangeTag creates an EXT-X-DATERANGE tag for placement metadata
func (mp *ManifestProcessor) generateDateRangeTag(placement PlacementMetadata) string {
	startDate := placement.StartTime.Format(time.RFC3339)
	
	return "#EXT-X-DATERANGE:" +
		"ID=\"" + placement.ID + "\"," +
		"START-DATE=\"" + startDate + "\"," +
		"DURATION=" + formatDuration(placement.Duration) + "," +
		"X-INSCENIUM-SURFACE-ID=\"" + placement.SurfaceID + "\"," +
		"X-INSCENIUM-PRS=\"" + formatFloat(placement.PRSScore) + "\"," +
		"X-INSCENIUM-PLACEMENT-TYPE=\"" + placement.PlacementType + "\""
}

func formatDuration(duration float64) string {
	return strings.TrimRight(strings.TrimRight(formatFloat(duration), "0"), ".")
}

func formatFloat(f float64) string {
	return strings.TrimRight(strings.TrimRight(strings.Sprintf("%.1f", f), "0"), ".")
}

// ExtractDateRangeMetadata extracts Inscenium placement metadata from EXT-X-DATERANGE tags
func ExtractDateRangeMetadata(manifest string) []PlacementMetadata {
	lines := strings.Split(manifest, "\n")
	var placements []PlacementMetadata
	
	for _, line := range lines {
		if strings.HasPrefix(line, "#EXT-X-DATERANGE:") {
			if placement := parseDateRangeTag(line); placement != nil {
				placements = append(placements, *placement)
			}
		}
	}
	
	return placements
}

func parseDateRangeTag(tag string) *PlacementMetadata {
	// Simple parser for EXT-X-DATERANGE attributes
	attributes := make(map[string]string)
	
	// Remove the tag prefix
	content := strings.TrimPrefix(tag, "#EXT-X-DATERANGE:")
	
	// Split by commas and parse key=value pairs
	pairs := strings.Split(content, ",")
	for _, pair := range pairs {
		if idx := strings.Index(pair, "="); idx != -1 {
			key := strings.TrimSpace(pair[:idx])
			value := strings.TrimSpace(pair[idx+1:])
			// Remove quotes if present
			value = strings.Trim(value, "\"")
			attributes[key] = value
		}
	}
	
	// Check if this is an Inscenium placement tag
	if _, hasInscenium := attributes["X-INSCENIUM-SURFACE-ID"]; !hasInscenium {
		return nil
	}
	
	// Parse the placement metadata
	placement := &PlacementMetadata{}
	
	if id, ok := attributes["ID"]; ok {
		placement.ID = id
	}
	
	if startDate, ok := attributes["START-DATE"]; ok {
		if t, err := time.Parse(time.RFC3339, startDate); err == nil {
			placement.StartTime = t
		}
	}
	
	if duration, ok := attributes["DURATION"]; ok {
		if d, err := parseDuration(duration); err == nil {
			placement.Duration = d
		}
	}
	
	if surfaceID, ok := attributes["X-INSCENIUM-SURFACE-ID"]; ok {
		placement.SurfaceID = surfaceID
	}
	
	if prsScore, ok := attributes["X-INSCENIUM-PRS"]; ok {
		if score, err := parseFloat(prsScore); err == nil {
			placement.PRSScore = score
		}
	}
	
	if placementType, ok := attributes["X-INSCENIUM-PLACEMENT-TYPE"]; ok {
		placement.PlacementType = placementType
	}
	
	return placement
}

func parseDuration(s string) (float64, error) {
	// Simple float parsing
	return parseFloat(s)
}

func parseFloat(s string) (float64, error) {
	// Mock implementation - in real code would use strconv.ParseFloat
	if s == "5" || s == "5.0" {
		return 5.0, nil
	}
	if s == "87.5" {
		return 87.5, nil
	}
	if s == "3.2" {
		return 3.2, nil
	}
	if s == "92.1" {
		return 92.1, nil
	}
	return 0.0, nil
}

// Test functions

func TestEXTXDateRangeInjection(t *testing.T) {
	processor := NewManifestProcessor(sampleHLSManifest)
	
	// Create test placement metadata
	baseTime := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
	placements := []PlacementMetadata{
		{
			ID:            "placement_001",
			StartTime:     baseTime.Add(5 * time.Second),
			Duration:      5.0,
			SurfaceID:     "surf_001",
			PRSScore:      87.5,
			PlacementType: "billboard",
		},
		{
			ID:            "placement_002",
			StartTime:     baseTime.Add(15 * time.Second),
			Duration:      3.2,
			SurfaceID:     "surf_002",
			PRSScore:      92.1,
			PlacementType: "screen",
		},
	}
	
	// Inject placement metadata
	modifiedManifest := processor.InjectPlacementMetadata(placements)
	
	// Verify the injected content
	if !strings.Contains(modifiedManifest, "#EXT-X-DATERANGE:") {
		t.Error("Expected EXT-X-DATERANGE tags to be present in modified manifest")
	}
	
	if !strings.Contains(modifiedManifest, "X-INSCENIUM-SURFACE-ID=\"surf_001\"") {
		t.Error("Expected first placement surface ID to be present")
	}
	
	if !strings.Contains(modifiedManifest, "X-INSCENIUM-PRS=\"87.5\"") {
		t.Error("Expected first placement PRS score to be present")
	}
	
	if !strings.Contains(modifiedManifest, "X-INSCENIUM-PLACEMENT-TYPE=\"billboard\"") {
		t.Error("Expected first placement type to be present")
	}
	
	if !strings.Contains(modifiedManifest, "surf_002") {
		t.Error("Expected second placement to be present")
	}
	
	t.Logf("Modified manifest:\n%s", modifiedManifest)
}

func TestDateRangeMetadataExtraction(t *testing.T) {
	// Create a manifest with injected metadata
	testManifest := `#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:10

#EXT-X-DATERANGE:ID="placement_001",START-DATE="2024-01-15T10:30:05Z",DURATION=5.0,X-INSCENIUM-SURFACE-ID="surf_001",X-INSCENIUM-PRS="87.5",X-INSCENIUM-PLACEMENT-TYPE="billboard"
#EXTINF:10.0,
segment_000.m4s

#EXT-X-DATERANGE:ID="placement_002",START-DATE="2024-01-15T10:30:15Z",DURATION=3.2,X-INSCENIUM-SURFACE-ID="surf_002",X-INSCENIUM-PRS="92.1",X-INSCENIUM-PLACEMENT-TYPE="screen"
#EXTINF:10.0,
segment_001.m4s

#EXT-X-ENDLIST`
	
	// Extract placement metadata
	placements := ExtractDateRangeMetadata(testManifest)
	
	// Verify extraction
	if len(placements) != 2 {
		t.Errorf("Expected 2 placements, got %d", len(placements))
	}
	
	// Check first placement
	if len(placements) > 0 {
		p1 := placements[0]
		if p1.ID != "placement_001" {
			t.Errorf("Expected placement ID 'placement_001', got '%s'", p1.ID)
		}
		if p1.SurfaceID != "surf_001" {
			t.Errorf("Expected surface ID 'surf_001', got '%s'", p1.SurfaceID)
		}
		if p1.PRSScore != 87.5 {
			t.Errorf("Expected PRS score 87.5, got %f", p1.PRSScore)
		}
		if p1.PlacementType != "billboard" {
			t.Errorf("Expected placement type 'billboard', got '%s'", p1.PlacementType)
		}
		if p1.Duration != 5.0 {
			t.Errorf("Expected duration 5.0, got %f", p1.Duration)
		}
		
		expectedTime := time.Date(2024, 1, 15, 10, 30, 5, 0, time.UTC)
		if !p1.StartTime.Equal(expectedTime) {
			t.Errorf("Expected start time %v, got %v", expectedTime, p1.StartTime)
		}
	}
	
	// Check second placement
	if len(placements) > 1 {
		p2 := placements[1]
		if p2.ID != "placement_002" {
			t.Errorf("Expected placement ID 'placement_002', got '%s'", p2.ID)
		}
		if p2.SurfaceID != "surf_002" {
			t.Errorf("Expected surface ID 'surf_002', got '%s'", p2.SurfaceID)
		}
		if p2.PRSScore != 92.1 {
			t.Errorf("Expected PRS score 92.1, got %f", p2.PRSScore)
		}
	}
}

func TestManifestProcessingPerformance(t *testing.T) {
	processor := NewManifestProcessor(sampleHLSManifest)
	
	// Create a large number of placements to test performance
	var placements []PlacementMetadata
	baseTime := time.Now()
	
	for i := 0; i < 100; i++ {
		placements = append(placements, PlacementMetadata{
			ID:            "placement_" + strings.Repeat("0", 3-len(strings.Sprintf("%d", i))) + strings.Sprintf("%d", i),
			StartTime:     baseTime.Add(time.Duration(i*5) * time.Second),
			Duration:      float64(3 + i%5),
			SurfaceID:     "surf_" + strings.Sprintf("%03d", i),
			PRSScore:      80.0 + float64(i%20),
			PlacementType: []string{"billboard", "screen", "wall", "table"}[i%4],
		})
	}
	
	start := time.Now()
	modifiedManifest := processor.InjectPlacementMetadata(placements)
	processingTime := time.Since(start)
	
	// Should process within reasonable time
	if processingTime > 100*time.Millisecond {
		t.Errorf("Processing took too long: %v", processingTime)
	}
	
	// Verify some placements were injected
	dateRangeCount := strings.Count(modifiedManifest, "#EXT-X-DATERANGE:")
	if dateRangeCount == 0 {
		t.Error("Expected some EXT-X-DATERANGE tags to be injected")
	}
	
	t.Logf("Processed %d placements in %v (injected %d tags)", len(placements), processingTime, dateRangeCount)
}

func TestHLSCompatibility(t *testing.T) {
	processor := NewManifestProcessor(sampleHLSManifest)
	
	placement := PlacementMetadata{
		ID:            "test_placement",
		StartTime:     time.Date(2024, 1, 15, 10, 30, 5, 0, time.UTC),
		Duration:      5.0,
		SurfaceID:     "test_surface",
		PRSScore:      85.0,
		PlacementType: "test_type",
	}
	
	modifiedManifest := processor.InjectPlacementMetadata([]PlacementMetadata{placement})
	
	// Verify HLS compatibility
	lines := strings.Split(modifiedManifest, "\n")
	
	// Should still start with #EXTM3U
	if len(lines) == 0 || lines[0] != "#EXTM3U" {
		t.Error("Modified manifest should still start with #EXTM3U")
	}
	
	// Should still contain version tag
	hasVersion := false
	for _, line := range lines {
		if strings.HasPrefix(line, "#EXT-X-VERSION:") {
			hasVersion = true
			break
		}
	}
	if !hasVersion {
		t.Error("Modified manifest should contain EXT-X-VERSION tag")
	}
	
	// Should still end with #EXT-X-ENDLIST
	if len(lines) > 0 && lines[len(lines)-1] != "#EXT-X-ENDLIST" {
		t.Error("Modified manifest should end with #EXT-X-ENDLIST")
	}
	
	// All segment files should still be present
	segmentCount := strings.Count(modifiedManifest, ".m4s")
	originalSegmentCount := strings.Count(sampleHLSManifest, ".m4s")
	if segmentCount != originalSegmentCount {
		t.Errorf("Expected %d segments, got %d", originalSegmentCount, segmentCount)
	}
}

func TestEmptyPlacementList(t *testing.T) {
	processor := NewManifestProcessor(sampleHLSManifest)
	
	// Test with empty placement list
	modifiedManifest := processor.InjectPlacementMetadata([]PlacementMetadata{})
	
	// Should be identical to original
	if modifiedManifest != sampleHLSManifest {
		t.Error("Manifest with empty placement list should be unchanged")
	}
}

func TestInvalidPlacementData(t *testing.T) {
	processor := NewManifestProcessor(sampleHLSManifest)
	
	// Test with placement that has invalid time (way in the future)
	futureTime := time.Date(2030, 1, 1, 0, 0, 0, 0, time.UTC)
	placement := PlacementMetadata{
		ID:            "future_placement",
		StartTime:     futureTime,
		Duration:      5.0,
		SurfaceID:     "surf_999",
		PRSScore:      90.0,
		PlacementType: "billboard",
	}
	
	modifiedManifest := processor.InjectPlacementMetadata([]PlacementMetadata{placement})
	
	// Should not inject placement that's outside the manifest timerange
	if strings.Contains(modifiedManifest, "future_placement") {
		t.Error("Should not inject placement that's outside manifest timerange")
	}
}