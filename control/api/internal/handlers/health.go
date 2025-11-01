package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/inscenium/inscenium/control/api/internal/db"
)

// HealthHandler handles health check requests
type HealthHandler struct {
	db *db.DB
}

// NewHealthHandler creates a new health handler
func NewHealthHandler(database *db.DB) *HealthHandler {
	return &HealthHandler{db: database}
}

// Health handles GET /health
func (h *HealthHandler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"service":   "inscenium-api-gateway",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"version":   "1.0.0",
	})
}

// Readiness handles GET /readiness
func (h *HealthHandler) Readiness(c *gin.Context) {
	checks := make(map[string]interface{})
	allHealthy := true

	// Check database connection
	if h.db != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()

		if err := h.db.PingContext(ctx); err != nil {
			checks["database"] = map[string]interface{}{
				"status": "unhealthy",
				"error":  err.Error(),
			}
			allHealthy = false
		} else {
			checks["database"] = map[string]interface{}{
				"status": "healthy",
			}
		}
	} else {
		checks["database"] = map[string]interface{}{
			"status": "not_configured",
		}
	}

	// Redis is not directly accessible from health handler
	// This would need to be passed in if Redis health checks are required
	checks["redis"] = map[string]interface{}{
		"status": "not_configured",
	}

	status := "ready"
	statusCode := http.StatusOK
	if !allHealthy {
		status = "not_ready"
		statusCode = http.StatusServiceUnavailable
	}

	c.JSON(statusCode, gin.H{
		"status":    status,
		"service":   "inscenium-api-gateway",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"checks":    checks,
	})
}