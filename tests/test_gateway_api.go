package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
)

// Mock HTTP gateway server for testing
func createTestGateway() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "ok",
			"timestamp": time.Now().UTC().Format(time.RFC3339),
			"service":   "inscenium-api-gateway",
			"version":   "2.0.0",
		})
	})

	// Additional test endpoints
	router.GET("/api/v1/opportunities", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"opportunities": []gin.H{
				{
					"id":        "opp_001",
					"prs_score": 87.5,
					"status":    "available",
				},
				{
					"id":        "opp_002", 
					"prs_score": 92.1,
					"status":    "active",
				},
			},
			"total": 2,
		})
	})

	router.GET("/api/v1/scene-graphs/:id", func(c *gin.Context) {
		id := c.Param("id")
		c.JSON(http.StatusOK, gin.H{
			"scene_graph_id": id,
			"node_count":     15,
			"edge_count":     28,
			"created_at":     time.Now().UTC().Format(time.RFC3339),
		})
	})

	router.POST("/api/v1/quality-check", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"check_id":      "qc_" + time.Now().Format("20060102150405"),
			"status":        "completed",
			"overall_score": 84.2,
			"issues":        []string{},
		})
	})

	return router
}

func TestHealthEndpoint(t *testing.T) {
	// Create test server
	router := createTestGateway()
	
	// Create test request
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	// Record response
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// Assert status code
	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	// Assert content type
	expectedContentType := "application/json; charset=utf-8"
	if contentType := w.Header().Get("Content-Type"); contentType != expectedContentType {
		t.Errorf("Expected Content-Type %s, got %s", expectedContentType, contentType)
	}

	// Parse response body
	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse JSON response: %v", err)
	}

	// Assert response structure
	if status, ok := response["status"].(string); !ok || status != "ok" {
		t.Errorf("Expected status 'ok', got %v", response["status"])
	}

	if service, ok := response["service"].(string); !ok || service != "inscenium-api-gateway" {
		t.Errorf("Expected service 'inscenium-api-gateway', got %v", response["service"])
	}

	if version, ok := response["version"].(string); !ok || version != "2.0.0" {
		t.Errorf("Expected version '2.0.0', got %v", response["version"])
	}

	// Verify timestamp is recent
	if timestamp, ok := response["timestamp"].(string); ok {
		parsedTime, err := time.Parse(time.RFC3339, timestamp)
		if err != nil {
			t.Errorf("Failed to parse timestamp: %v", err)
		}
		if time.Since(parsedTime) > time.Minute {
			t.Errorf("Timestamp is too old: %v", timestamp)
		}
	} else {
		t.Error("Missing or invalid timestamp in response")
	}
}

func TestOpportunitiesEndpoint(t *testing.T) {
	router := createTestGateway()

	req, err := http.NewRequest("GET", "/api/v1/opportunities", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse JSON response: %v", err)
	}

	// Check opportunities array
	opportunities, ok := response["opportunities"].([]interface{})
	if !ok {
		t.Fatalf("Expected opportunities array, got %T", response["opportunities"])
	}

	if len(opportunities) != 2 {
		t.Errorf("Expected 2 opportunities, got %d", len(opportunities))
	}

	// Check first opportunity
	if len(opportunities) > 0 {
		opp := opportunities[0].(map[string]interface{})
		if opp["id"] != "opp_001" {
			t.Errorf("Expected opportunity id 'opp_001', got %v", opp["id"])
		}
		if opp["prs_score"] != 87.5 {
			t.Errorf("Expected PRS score 87.5, got %v", opp["prs_score"])
		}
	}

	// Check total count
	if total, ok := response["total"].(float64); !ok || total != 2 {
		t.Errorf("Expected total 2, got %v", response["total"])
	}
}

func TestSceneGraphEndpoint(t *testing.T) {
	router := createTestGateway()

	testID := "sg_12345"
	req, err := http.NewRequest("GET", "/api/v1/scene-graphs/"+testID, nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse JSON response: %v", err)
	}

	if response["scene_graph_id"] != testID {
		t.Errorf("Expected scene_graph_id '%s', got %v", testID, response["scene_graph_id"])
	}

	if nodeCount, ok := response["node_count"].(float64); !ok || nodeCount != 15 {
		t.Errorf("Expected node_count 15, got %v", response["node_count"])
	}

	if edgeCount, ok := response["edge_count"].(float64); !ok || edgeCount != 28 {
		t.Errorf("Expected edge_count 28, got %v", response["edge_count"])
	}
}

func TestQualityCheckEndpoint(t *testing.T) {
	router := createTestGateway()

	req, err := http.NewRequest("POST", "/api/v1/quality-check", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse JSON response: %v", err)
	}

	// Check check_id format
	if checkID, ok := response["check_id"].(string); !ok || len(checkID) == 0 {
		t.Errorf("Expected non-empty check_id, got %v", response["check_id"])
	}

	if response["status"] != "completed" {
		t.Errorf("Expected status 'completed', got %v", response["status"])
	}

	if overallScore, ok := response["overall_score"].(float64); !ok || overallScore != 84.2 {
		t.Errorf("Expected overall_score 84.2, got %v", response["overall_score"])
	}

	// Check issues array exists (even if empty)
	if issues, ok := response["issues"].([]interface{}); !ok {
		t.Errorf("Expected issues array, got %T", response["issues"])
	} else if len(issues) != 0 {
		t.Errorf("Expected empty issues array, got %d items", len(issues))
	}
}

func TestGatewayPerformance(t *testing.T) {
	router := createTestGateway()

	// Test multiple concurrent requests
	const numRequests = 50
	done := make(chan bool, numRequests)
	errors := make(chan error, numRequests)

	start := time.Now()

	for i := 0; i < numRequests; i++ {
		go func() {
			req, err := http.NewRequest("GET", "/health", nil)
			if err != nil {
				errors <- err
				return
			}

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != http.StatusOK {
				errors <- err
				return
			}

			done <- true
		}()
	}

	// Wait for all requests to complete
	completed := 0
	errorCount := 0
	timeout := time.After(5 * time.Second)

	for completed+errorCount < numRequests {
		select {
		case <-done:
			completed++
		case err := <-errors:
			t.Logf("Request error: %v", err)
			errorCount++
		case <-timeout:
			t.Fatalf("Timeout waiting for requests to complete. Completed: %d, Errors: %d", completed, errorCount)
		}
	}

	duration := time.Since(start)
	
	if errorCount > 0 {
		t.Errorf("Expected no errors, got %d errors out of %d requests", errorCount, numRequests)
	}

	// Should complete within reasonable time
	if duration > time.Second {
		t.Errorf("Performance test took too long: %v", duration)
	}

	avgResponseTime := duration / time.Duration(numRequests)
	t.Logf("Performance: %d requests in %v (avg: %v per request)", numRequests, duration, avgResponseTime)
}

func TestGatewayErrorHandling(t *testing.T) {
	router := createTestGateway()

	// Test non-existent endpoint
	req, err := http.NewRequest("GET", "/non-existent", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status code %d for non-existent endpoint, got %d", http.StatusNotFound, w.Code)
	}

	// Test invalid HTTP method
	req, err = http.NewRequest("DELETE", "/health", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("Expected status code %d for invalid method, got %d", http.StatusMethodNotAllowed, w.Code)
	}
}

func BenchmarkHealthEndpoint(b *testing.B) {
	router := createTestGateway()

	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		b.Fatalf("Failed to create request: %v", err)
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)
			
			if w.Code != http.StatusOK {
				b.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
			}
		}
	})
}