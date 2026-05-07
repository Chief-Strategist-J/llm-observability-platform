.PHONY: sonar-analyze sonar-setup sonar-coverage sonar-start sonar-stop sonar-scan

SCRIPTS_DIR := scripts/sonar

sonar-analyze:
	@bash $(SCRIPTS_DIR)/orchestrator.sh

sonar-setup:
	@cargo install cargo-tarpaulin
	@echo "Dependencies installed successfully"

sonar-coverage:
	@bash $(SCRIPTS_DIR)/coverage_generator.sh

sonar-start:
	@bash $(SCRIPTS_DIR)/server_manager.sh start_server

sonar-stop:
	@bash $(SCRIPTS_DIR)/server_manager.sh stop_server

sonar-scan:
	@bash $(SCRIPTS_DIR)/sonar_scanner.sh
