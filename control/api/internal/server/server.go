package server

import (
	"database/sql"

	"github.com/redis/go-redis/v9"
)

// Config holds server configuration
type Config struct {
	Database    *sql.DB
	Redis       *redis.Client
	JWTSecret   string
	Environment string
}

// Server represents the main server instance
type Server struct {
	config *Config
	db     *sql.DB
	redis  *redis.Client
}

// New creates a new server instance
func New(config *Config) *Server {
	return &Server{
		config: config,
		db:     config.Database,
		redis:  config.Redis,
	}
}

// Database returns the database connection
func (s *Server) Database() *sql.DB {
	return s.db
}

// Redis returns the redis connection
func (s *Server) Redis() *redis.Client {
	return s.redis
}

// Config returns the server configuration
func (s *Server) Config() *Config {
	return s.config
}