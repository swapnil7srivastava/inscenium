package handlers

import (
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

type MockDB struct {
	*db.DB
	opportunities []map[string]interface{}
	opportunity   map[string]interface{}
	shouldError   bool
}

func (m *MockDB) GetPlacementOpportunities(titleID string, minPRS float64, limit, offset int) ([]map[string]interface{}, error) {
	if m.shouldError {
		return nil, assert.AnError
	}
	return m.opportunities, nil
}

func (m *MockDB) GetPlacementOpportunity(surfaceID string) (map[string]interface{}, error) {
	if m.shouldError {
		return nil, assert.AnError
	}
	return m.opportunity, nil
}

func TestSGIHandler_ListOpportunities(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		queryParams    string
		mockDB         *MockDB
		expectedStatus int
		expectedCount  int
		description    string
	}{
		{
			name:        "list opportunities with no filters",
			queryParams: "",
			mockDB: &MockDB{
				opportunities: []map[string]interface{}{
					{
						"surface_id": "surface_001",
						"title_id":   "title_001",
						"prs_score":  87.5,
					},
					{
						"surface_id": "surface_002", 
						"title_id":   "title_001",
						"prs_score":  92.1,
					},
				},
				shouldError: false,
			},
			expectedStatus: http.StatusOK,
			expectedCount:  2,
			description:    "Should return all opportunities from database",
		},
		{
			name:        "list opportunities with title filter",
			queryParams: "?title_id=title_001&min_prs=80",
			mockDB: &MockDB{
				opportunities: []map[string]interface{}{
					{
						"surface_id": "surface_001",
						"title_id":   "title_001",
						"prs_score":  87.5,
					},
				},
				shouldError: false,
			},
			expectedStatus: http.StatusOK,
			expectedCount:  1,
			description:    "Should filter opportunities by title and PRS score",
		},
		{
			name:        "list opportunities with invalid min_prs",
			queryParams: "?min_prs=invalid",
			mockDB: &MockDB{
				opportunities: []map[string]interface{}{},
				shouldError:   false,
			},
			expectedStatus: http.StatusBadRequest,
			expectedCount:  0,
			description:    "Should return error for invalid min_prs parameter",
		},
		{
			name:        "database error",
			queryParams: "",
			mockDB: &MockDB{
				opportunities: []map[string]interface{}{},
				shouldError:   true,
			},
			expectedStatus: http.StatusInternalServerError,
			expectedCount:  0,
			description:    "Should return 500 on database error",
		},
		{
			name:        "empty database returns mock data",
			queryParams: "",
			mockDB: &MockDB{
				opportunities: []map[string]interface{}{}, // Empty result triggers mock data
				shouldError:   false,
			},
			expectedStatus: http.StatusOK,
			expectedCount:  3, // Mock data has 3 opportunities
			description:    "Should return mock data when database is empty",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler with mock database
			handler := &SGIHandler{db: tt.mockDB}
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
				assert.Contains(t, response, "limit")
				assert.Contains(t, response, "offset") 
				assert.Contains(t, response, "filters")

				// Check opportunity count
				opportunities, ok := response["opportunities"].([]interface{})
				assert.True(t, ok, "Opportunities should be an array")
				assert.Len(t, opportunities, tt.expectedCount)

				// Validate total_count matches array length
				totalCount, ok := response["total_count"].(float64)
				assert.True(t, ok, "Total count should be a number")
				assert.Equal(t, float64(tt.expectedCount), totalCount)

				// Validate filters object
				filters, ok := response["filters"].(map[string]interface{})
				assert.True(t, ok, "Filters should be an object")
				assert.Contains(t, filters, "title_id")
				assert.Contains(t, filters, "min_prs")
			}
		})
	}
}

func TestSGIHandler_GetOpportunity(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		surfaceID      string
		mockDB         *MockDB
		expectedStatus int
		description    string
	}{
		{
			name:      "get existing opportunity",
			surfaceID: "surface_001",
			mockDB: &MockDB{
				opportunity: map[string]interface{}{
					"surface_id":       "surface_001",
					"title_id":         "title_001",
					"prs_score":        87.5,
					"visibility_score": 92.1,
				},
				shouldError: false,
			},
			expectedStatus: http.StatusOK,
			description:    "Should return opportunity from database",
		},
		{
			name:      "opportunity not found in database, return mock",
			surfaceID: "surface_999",
			mockDB: &MockDB{
				opportunity: nil, // Not found
				shouldError: false,
			},
			expectedStatus: http.StatusOK,
			description:    "Should return mock data when opportunity not found",
		},
		{
			name:      "database error",
			surfaceID: "surface_001",
			mockDB: &MockDB{
				opportunity: nil,
				shouldError: true,
			},
			expectedStatus: http.StatusInternalServerError,
			description:    "Should return 500 on database error",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup handler with mock database
			handler := &SGIHandler{db: tt.mockDB}
			router := gin.New()
			router.GET("/opportunities/:surface_id", handler.GetOpportunity)

			// Execute request
			url := "/opportunities/" + tt.surfaceID
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

				// Validate required fields
				assert.Contains(t, response, "surface_id")
				assert.Contains(t, response, "title_id") 
				assert.Contains(t, response, "prs_score")

				// Validate surface_id matches request
				surfaceID, ok := response["surface_id"].(string)
				assert.True(t, ok, "Surface ID should be string")
				assert.Equal(t, tt.surfaceID, surfaceID)

				// Validate numeric fields
				prsScore, ok := response["prs_score"].(float64)
				assert.True(t, ok, "PRS score should be number")
				assert.Greater(t, prsScore, 0.0, "PRS score should be positive")
			}
		})
	}
}

func TestSGIHandler_getMockOpportunities(t *testing.T) {
	handler := &SGIHandler{db: nil}

	tests := []struct {
		name         string
		titleID      string
		minPRS       float64
		expectedLen  int
		description  string
	}{
		{
			name:        "all opportunities with no filter",
			titleID:     "title_001",
			minPRS:      0.0,
			expectedLen: 3,
			description: "Should return all mock opportunities",
		},
		{
			name:        "filter by high PRS score",
			titleID:     "title_001", 
			minPRS:      85.0,
			expectedLen: 2, // surface_001 (87.5) and surface_002 (92.1)
			description: "Should filter opportunities by minimum PRS score",
		},
		{
			name:        "filter by very high PRS score",
			titleID:     "title_001",
			minPRS:      95.0,
			expectedLen: 0,
			description: "Should return no opportunities when PRS filter is too high",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opportunities := handler.getMockOpportunities(tt.titleID, tt.minPRS)
			
			assert.Len(t, opportunities, tt.expectedLen, tt.description)

			// Validate each opportunity has required fields
			for i, opp := range opportunities {
				assert.Contains(t, opp, "surface_id", "Opportunity %d should have surface_id", i)
				assert.Contains(t, opp, "title_id", "Opportunity %d should have title_id", i) 
				assert.Contains(t, opp, "prs_score", "Opportunity %d should have prs_score", i)
				assert.Contains(t, opp, "surface_type", "Opportunity %d should have surface_type", i)
				assert.Contains(t, opp, "visibility_score", "Opportunity %d should have visibility_score", i)

				// Validate title_id matches request
				assert.Equal(t, tt.titleID, opp["title_id"], "Title ID should match request")

				// Validate PRS score meets minimum requirement
				prsScore, ok := opp["prs_score"].(float64)
				assert.True(t, ok, "PRS score should be float64")
				assert.GreaterOrEqual(t, prsScore, tt.minPRS, "PRS score should meet minimum requirement")
			}
		})
	}
}

func TestSGIHandler_getMockOpportunity(t *testing.T) {
	handler := &SGIHandler{db: nil}

	tests := []struct {
		name        string
		surfaceID   string
		description string
	}{
		{
			name:        "generate mock opportunity",
			surfaceID:   "test_surface_123",
			description: "Should generate mock opportunity for any surface ID",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opportunity := handler.getMockOpportunity(tt.surfaceID)

			// Validate required fields
			assert.Contains(t, opportunity, "surface_id")
			assert.Contains(t, opportunity, "title_id")
			assert.Contains(t, opportunity, "prs_score")
			assert.Contains(t, opportunity, "surface_type")
			assert.Contains(t, opportunity, "visibility_score")
			assert.Contains(t, opportunity, "geometry")

			// Validate surface_id matches request
			assert.Equal(t, tt.surfaceID, opportunity["surface_id"])

			// Validate numeric fields are reasonable
			prsScore, ok := opportunity["prs_score"].(float64)
			assert.True(t, ok, "PRS score should be float64")
			assert.Greater(t, prsScore, 0.0, "PRS score should be positive")
			assert.LessOrEqual(t, prsScore, 100.0, "PRS score should be <= 100")

			visibilityScore, ok := opportunity["visibility_score"].(float64)
			assert.True(t, ok, "Visibility score should be float64")
			assert.Greater(t, visibilityScore, 0.0, "Visibility score should be positive")

			// Validate geometry object
			geometry, ok := opportunity["geometry"].(map[string]interface{})
			assert.True(t, ok, "Geometry should be object")
			assert.Contains(t, geometry, "bounds_3d")
		})
	}
}

func TestNewSGIHandler(t *testing.T) {
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
			handler := NewSGIHandler(tt.database)
			
			if tt.wantNil {
				assert.Nil(t, handler)
			} else {
				assert.NotNil(t, handler)
				assert.Equal(t, tt.database, handler.db)
			}
		})
	}
}

// Benchmark list opportunities endpoint
func BenchmarkSGIHandler_ListOpportunities(b *testing.B) {
	gin.SetMode(gin.TestMode)
	
	mockDB := &MockDB{
		opportunities: []map[string]interface{}{
			{"surface_id": "surface_001", "prs_score": 87.5},
			{"surface_id": "surface_002", "prs_score": 92.1},
		},
		shouldError: false,
	}
	
	handler := &SGIHandler{db: mockDB}
	router := gin.New()
	router.GET("/opportunities", handler.ListOpportunities)

	req := httptest.NewRequest(http.MethodGet, "/opportunities", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resp := httptest.NewRecorder()
		router.ServeHTTP(resp, req)
	}
}

// Benchmark get opportunity endpoint
func BenchmarkSGIHandler_GetOpportunity(b *testing.B) {
	gin.SetMode(gin.TestMode)
	
	mockDB := &MockDB{
		opportunity: map[string]interface{}{
			"surface_id": "surface_001",
			"prs_score":  87.5,
		},
		shouldError: false,
	}
	
	handler := &SGIHandler{db: mockDB}
	router := gin.New()
	router.GET("/opportunities/:surface_id", handler.GetOpportunity)

	req := httptest.NewRequest(http.MethodGet, "/opportunities/surface_001", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resp := httptest.NewRecorder()
		router.ServeHTTP(resp, req)
	}
}