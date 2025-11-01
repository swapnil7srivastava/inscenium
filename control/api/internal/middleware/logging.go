package middleware

import (
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// RequestLogger middleware logs HTTP requests
func RequestLogger() gin.HandlerFunc {
	return gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		logrus.WithFields(logrus.Fields{
			"timestamp":    param.TimeStamp.Format(time.RFC3339),
			"status":       param.StatusCode,
			"latency":      param.Latency,
			"client_ip":    param.ClientIP,
			"method":       param.Method,
			"path":         param.Path,
			"user_agent":   param.Request.UserAgent(),
			"request_id":   param.Request.Header.Get("X-Request-ID"),
		}).Info("HTTP Request")
		return ""
	})
}

// Recovery middleware handles panics
func Recovery() gin.HandlerFunc {
	return gin.RecoveryWithWriter(logrus.StandardLogger().Out, func(c *gin.Context, recovered interface{}) {
		logrus.WithFields(logrus.Fields{
			"recovered": recovered,
			"path":      c.Request.URL.Path,
			"method":    c.Request.Method,
		}).Error("Panic recovered")
	})
}

// RequestID middleware adds request ID to context
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}
		
		c.Header("X-Request-ID", requestID)
		c.Set("request_id", requestID)
		c.Next()
	}
}