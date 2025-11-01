package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/inscenium/inscenium/control/api/internal/db"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// MockPlacementDB extends MockDB for placement-specific methods
type MockPlacementDB struct {
	*db.DB
	opportunities []map[string]interface{}
	opportunity   map[string]interface{}
	booking       map[string]interface{}
	bookingID     string
	shouldError   bool
}

func (m *MockPlacementDB) GetPlacementOpportunities(titleID string, minPRS float64, limit, offset int) ([]map[string]interface{}, error) {
	if m.shouldError {
		return nil, assert.AnError
	}
	return m.opportunities, nil
}

func (m *MockPlacementDB) GetPlacementOpportunity(surfaceID string) (map[string]interface{}, error) {
	if m.shouldError {
		return nil, assert.AnError
	}
	return m.opportunity, nil
}

func (m *MockPlacementDB) CreatePlacementBooking(booking map[string]interface{}) (string, error) {
	if m.shouldError {
		return "", assert.AnError
	}
	return m.bookingID, nil
}

func (m *MockPlacementDB) GetPlacementBooking(bookingID string) (map[string]interface{}, error) {
	if m.shouldError {
		return nil, assert.AnError
	}
	return m.booking, nil
}

func TestPlacementHandler_ListOpportunities(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		queryParams    string
		expectedStatus int
		description    string
	}{
		{
			name:           "list opportunities with no filters",
			queryParams:    "",
			expectedStatus: http.StatusOK,
			description:    "Should return mock opportunities",
		},
		{
			name:           "list opportunities with title filter",
			queryParams:    "?title_id=title_001&min_prs=80",
			expectedStatus: http.StatusOK,
			description:    "Should filter opportunities by title and PRS score",
		},
		{
			name:           "list opportunities with invalid min_prs",
			queryParams:    "?min_prs=invalid",
			expectedStatus: http.StatusBadRequest,
			description:    "Should return error for invalid min_prs parameter",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.GET("/opportunities", handler.ListOpportunities)

			// Execute request
			url := "/opportunities" + tt.queryParams
			req := httptest.NewRequest(http.MethodGet, url, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusOK {
				// Parse response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check response structure
				assert.Contains(t, response, "opportunities")
				assert.Contains(t, response, "total_count")
				assert.Contains(t, response, "filters")

				// Validate opportunities array
				opportunities, ok := response["opportunities"].([]interface{})
				assert.True(t, ok, "Opportunities should be an array")

				// Validate each opportunity has required fields
				for i, opp := range opportunities {
					oppMap, ok := opp.(map[string]interface{})
					assert.True(t, ok, "Opportunity %d should be object", i)
					
					assert.Contains(t, oppMap, "id", "Opportunity %d should have id", i)
					assert.Contains(t, oppMap, "title_id", "Opportunity %d should have title_id", i)
					assert.Contains(t, oppMap, "prs_score", "Opportunity %d should have prs_score", i)
					assert.Contains(t, oppMap, "surface_type", "Opportunity %d should have surface_type", i)
				}
			}
		})
	}
}

func TestPlacementHandler_GetOpportunity(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		opportunityID  string
		expectedStatus int
		description    string
	}{
		{
			name:           "get existing opportunity",
			opportunityID:  "surface_001",
			expectedStatus: http.StatusOK,
			description:    "Should return mock opportunity data",
		},
		{
			name:           "get opportunity with any ID",
			opportunityID:  "custom_surface_123",
			expectedStatus: http.StatusOK,
			description:    "Should return opportunity with requested ID",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.GET("/opportunities/:id", handler.GetOpportunity)

			// Execute request
			url := "/opportunities/" + tt.opportunityID
			req := httptest.NewRequest(http.MethodGet, url, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusOK {
				// Parse response
				var response PlacementOpportunity
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Validate required fields
				assert.Equal(t, tt.opportunityID, response.ID)
				assert.NotEmpty(t, response.TitleID)
				assert.Greater(t, response.PRSScore, 0.0, "PRS score should be positive")
				assert.NotEmpty(t, response.SurfaceType)
				assert.NotEmpty(t, response.CreatedAt)
			}
		})
	}
}

func TestPlacementHandler_BookPlacement(t *testing.T) {
	gin.SetMode(gin.TestMode)

	validBooking := map[string]interface{}{
		"surface_id":      "surface_001",
		"advertiser_id":   "advertiser_123",
		"campaign_id":     "campaign_456",
		"bid_amount_cpm":  5.50,
		"max_impressions": 1000,
		"min_prs_score":   80.0,
	}

	tests := []struct {
		name           string
		requestBody    map[string]interface{}
		mockDB         *MockPlacementDB
		expectedStatus int
		description    string
	}{
		{
			name:        "successful booking",
			requestBody: validBooking,
			mockDB: &MockPlacementDB{
				bookingID:   "booking_123",
				shouldError: false,
			},
			expectedStatus: http.StatusCreated,
			description:    "Should create booking successfully",
		},
		{
			name: "missing required fields",
			requestBody: map[string]interface{}{
				"surface_id": "surface_001",
				// Missing advertiser_id, campaign_id, bid_amount_cpm
			},
			mockDB: &MockPlacementDB{
				shouldError: false,
			},
			expectedStatus: http.StatusBadRequest,
			description:    "Should return 400 for missing required fields",
		},
		{
			name:        "database error",
			requestBody: validBooking,
			mockDB: &MockPlacementDB{
				shouldError: true,
			},
			expectedStatus: http.StatusInternalServerError,
			description:    "Should return 500 on database error",
		},
		{
			name: "invalid JSON",
			requestBody: map[string]interface{}{
				"bid_amount_cpm": "invalid_number",
			},
			mockDB: &MockPlacementDB{
				shouldError: false,
			},
			expectedStatus: http.StatusBadRequest,
			description:    "Should return 400 for invalid data types",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler with mock database
			handler := &PlacementHandler{db: tt.mockDB}
			router := gin.New()
			router.POST("/bookings", handler.BookPlacement)

			// Prepare request body
			requestBody, _ := json.Marshal(tt.requestBody)
			
			// Execute request
			req := httptest.NewRequest(http.MethodPost, "/bookings", bytes.NewReader(requestBody))
			req.Header.Set("Content-Type", "application/json")
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusCreated {
				// Parse success response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check response structure
				assert.Contains(t, response, "booking_id")
				assert.Contains(t, response, "status") 
				assert.Contains(t, response, "message")
				assert.Contains(t, response, "confirmation_time")

				// Validate values
				assert.Equal(t, "confirmed", response["status"])
				assert.NotEmpty(t, response["booking_id"])
			}
		})
	}
}

func TestPlacementHandler_GetBooking(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		bookingID      string
		expectedStatus int
		description    string
	}{
		{
			name:           "get existing booking",
			bookingID:      "booking_123",
			expectedStatus: http.StatusOK,
			description:    "Should return booking status",
		},
		{
			name:           "get booking with any ID",
			bookingID:      "custom_booking_456",
			expectedStatus: http.StatusOK,
			description:    "Should return mock booking data for any ID",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.GET("/bookings/:id", handler.GetBooking)

			// Execute request
			url := "/bookings/" + tt.bookingID
			req := httptest.NewRequest(http.MethodGet, url, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusOK {
				// Parse response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check required fields
				assert.Contains(t, response, "booking_id")
				assert.Contains(t, response, "status")
				assert.Contains(t, response, "placement_id")
				assert.Contains(t, response, "confirmation_time")

				// Validate booking ID matches request
				assert.Equal(t, tt.bookingID, response["booking_id"])
			}
		})
	}
}

func TestPlacementHandler_CancelBooking(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		bookingID      string
		expectedStatus int
		description    string
	}{
		{
			name:           "cancel existing booking",
			bookingID:      "booking_123",
			expectedStatus: http.StatusOK,
			description:    "Should cancel booking successfully",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.DELETE("/bookings/:id", handler.CancelBooking)

			// Execute request
			url := "/bookings/" + tt.bookingID
			req := httptest.NewRequest(http.MethodDelete, url, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusOK {
				// Parse response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check response structure
				assert.Contains(t, response, "success")
				assert.Contains(t, response, "message")
				assert.Contains(t, response, "cancelled_at")

				// Validate success
				assert.Equal(t, true, response["success"])
			}
		})
	}
}

func TestPlacementHandler_RecordExposure(t *testing.T) {
	gin.SetMode(gin.TestMode)

	validExposure := map[string]interface{}{
		"booking_id":        "booking_123",
		"viewer_id":         "viewer_456",
		"exposure_duration": 5.2,
		"screen_coverage":   25.4,
		"attention_score":   0.82,
	}

	tests := []struct {
		name           string
		requestBody    map[string]interface{}
		expectedStatus int
		description    string
	}{
		{
			name:           "successful exposure recording",
			requestBody:    validExposure,
			expectedStatus: http.StatusCreated,
			description:    "Should record exposure successfully",
		},
		{
			name: "missing required fields",
			requestBody: map[string]interface{}{
				"booking_id": "booking_123",
				// Missing viewer_id and exposure_duration
			},
			expectedStatus: http.StatusBadRequest,
			description:    "Should return 400 for missing required fields",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.POST("/events/exposure", handler.RecordExposure)

			// Prepare request body
			requestBody, _ := json.Marshal(tt.requestBody)
			
			// Execute request
			req := httptest.NewRequest(http.MethodPost, "/events/exposure", bytes.NewReader(requestBody))
			req.Header.Set("Content-Type", "application/json")
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusCreated {
				// Parse response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check response structure
				assert.Contains(t, response, "success")
				assert.Contains(t, response, "event_id")
				assert.Contains(t, response, "message")

				// Validate success
				assert.Equal(t, true, response["success"])
				assert.NotEmpty(t, response["event_id"])
			}
		})
	}
}

func TestPlacementHandler_BatchRecordExposures(t *testing.T) {
	gin.SetMode(gin.TestMode)

	validBatch := map[string]interface{}{
		"events": []map[string]interface{}{
			{
				"booking_id":        "booking_123",
				"viewer_id":         "viewer_456",
				"exposure_duration": 5.2,
			},
			{
				"booking_id":        "booking_123",
				"viewer_id":         "viewer_789",
				"exposure_duration": 3.8,
			},
		},
	}

	tests := []struct {
		name           string
		requestBody    map[string]interface{}
		expectedStatus int
		description    string
	}{
		{
			name:           "successful batch recording",
			requestBody:    validBatch,
			expectedStatus: http.StatusCreated,
			description:    "Should record batch exposures successfully",
		},
		{
			name: "missing events array",
			requestBody: map[string]interface{}{
				"invalid": "data",
			},
			expectedStatus: http.StatusBadRequest,
			description:    "Should return 400 for missing events array",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.POST("/events/exposure/batch", handler.BatchRecordExposures)

			// Prepare request body
			requestBody, _ := json.Marshal(tt.requestBody)
			
			// Execute request
			req := httptest.NewRequest(http.MethodPost, "/events/exposure/batch", bytes.NewReader(requestBody))
			req.Header.Set("Content-Type", "application/json")
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusCreated {
				// Parse response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check response structure
				assert.Contains(t, response, "processed_count")
				assert.Contains(t, response, "failed_count")
				assert.Contains(t, response, "message")

				// Validate counts
				processedCount, ok := response["processed_count"].(float64)
				assert.True(t, ok, "Processed count should be number")
				assert.Greater(t, processedCount, 0.0, "Should process at least one event")
			}
		})
	}
}

func TestPlacementHandler_GetMetrics(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		bookingID      string
		expectedStatus int
		description    string
	}{
		{
			name:           "get metrics for booking",
			bookingID:      "booking_123",
			expectedStatus: http.StatusOK,
			description:    "Should return analytics metrics",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler
			handler := NewPlacementHandler(nil)
			router := gin.New()
			router.GET("/analytics/metrics/:booking_id", handler.GetMetrics)

			// Execute request
			url := "/analytics/metrics/" + tt.bookingID
			req := httptest.NewRequest(http.MethodGet, url, nil)
			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, resp.Code, tt.description)

			if tt.expectedStatus == http.StatusOK {
				// Parse response
				var response map[string]interface{}
				err := json.Unmarshal(resp.Body.Bytes(), &response)
				require.NoError(t, err)

				// Check required metrics fields
				assert.Contains(t, response, "booking_id")
				assert.Contains(t, response, "total_impressions")
				assert.Contains(t, response, "unique_viewers")
				assert.Contains(t, response, "total_exposure_time")
				assert.Contains(t, response, "average_exposure_time")
				assert.Contains(t, response, "average_prs_score")
				assert.Contains(t, response, "average_attention_score")
				assert.Contains(t, response, "average_screen_coverage")

				// Validate booking ID matches request
				assert.Equal(t, tt.bookingID, response["booking_id"])
			}
		})
	}
}

func TestNewPlacementHandler(t *testing.T) {
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
			handler := NewPlacementHandler(tt.database)
			
			if tt.wantNil {
				assert.Nil(t, handler)
			} else {
				assert.NotNil(t, handler)
				assert.Equal(t, tt.database, handler.db)
			}
		})
	}
}