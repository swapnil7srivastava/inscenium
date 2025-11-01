package handlers

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/inscenium/inscenium/control/api/internal/db"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestHealthHandler_Health(t *testing.T) {
	gin.SetMode(gin.TestMode)
	
	tests := []struct {
		name           string
		expectedStatus int
		checkFields    []string
	}{
		{
			name:           "health check returns 200",
			expectedStatus: http.StatusOK,
			checkFields:    []string{"status", "service", "timestamp", "version"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup
			handler := NewHealthHandler(nil) // Health endpoint doesn't need DB
			router := gin.New()
			router.GET("/health", handler.Health)

			// Execute request
			req := httptest.NewRequest(http.MethodGet, "/health", nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert
			assert.Equal(t, tt.expectedStatus, resp.Code)

			var response map[string]interface{}
			err := json.Unmarshal(resp.Body.Bytes(), &response)
			require.NoError(t, err)

			// Check required fields
			for _, field := range tt.checkFields {
				assert.Contains(t, response, field, "Response should contain field: %s", field)
			}

			// Validate specific values
			assert.Equal(t, "healthy", response["status"])
			assert.Equal(t, "inscenium-api-gateway", response["service"])
			assert.Equal(t, "1.0.0", response["version"])

			// Validate timestamp format
			timestamp, ok := response["timestamp"].(string)
			assert.True(t, ok, "Timestamp should be string")
			_, err = time.Parse(time.RFC3339, timestamp)
			assert.NoError(t, err, "Timestamp should be valid RFC3339 format")
		})
	}
}

func TestHealthHandler_Readiness(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		mockDB         *db.DB
		expectedStatus int
		expectedReady  bool
		description    string
	}{
		{
			name:           "readiness with no database",
			mockDB:         nil,
			expectedStatus: http.StatusOK,
			expectedReady:  true, // Should be ready even without DB configured
			description:    "Service is ready when DB is not configured",
		},
		{
			name:           "readiness with database configured",
			mockDB:         &db.DB{}, // Empty DB struct for test
			expectedStatus: http.StatusOK,
			expectedReady:  false, // Will fail ping since it's not a real connection
			description:    "Service readiness depends on DB health",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup
			handler := NewHealthHandler(tt.mockDB)
			router := gin.New()
			router.GET("/readiness", handler.Readiness)

			// Execute request
			req := httptest.NewRequest(http.MethodGet, "/readiness", nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert
			assert.Equal(t, tt.expectedStatus, resp.Code)

			var response map[string]interface{}
			err := json.Unmarshal(resp.Body.Bytes(), &response)
			require.NoError(t, err)

			// Check required fields
			assert.Contains(t, response, "status")
			assert.Contains(t, response, "service")
			assert.Contains(t, response, "timestamp")
			assert.Contains(t, response, "checks")

			// Validate service
			assert.Equal(t, "inscenium-api-gateway", response["service"])

			// Validate checks structure
			checks, ok := response["checks"].(map[string]interface{})
			assert.True(t, ok, "Checks should be an object")
			
			assert.Contains(t, checks, "database")
			assert.Contains(t, checks, "redis")

			// Validate database check
			dbCheck, ok := checks["database"].(map[string]interface{})
			assert.True(t, ok, "Database check should be an object")
			assert.Contains(t, dbCheck, "status")

			// Validate Redis check (should be not_configured)
			redisCheck, ok := checks["redis"].(map[string]interface{})
			assert.True(t, ok, "Redis check should be an object")
			assert.Equal(t, "not_configured", redisCheck["status"])

			// Validate timestamp format
			timestamp, ok := response["timestamp"].(string)
			assert.True(t, ok, "Timestamp should be string")
			_, err = time.Parse(time.RFC3339, timestamp)
			assert.NoError(t, err, "Timestamp should be valid RFC3339 format")
		})
	}
}

func TestNewHealthHandler(t *testing.T) {
	tests := []struct {
		name     string
		database *db.DB
		wantNil  bool
	}{
		{
			name:     "create handler with nil database",
			database: nil,
			wantNil:  false,
		},
		{
			name:     "create handler with database",
			database: &db.DB{},
			wantNil:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			handler := NewHealthHandler(tt.database)
			
			if tt.wantNil {
				assert.Nil(t, handler)
			} else {
				assert.NotNil(t, handler)
				assert.Equal(t, tt.database, handler.db)
			}
		})
	}
}

// Benchmark health endpoint
func BenchmarkHealthHandler_Health(b *testing.B) {
	gin.SetMode(gin.TestMode)
	handler := NewHealthHandler(nil)
	router := gin.New()
	router.GET("/health", handler.Health)

	req := httptest.NewRequest(http.MethodGet, "/health", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resp := httptest.NewRecorder()
		router.ServeHTTP(resp, req)
	}
}

// Benchmark readiness endpoint  
func BenchmarkHealthHandler_Readiness(b *testing.B) {
	gin.SetMode(gin.TestMode)
	handler := NewHealthHandler(nil)
	router := gin.New()
	router.GET("/readiness", handler.Readiness)

	req := httptest.NewRequest(http.MethodGet, "/readiness", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resp := httptest.NewRecorder()
		router.ServeHTTP(resp, req)
	}
}