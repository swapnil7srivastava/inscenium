// Inscenium HTTP Gateway
// ======================
//
// REST API gateway that exposes gRPC services over HTTP.
// Provides endpoints for placement opportunities, booking, and analytics.

package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/inscenium/inscenium/control/api/internal/db"
	"github.com/inscenium/inscenium/control/api/internal/handlers"
	"github.com/inscenium/inscenium/control/api/internal/middleware"
	"github.com/lib/pq"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/redis/go-redis/v9"
	"github.com/rs/cors"
	"github.com/sirupsen/logrus"
)

var (
	// Version information (set during build)
	Version   = "dev"
	BuildTime = "unknown"
	GitCommit = "unknown"
)

// Config holds application configuration
type Config struct {
	Port         string
	DatabaseURL  string
	RedisURL     string
	JWTSecret    string
	Environment  string
	LogLevel     string
	EnableCORS   bool
	CORSOrigins  []string
	EnableMetrics bool
}

// loadConfig loads configuration from environment variables
func loadConfig() *Config {
	return &Config{
		Port:         getEnv("API_PORT", "8080"),
		DatabaseURL:  getEnv("POSTGRES_DSN", "postgresql://inscenium:inscenium@localhost:5432/inscenium"),
		RedisURL:     getEnv("REDIS_URL", "redis://localhost:6379/0"),
		JWTSecret:    getEnv("JWT_SECRET", "dev-secret-key"),
		Environment:  getEnv("ENVIRONMENT", "development"),
		LogLevel:     getEnv("LOG_LEVEL", "INFO"),
		EnableCORS:   getEnv("ENABLE_CORS", "true") == "true",
		CORSOrigins:  strings.Split(getEnv("CORS_ORIGINS", "*"), ","),
		EnableMetrics: getEnv("ENABLE_METRICS", "true") == "true",
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func main() {
	// Load configuration
	config := loadConfig()

	// Configure logging
	setupLogging(config.LogLevel)

	logrus.WithFields(logrus.Fields{
		"version":    Version,
		"build_time": BuildTime,
		"git_commit": GitCommit,
		"environment": config.Environment,
	}).Info("Starting Inscenium HTTP Gateway")

	// Initialize dependencies
	ctx := context.Background()
	
	// Database connection
	database, err := db.Connect()
	if err != nil {
		logrus.WithError(err).Fatal("Failed to connect to database")
	}
	defer database.Close()

	// Apply database migrations
	if err := database.RunMigrations(); err != nil {
		logrus.WithError(err).Fatal("Failed to apply database migrations")
	}

	// Redis connection (optional)
	var redisClient *redis.Client
	if config.RedisURL != "" {
		redisClient, err = connectRedis(config.RedisURL)
		if err != nil {
			logrus.WithError(err).Warn("Failed to connect to Redis, continuing without cache")
		} else {
			defer redisClient.Close()
			logrus.Info("Connected to Redis")
		}
	}

	// Set up HTTP router
	router := setupRouter(config, database, redisClient)

	// Start server
	addr := ":" + config.Port
	logrus.WithField("address", addr).Info("Starting HTTP server")
	
	if err := http.ListenAndServe(addr, router); err != nil {
		logrus.WithError(err).Fatal("Server failed to start")
	}
}

func setupLogging(level string) {
	logrus.SetFormatter(&logrus.JSONFormatter{
		TimestampFormat: time.RFC3339,
	})

	switch strings.ToUpper(level) {
	case "DEBUG":
		logrus.SetLevel(logrus.DebugLevel)
	case "INFO":
		logrus.SetLevel(logrus.InfoLevel)
	case "WARN":
		logrus.SetLevel(logrus.WarnLevel)
	case "ERROR":
		logrus.SetLevel(logrus.ErrorLevel)
	default:
		logrus.SetLevel(logrus.InfoLevel)
	}
}

func setupRouter(config *Config, database *db.DB, redisClient *redis.Client) http.Handler {
	// Set Gin mode based on environment
	if config.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()

	// Global middleware
	r.Use(middleware.RequestLogger())
	r.Use(middleware.Recovery())
	r.Use(middleware.RequestID())

	// CORS middleware
	if config.EnableCORS {
		c := cors.New(cors.Options{
			AllowedOrigins:   config.CORSOrigins,
			AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
			AllowedHeaders:   []string{"*"},
			ExposedHeaders:   []string{"X-Request-ID"},
			AllowCredentials: true,
			MaxAge:           300,
		})
		r.Use(func(ctx *gin.Context) {
			c.HandlerFunc(ctx.Writer, ctx.Request)
			ctx.Next()
		})
	}

	// Initialize handlers
	placementHandler := handlers.NewPlacementHandler(database)
	sgiHandler := handlers.NewSGIHandler(database)
	healthHandler := handlers.NewHealthHandler(database)

	// Health and system endpoints
	r.GET("/health", healthHandler.Health)
	r.GET("/readiness", healthHandler.Readiness)
	r.GET("/version", versionHandler)

	// Metrics endpoint
	if config.EnableMetrics {
		r.GET("/metrics", gin.WrapH(promhttp.Handler()))
	}

	// API routes
	v1 := r.Group("/api/v1")
	{
		// Authentication (TODO: implement proper auth)
		v1.POST("/auth/login", authLoginHandler)

		// SGI opportunities (protected routes)
		sgi := v1.Group("/sgi")
		sgi.Use(middleware.AuthRequired(config.JWTSecret))
		{
			sgi.GET("/opportunities", sgiHandler.ListOpportunities)
			sgi.GET("/opportunities/:surface_id", sgiHandler.GetOpportunity)
		}

		// Placement booking
		bookings := v1.Group("/bookings")
		bookings.Use(middleware.AuthRequired(config.JWTSecret))
		{
			bookings.POST("", placementHandler.BookPlacement)
			bookings.GET("/:id", placementHandler.GetBooking)
			bookings.DELETE("/:id", placementHandler.CancelBooking)
		}

		// Exposure events
		events := v1.Group("/events")
		events.Use(middleware.AuthRequired(config.JWTSecret))
		{
			events.POST("/exposure", placementHandler.RecordExposure)
			events.POST("/exposure/batch", placementHandler.BatchRecordExposures)
		}

		// Analytics and metrics
		analytics := v1.Group("/analytics")
		analytics.Use(middleware.AuthRequired(config.JWTSecret))
		{
			analytics.GET("/metrics/:booking_id", placementHandler.GetMetrics)
			analytics.GET("/events/:booking_id", placementHandler.GetExposureEvents)
		}
	}

	return r
}

// Version handler returns build information
func versionHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"version":    Version,
		"build_time": BuildTime,
		"git_commit": GitCommit,
		"service":    "inscenium-api-gateway",
	})
}

// Simple auth handler for development (TODO: implement proper authentication)
func authLoginHandler(c *gin.Context) {
	var loginReq struct {
		Username string `json:"username" binding:"required"`
		Password string `json:"password" binding:"required"`
	}

	if err := c.ShouldBindJSON(&loginReq); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Implement proper user authentication
	// For now, accept any username/password for development
	if loginReq.Username == "" || loginReq.Password == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Generate JWT token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": loginReq.Username,
		"exp": time.Now().Add(24 * time.Hour).Unix(),
		"iat": time.Now().Unix(),
		"aud": "inscenium-api",
	})

	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "dev-secret-key"
	}

	tokenString, err := token.SignedString([]byte(jwtSecret))
	if err != nil {
		logrus.WithError(err).Error("Failed to sign JWT token")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token":      tokenString,
		"token_type": "Bearer",
		"expires_in": 86400, // 24 hours
		"user":       loginReq.Username,
	})
}

// connectDatabase establishes database connection with retries
func connectDatabase(databaseURL string) (*sql.DB, error) {
	maxRetries := 5
	var db *sql.DB
	var err error

	for i := 0; i < maxRetries; i++ {
		db, err = sql.Open("postgres", databaseURL)
		if err != nil {
			logrus.WithError(err).Warnf("Database connection attempt %d failed", i+1)
			time.Sleep(time.Duration(i+1) * time.Second)
			continue
		}

		err = db.Ping()
		if err != nil {
			logrus.WithError(err).Warnf("Database ping attempt %d failed", i+1)
			time.Sleep(time.Duration(i+1) * time.Second)
			continue
		}

		logrus.Info("Successfully connected to database")
		
		// Configure connection pool
		db.SetMaxOpenConns(25)
		db.SetMaxIdleConns(5)
		db.SetConnMaxLifetime(5 * time.Minute)
		
		return db, nil
	}

	return nil, fmt.Errorf("failed to connect to database after %d attempts: %w", maxRetries, err)
}

// connectRedis establishes Redis connection
func connectRedis(redisURL string) (*redis.Client, error) {
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse Redis URL: %w", err)
	}

	client := redis.NewClient(opts)
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err = client.Ping(ctx).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to ping Redis: %w", err)
	}

	return client, nil
}