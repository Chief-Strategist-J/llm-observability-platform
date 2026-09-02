package server

import (
	"context"
	"log"
	"net/http"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/models"
)

type ServerConfig = models.ServerConfig

var DefaultServerConfig = models.DefaultServerConfig

type Server struct {
	httpServer *http.Server
	config     ServerConfig
}

func NewServer(config ServerConfig, handler http.Handler) *Server {
	addr := config.Addr
	if addr == "" {
		addr = ":31426"
	}
	return &Server{
		config: config,
		httpServer: &http.Server{
			Addr:         addr,
			Handler:      handler,
			ReadTimeout:  config.ReadTimeout,
			WriteTimeout: config.WriteTimeout,
		},
	}
}

func (s *Server) Start() error {
	log.Printf("[server] listening on %s", s.httpServer.Addr)
	return s.httpServer.ListenAndServe()
}

func (s *Server) Shutdown() error {
	ctx, cancel := context.WithTimeout(context.Background(), s.config.ShutdownTimeout)
	defer cancel()
	log.Println("[server] shutting down gracefully")
	return s.httpServer.Shutdown(ctx)
}
