package main

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/hashicorp/hcl/v2"
	"github.com/hashicorp/hcl/v2/hclparse"
	"gopkg.in/yaml.v3"
)

type InfrastructureIssue struct {
	FilePath    string `json:"file_path"`
	LineNumber  int    `json:"line_number"`
	IssueType   string `json:"issue_type"`
	Severity    string `json:"severity"`
	Description string `json:"description"`
	Rule        string `json:"rule"`
}

type InfrastructureMetrics struct {
	TotalFiles      int            `json:"total_files"`
	TerraformFiles  int            `json:"terraform_files"`
	KubernetesFiles int            `json:"kubernetes_files"`
	DockerFiles     int            `json:"docker_files"`
	Issues          []InfrastructureIssue `json:"issues"`
}

type InfrastructureAnalyzer struct {
	rootPath string
	issues   []InfrastructureIssue
	metrics  InfrastructureMetrics
}

func NewInfrastructureAnalyzer(rootPath string) *InfrastructureAnalyzer {
	return &InfrastructureAnalyzer{
		rootPath: rootPath,
		issues:   make([]InfrastructureIssue, 0),
		metrics:  InfrastructureMetrics{},
	}
}

func (ia *InfrastructureAnalyzer) AnalyzeInfrastructure() (*InfrastructureMetrics, error) {
	fmt.Printf("🔍 Starting infrastructure analysis of %s\n", ia.rootPath)

	err := filepath.WalkDir(ia.rootPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		if d.IsDir() {
			// Skip common non-infrastructure directories
			if shouldSkipDirectory(d.Name()) {
				return filepath.SkipDir
			}
			return nil
		}

		ia.metrics.TotalFiles++
		fileExt := strings.ToLower(filepath.Ext(path))
		fileName := strings.ToLower(d.Name())

		switch {
		case fileExt == ".tf" || fileExt == ".tf.json":
			ia.metrics.TerraformFiles++
			return ia.analyzeTerraformFile(path)
		case fileExt == ".yaml" || fileExt == ".yml":
			if strings.Contains(path, "k8s") || strings.Contains(path, "kubernetes") {
				ia.metrics.KubernetesFiles++
				return ia.analyzeKubernetesFile(path)
			}
		case fileName == "dockerfile" || fileName == "docker-compose.yml" || fileName == "docker-compose.yaml":
			ia.metrics.DockerFiles++
			return ia.analyzeDockerFile(path)
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking directory: %w", err)
	}

	ia.metrics.Issues = ia.issues
	return &ia.metrics, nil
}

func shouldSkipDirectory(dirName string) bool {
	skipDirs := []string{".git", ".svn", "node_modules", ".venv", "venv", "__pycache__", ".terraform"}
	for _, skip := range skipDirs {
		if dirName == skip {
			return true
		}
	}
	return false
}

func (ia *InfrastructureAnalyzer) analyzeTerraformFile(filePath string) error {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file %s: %w", filePath, err)
	}

	parser := hclparse.NewParser()
	_, diags := parser.ParseHCL(content, filePath)
	if diags.HasErrors() {
		ia.addIssue(filePath, 1, "terraform_syntax", "high", "Terraform syntax error", "TF_SYNTAX_ERROR")
		return nil
	}

	contentStr := string(content)
	lines := strings.Split(contentStr, "\n")

	// Check for common Terraform issues
	for i, line := range lines {
		lineNum := i + 1
		trimmedLine := strings.TrimSpace(line)

		// Check for hardcoded secrets
		if strings.Contains(trimmedLine, "password") && strings.Contains(trimmedLine, "=") {
			if !strings.Contains(trimmedLine, "var.") && !strings.Contains(trimmedLine, "data.") {
				ia.addIssue(filePath, lineNum, "hardcoded_secret", "critical", 
					"Potential hardcoded password detected", "TF_HARDCODED_SECRET")
			}
		}

		// Check for unencrypted storage
		if strings.Contains(trimmedLine, "encryption_key") && strings.Contains(trimmedLine, "= \"\"") {
			ia.addIssue(filePath, lineNum, "unencrypted_storage", "high",
				"Unencrypted storage detected", "TF_UNENCRYPTED_STORAGE")
		}

		// Check for public security groups
		if strings.Contains(trimmedLine, "0.0.0.0/0") {
			ia.addIssue(filePath, lineNum, "open_security_group", "critical",
				"Open security group (0.0.0.0/0) detected", "TF_OPEN_SECURITY_GROUP")
		}

		// Check for missing tags
		if strings.Contains(trimmedLine, "resource") && !strings.Contains(contentStr, "tags") {
			ia.addIssue(filePath, lineNum, "missing_tags", "medium",
				"Resource missing tags for cost allocation", "TF_MISSING_TAGS")
		}
	}

	return nil
}

func (ia *InfrastructureAnalyzer) analyzeKubernetesFile(filePath string) error {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file %s: %w", filePath, err)
	}

	var kubeConfig map[string]interface{}
	err = yaml.Unmarshal(content, &kubeConfig)
	if err != nil {
		ia.addIssue(filePath, 1, "kubernetes_syntax", "high", "Kubernetes YAML syntax error", "K8S_SYNTAX_ERROR")
		return nil
	}

	// Check for Kubernetes security issues
	if kind, ok := kubeConfig["kind"].(string); ok {
		switch kind {
		case "Pod", "Deployment", "StatefulSet":
			ia.analyzeWorkloadSecurity(filePath, kubeConfig)
		case "Service":
			ia.analyzeServiceSecurity(filePath, kubeConfig)
		case "ConfigMap", "Secret":
			ia.analyzeConfigSecurity(filePath, kubeConfig)
		}
	}

	return nil
}

func (ia *InfrastructureAnalyzer) analyzeWorkloadSecurity(filePath string, config map[string]interface{}) {
	spec, ok := config["spec"].(map[string]interface{})
	if !ok {
		return
	}

	// Check for privileged containers
	if containers, ok := spec["containers"].([]interface{}); ok {
		for _, container := range containers {
			if containerMap, ok := container.(map[string]interface{}); ok {
				if securityContext, ok := containerMap["securityContext"].(map[string]interface{}); ok {
					if privileged, ok := securityContext["privileged"].(bool); ok && privileged {
						ia.addIssue(filePath, 1, "privileged_container", "critical",
							"Privileged container detected", "K8S_PRIVILEGED_CONTAINER")
					}
				}

				// Check for running as root
				if securityContext, ok := containerMap["securityContext"].(map[string]interface{}); ok {
					if runAsUser, ok := securityContext["runAsUser"].(int); ok && runAsUser == 0 {
						ia.addIssue(filePath, 1, "run_as_root", "high",
							"Container running as root user", "K8S_RUN_AS_ROOT")
					}
				}
			}
		}
	}
}

func (ia *InfrastructureAnalyzer) analyzeServiceSecurity(filePath string, config map[string]interface{}) {
	spec, ok := config["spec"].(map[string]interface{})
	if !ok {
		return
	}

	// Check for NodePort services
	if serviceType, ok := spec["type"].(string); ok && serviceType == "NodePort" {
		ia.addIssue(filePath, 1, "nodeport_service", "medium",
			"NodePort service exposes cluster to external network", "K8S_NODEPORT_SERVICE")
	}
}

func (ia *InfrastructureAnalyzer) analyzeConfigSecurity(filePath string, config map[string]interface{}) {
	// Check for secrets in ConfigMaps
	if config["kind"] == "ConfigMap" {
		data, ok := config["data"].(map[string]interface{})
		if ok {
			for key := range data {
				if strings.Contains(strings.ToLower(key), "password") ||
					strings.Contains(strings.ToLower(key), "secret") ||
					strings.Contains(strings.ToLower(key), "key") {
					ia.addIssue(filePath, 1, "secret_in_configmap", "high",
						fmt.Sprintf("Potential secret '%s' found in ConfigMap", key), "K8S_SECRET_IN_CONFIGMAP")
				}
			}
		}
	}
}

func (ia *InfrastructureAnalyzer) analyzeDockerFile(filePath string) error {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file %s: %w", filePath, err)
	}

	lines := strings.Split(string(content), "\n")
	for i, line := range lines {
		lineNum := i + 1
		trimmedLine := strings.TrimSpace(line)

		// Check for running as root
		if strings.HasPrefix(trimmedLine, "USER") && !strings.Contains(trimmedLine, "root") {
			// This is good, but we should check if there's no USER instruction at all
		}

		// Check for adding sensitive files
		if strings.HasPrefix(trimmedLine, "ADD") || strings.HasPrefix(trimmedLine, "COPY") {
			if strings.Contains(trimmedLine, ".ssh") || strings.Contains(trimmedLine, ".aws") {
				ia.addIssue(filePath, lineNum, "copying_secrets", "critical",
					"Copying sensitive files into container", "DOCKER_COPYING_SECRETS")
			}
		}

		// Check for using latest tag
		if strings.Contains(trimmedLine, ":latest") {
			ia.addIssue(filePath, lineNum, "latest_tag", "medium",
				"Using 'latest' tag can lead to unpredictable builds", "DOCKER_LATEST_TAG")
		}
	}

	return nil
}

func (ia *InfrastructureAnalyzer) addIssue(filePath, lineNumber int, issueType, severity, description, rule string) {
	relativePath, _ := filepath.Rel(ia.rootPath, filePath)
	issue := InfrastructureIssue{
		FilePath:    relativePath,
		LineNumber:  lineNumber,
		IssueType:   issueType,
		Severity:    severity,
		Description: description,
		Rule:        rule,
	}
	ia.issues = append(ia.issues, issue)
}

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Usage: go run main.go <infrastructure_path>")
		os.Exit(1)
	}

	rootPath := os.Args[1]
	analyzer := NewInfrastructureAnalyzer(rootPath)

	metrics, err := analyzer.AnalyzeInfrastructure()
	if err != nil {
		log.Fatalf("Error analyzing infrastructure: %v", err)
	}

	// Generate summary
	summary := map[string]interface{}{
		"analysis_timestamp": time.Now().Format(time.RFC3339),
		"summary": map[string]interface{}{
			"total_files":       metrics.TotalFiles,
			"terraform_files":   metrics.TerraformFiles,
			"kubernetes_files":  metrics.KubernetesFiles,
			"docker_files":      metrics.DockerFiles,
			"total_issues":      len(metrics.Issues),
		},
		"issues": metrics.Issues,
		"recommendations": generateRecommendations(metrics),
	}

	jsonOutput, err := json.MarshalIndent(summary, "", "  ")
	if err != nil {
		log.Fatalf("Error marshaling JSON: %v", err)
	}

	fmt.Println(string(jsonOutput))
}

func generateRecommendations(metrics *InfrastructureMetrics) []string {
	var recommendations []string

	criticalIssues := 0
	highIssues := 0

	for _, issue := range metrics.Issues {
		switch issue.Severity {
		case "critical":
			criticalIssues++
		case "high":
			highIssues++
		}
	}

	if criticalIssues > 0 {
		recommendations = append(recommendations, fmt.Sprintf("URGENT: Fix %d critical security issues", criticalIssues))
	}

	if highIssues > 0 {
		recommendations = append(recommendations, fmt.Sprintf("Address %d high-priority security issues", highIssues))
	}

	if metrics.TerraformFiles > 0 {
		recommendations = append(recommendations, "Implement Terraform state locking and remote state management")
	}

	if metrics.KubernetesFiles > 0 {
		recommendations = append(recommendations, "Use network policies and RBAC for Kubernetes security")
	}

	if metrics.DockerFiles > 0 {
		recommendations = append(recommendations, "Use multi-stage builds and non-root users in Docker containers")
	}

	if len(recommendations) == 0 {
		recommendations = append(recommendations, "Excellent infrastructure security posture!")
	}

	return recommendations
}
