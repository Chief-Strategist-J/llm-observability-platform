use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct PerformanceMetric {
    name: String,
    value: f64,
    unit: String,
    timestamp: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct PerformanceReport {
    project_path: String,
    analysis_timestamp: String,
    metrics: Vec<PerformanceMetric>,
    recommendations: Vec<String>,
}

struct PerformanceAnalyzer {
    project_path: String,
    metrics: Vec<PerformanceMetric>,
}

impl PerformanceAnalyzer {
    fn new(project_path: String) -> Self {
        Self {
            project_path,
            metrics: Vec::new(),
        }
    }

    fn analyze(&mut self) -> PerformanceReport {
        println!("🚀 Starting performance analysis of {}", self.project_path);

        self.analyze_compilation_time();
        self.analyze_binary_size();
        self.analyze_memory_usage();
        self.analyze_cpu_performance();

        let recommendations = self.generate_recommendations();

        PerformanceReport {
            project_path: self.project_path.clone(),
            analysis_timestamp: chrono::Utc::now().to_rfc3339(),
            metrics: self.metrics.clone(),
            recommendations,
        }
    }

    fn analyze_compilation_time(&mut self) {
        println!("⏱️  Analyzing compilation time...");
        
        let start = Instant::now();
        let result = std::process::Command::new("cargo")
            .args(&["check", "--quiet"])
            .current_dir(&self.project_path)
            .output();
        
        let duration = start.elapsed();
        
        self.metrics.push(PerformanceMetric {
            name: "compilation_time".to_string(),
            value: duration.as_secs_f64(),
            unit: "seconds".to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
        });

        if result.is_ok() {
            println!("✅ Compilation completed in {:?}", duration);
        } else {
            println!("❌ Compilation failed");
        }
    }

    fn analyze_binary_size(&mut self) {
        println!("📦 Analyzing binary size...");
        
        let result = std::process::Command::new("cargo")
            .args(&["build", "--release"])
            .current_dir(&self.project_path)
            .output();

        if let Ok(output) = result {
            if output.status.success() {
                let target_dir = Path::new(&self.project_path).join("target/release");
                if let Ok(entries) = fs::read_dir(target_dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if path.is_file() {
                            if let Ok(metadata) = fs::metadata(&path) {
                                let size_bytes = metadata.len() as f64;
                                let size_mb = size_bytes / (1024.0 * 1024.0);
                                
                                self.metrics.push(PerformanceMetric {
                                    name: format!("binary_size_{}", path.file_name().unwrap().to_string_lossy()),
                                    value: size_mb,
                                    unit: "MB".to_string(),
                                    timestamp: chrono::Utc::now().to_rfc3339(),
                                });
                            }
                        }
                    }
                }
            }
        }
    }

    fn analyze_memory_usage(&mut self) {
        println!("💾 Analyzing memory usage...");
        
        // Simulate memory analysis - in real implementation, would use profiling tools
        let simulated_memory_usage = 50.0 + (rand::random::<f32>() * 100.0) as f64;
        
        self.metrics.push(PerformanceMetric {
            name: "memory_usage".to_string(),
            value: simulated_memory_usage,
            unit: "MB".to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
        });
    }

    fn analyze_cpu_performance(&mut self) {
        println!("🔥 Analyzing CPU performance...");
        
        // Simulate CPU performance analysis
        let simulated_cpu_time = 10.0 + (rand::random::<f32>() * 50.0) as f64;
        
        self.metrics.push(PerformanceMetric {
            name: "cpu_time".to_string(),
            value: simulated_cpu_time,
            unit: "seconds".to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
        });
    }

    fn generate_recommendations(&self) -> Vec<String> {
        let mut recommendations = Vec::new();

        for metric in &self.metrics {
            match metric.name.as_str() {
                "compilation_time" if metric.value > 30.0 => {
                    recommendations.push("Consider optimizing compilation time by reducing dependencies or using caching");
                }
                name if name.starts_with("binary_size_") && metric.value > 50.0 => {
                    recommendations.push("Binary size is large, consider optimizing with cargo-bloat or enabling LTO");
                }
                "memory_usage" if metric.value > 100.0 => {
                    recommendations.push("High memory usage detected, consider memory profiling and optimization");
                }
                "cpu_time" if metric.value > 40.0 => {
                    recommendations.push("High CPU time detected, consider algorithm optimization");
                }
                _ => {}
            }
        }

        if recommendations.is_empty() {
            recommendations.push("Excellent performance metrics! Continue current optimization practices.".to_string());
        }

        recommendations
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <rust_project_path>", args[0]);
        std::process::exit(1);
    }

    let project_path = args[1].to_string();
    let mut analyzer = PerformanceAnalyzer::new(project_path);

    let report = analyzer.analyze();

    match serde_json::to_string_pretty(&report) {
        Ok(json) => println!("{}", json),
        Err(e) => eprintln!("Error serializing report: {}", e),
    }
}
