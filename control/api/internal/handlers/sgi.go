package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/inscenium/inscenium/control/api/internal/db"
	"github.com/sirupsen/logrus"
)

// SGIHandler handles Scene Graph Intelligence requests
type SGIHandler struct {
	db *db.DB
}

// NewSGIHandler creates a new SGI handler
func NewSGIHandler(database *db.DB) *SGIHandler {
	return &SGIHandler{db: database}
}

// ListOpportunities handles GET /sgi/opportunities
func (h *SGIHandler) ListOpportunities(c *gin.Context) {
	titleID := c.Query("title_id")
	minPRSStr := c.DefaultQuery("min_prs", "0")
	limitStr := c.DefaultQuery("limit", "20")
	offsetStr := c.DefaultQuery("offset", "0")

	minPRS, err := strconv.ParseFloat(minPRSStr, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid min_prs parameter"})
		return
	}

	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit < 1 || limit > 100 {
		limit = 20
	}

	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		offset = 0
	}

	logrus.WithFields(logrus.Fields{
		"title_id": titleID,
		"min_prs":  minPRS,
		"limit":    limit,
		"offset":   offset,
	}).Info("Listing placement opportunities")

	opportunities, err := h.db.GetPlacementOpportunities(titleID, minPRS, limit, offset)
	if err != nil {
		logrus.WithError(err).Error("Failed to get placement opportunities")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	// If no database results, return mock data for development
	if len(opportunities) == 0 {
		opportunities = h.getMockOpportunities(titleID, minPRS)
	}

	c.JSON(http.StatusOK, gin.H{
		"opportunities": opportunities,
		"total_count":   len(opportunities),
		"limit":         limit,
		"offset":        offset,
		"filters": gin.H{
			"title_id": titleID,
			"min_prs":  minPRS,
		},
	})
}

// GetOpportunity handles GET /sgi/opportunities/:surface_id
func (h *SGIHandler) GetOpportunity(c *gin.Context) {
	surfaceID := c.Param("surface_id")

	logrus.WithField("surface_id", surfaceID).Info("Getting placement opportunity")

	opportunity, err := h.db.GetPlacementOpportunity(surfaceID)
	if err != nil {
		logrus.WithError(err).Error("Failed to get placement opportunity")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	if opportunity == nil {
		// Return mock data for development
		opportunity = h.getMockOpportunity(surfaceID)
	}

	c.JSON(http.StatusOK, opportunity)
}

// getMockOpportunities returns mock opportunities for development
func (h *SGIHandler) getMockOpportunities(titleID string, minPRS float64) []map[string]interface{} {
	mockOpportunities := []map[string]interface{}{
		{
			"surface_id":       "surface_001",
			"title_id":         titleID,
			"shot_id":          "shot_001",
			"start_time":       5.2,
			"end_time":         12.8,
			"duration":         7.6,
			"prs_score":        87.5,
			"surface_type":     "wall",
			"visibility_score": 92.1,
			"created_at":       "2024-01-15T10:30:00Z",
		},
		{
			"surface_id":       "surface_002",
			"title_id":         titleID,
			"shot_id":          "shot_002",
			"start_time":       15.1,
			"end_time":         23.4,
			"duration":         8.3,
			"prs_score":        92.1,
			"surface_type":     "table",
			"visibility_score": 88.7,
			"created_at":       "2024-01-15T10:30:00Z",
		},
		{
			"surface_id":       "surface_003",
			"title_id":         titleID,
			"shot_id":          "shot_003",
			"start_time":       28.7,
			"end_time":         35.2,
			"duration":         6.5,
			"prs_score":        79.3,
			"surface_type":     "screen",
			"visibility_score": 85.4,
			"created_at":       "2024-01-15T10:30:00Z",
		},
	}

	// Filter by minimum PRS score
	filtered := make([]map[string]interface{}, 0)
	for _, opp := range mockOpportunities {
		if score, ok := opp["prs_score"].(float64); ok && score >= minPRS {
			filtered = append(filtered, opp)
		}
	}

	return filtered
}

// getMockOpportunity returns a mock opportunity for development
func (h *SGIHandler) getMockOpportunity(surfaceID string) map[string]interface{} {
	return map[string]interface{}{
		"surface_id":       surfaceID,
		"title_id":         "title_001",
		"shot_id":          "shot_001",
		"start_time":       5.2,
		"end_time":         12.8,
		"duration":         7.6,
		"prs_score":        87.5,
		"surface_type":     "wall",
		"visibility_score": 92.1,
		"area_pixels":      25680.0,
		"area_world_m2":    1.2,
		"restrictions":     `["family-friendly"]`,
		"geometry": map[string]interface{}{
			"bounds_3d": map[string]interface{}{
				"min_x": 0.1,
				"min_y": 0.2,
				"min_z": 5.0,
				"max_x": 1.8,
				"max_y": 1.5,
				"max_z": 5.1,
			},
		},
		"created_at": "2024-01-15T10:30:00Z",
	}
}