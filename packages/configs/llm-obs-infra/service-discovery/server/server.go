package server

import (
	"context"
	"log"
	"net/http"
	"time"
)

type ServerConfig struct {
	Port            string        `json:"port"`
	ReadTimeout     time.Duration `json:"readTimeout"`
	WriteTimeout    time.Duration `json:"writeTimeout"`
	ShutdownTimeout time.Duration `json:"shutdownTimeout"`
}

var DefaultServerConfig = ServerConfig{
	Port:            "31426",
	ReadTimeout:     10 * time.Second,
	WriteTimeout:    30 * time.Second,
	ShutdownTimeout: 5 * time.Second,
}

type Server struct {
	httpServer *http.Server
	config     ServerConfig
}

func NewServer(config ServerConfig, handler http.Handler) *Server {
	return &Server{
		config: config,
		httpServer: &http.Server{
			Addr:         ":" + config.Port,
			Handler:      handler,
			ReadTimeout:  config.ReadTimeout,
			WriteTimeout: config.WriteTimeout,
		},
	}
}

func (s *Server) Start() error {
	log.Printf("[server] listening on :%s", s.config.Port)
	return s.httpServer.ListenAndServe()
}

func (s *Server) Shutdown() error {
	ctx, cancel := context.WithTimeout(context.Background(), s.config.ShutdownTimeout)
	defer cancel()
	log.Println("[server] shutting down gracefully")
	return s.httpServer.Shutdown(ctx)
}
