package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/llm-observability/platform/packages/configs/llm-obs-infra/service-discovery/di"
)

func main() {
	configPath := envOrDefault("CONFIG_PATH", "/etc/service-registry/config.json")
	catalogPath := envOrDefault("CATALOG_PATH", "/etc/service-registry/services.json")

	config := di.LoadConfig(configPath)
	container := di.BuildContainer(config)

	di.LoadSeedCatalog(catalogPath, container.Registry)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go container.LeaseManager.Start(ctx)
	go container.HealthProber.Start(ctx)

	events := container.Registry.Subscribe()
	go container.TraefikExporter.Start(events)

	go func() {
		if err := container.Server.Start(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[main] server error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	log.Println("[main] received shutdown signal")
	cancel()

	if err := container.Server.Shutdown(); err != nil {
		log.Printf("[main] server shutdown error: %v", err)
	}

	log.Println("[main] service registry stopped")
}

func envOrDefault(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}
