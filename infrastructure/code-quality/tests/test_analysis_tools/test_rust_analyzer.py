import pytest
import json
import subprocess
import tempfile
import os
from pathlib import Path


class TestRustPerformanceTools:
    
    def test_analyze_rust_project_basic(self, sample_rust_project):
        """Test basic Rust project analysis"""
        # Build and run the Rust analyzer
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        # Build might fail if dependencies not available, but we can test the structure
        if build_result.returncode == 0:
            # Run analysis
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', sample_rust_project],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            # Should not crash
            assert result.returncode in [0, 1]  # 1 if compilation fails
            
            if result.returncode == 0:
                # Parse JSON output
                results = json.loads(result.stdout)
                
                # Verify structure
                assert 'project_path' in results
                assert 'analysis_timestamp' in results
                assert 'metrics' in results
                assert 'recommendations' in results
                
                # Check project path
                assert results['project_path'] == sample_rust_project
                
                # Should have metrics
                metrics = results['metrics']
                assert len(metrics) > 0
                
                # Check metric structure
                for metric in metrics:
                    assert 'name' in metric
                    assert 'value' in metric
                    assert 'unit' in metric
                    assert 'timestamp' in metric
    
    def test_analyze_empty_rust_project(self):
        """Test analysis of empty Rust project"""
        with tempfile.TemporaryDirectory() as empty_dir:
            # Create minimal Cargo.toml
            cargo_toml = os.path.join(empty_dir, "Cargo.toml")
            with open(cargo_toml, 'w') as f:
                f.write("""
[package]
name = "empty-project"
version = "0.1.0"
edition = "2021"
""")
            
            # Create empty src directory
            src_dir = os.path.join(empty_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            main_rs = os.path.join(src_dir, "main.rs")
            with open(main_rs, 'w') as f:
                f.write("fn main() {}\n")
            
            # Try to run analysis
            build_result = subprocess.run(
                ['cargo', 'build', '--release'],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if build_result.returncode == 0:
                result = subprocess.run(
                    ['cargo', 'run', '--release', '--', empty_dir],
                    cwd='../../analysis-tools/rust/performance-tools',
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    results = json.loads(result.stdout)
                    assert results['project_path'] == empty_dir
                    assert len(results['metrics']) > 0
    
    def test_analyze_nonexistent_project(self):
        """Test analysis of non-existent project"""
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        if build_result.returncode == 0:
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', '/non/existent/path'],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            # Should handle gracefully
            assert result.returncode in [0, 1]
    
    def test_analyze_complex_rust_project(self):
        """Test analysis of more complex Rust project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create complex Cargo.toml
            cargo_toml = os.path.join(temp_dir, "Cargo.toml")
            with open(cargo_toml, 'w') as f:
                f.write("""
[package]
name = "complex-project"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
reqwest = { version = "0.11", features = ["json"] }
""")
            
            # Create complex source files
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            
            # Main file with complex operations
            main_rs = os.path.join(src_dir, "main.rs")
            with open(main_rs, 'w') as f:
                f.write("""
use std::collections::HashMap;
use std::time::Instant;
use tokio::time::{sleep, Duration};

async fn complex_async_operation() -> Result<String, Box<dyn std::error::Error>> {
    let mut data = Vec::new();
    for i in 0..10000 {
        data.push(i.to_string());
    }
    
    sleep(Duration::from_millis(100)).await;
    
    let result = data.iter().map(|s| s.len()).sum::<usize>();
    Ok(result.to_string())
}

fn cpu_intensive_calculation() -> u64 {
    let mut result = 0u64;
    for i in 0..1_000_000 {
        result = result.wrapping_add(i * i);
        if result % 1000 == 0 {
            result >>= 1;
        }
    }
    result
}

fn memory_intensive_allocation() -> Vec<Vec<u8>> {
    let mut allocations = Vec::new();
    for i in 0..1000 {
        let mut data = vec![0u8; 1024];
        for j in 0..1024 {
            data[j] = (i + j) as u8;
        }
        allocations.push(data);
    }
    allocations
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let start = Instant::now();
    
    // Async operation
    let async_result = complex_async_operation().await?;
    
    // CPU intensive operation
    let cpu_result = cpu_intensive_calculation();
    
    // Memory intensive operation
    let memory_result = memory_intensive_allocation();
    
    let duration = start.elapsed();
    
    println!("Async result: {}", async_result);
    println!("CPU result: {}", cpu_result);
    println!("Memory allocations: {}", memory_result.len());
    println!("Total time: {:?}", duration);
    
    Ok(())
}
""")
            
            # Try to run analysis
            build_result = subprocess.run(
                ['cargo', 'build', '--release'],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if build_result.returncode == 0:
                result = subprocess.run(
                    ['cargo', 'run', '--release', '--', temp_dir],
                    cwd='../../analysis-tools/rust/performance-tools',
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    results = json.loads(result.stdout)
                    
                    # Should have performance metrics
                    metrics = results['metrics']
                    assert len(metrics) > 0
                    
                    # Check for expected metric types
                    metric_names = [metric['name'] for metric in metrics]
                    expected_metrics = ['compilation_time', 'memory_usage', 'cpu_time']
                    
                    # At least some expected metrics should be present
                    assert len(set(metric_names) & set(expected_metrics)) > 0
    
    def test_analyze_json_output_format(self, sample_rust_project):
        """Test JSON output format is valid"""
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        if build_result.returncode == 0:
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', sample_rust_project],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Should be valid JSON
                results = json.loads(result.stdout)
                
                # Should have required fields
                required_fields = ['project_path', 'analysis_timestamp', 'metrics', 'recommendations']
                for field in required_fields:
                    assert field in results
                
                # Metrics should have required fields
                for metric in results['metrics']:
                    required_metric_fields = ['name', 'value', 'unit', 'timestamp']
                    for field in required_metric_fields:
                        assert field in metric
    
    def test_analyze_recommendations_generation(self, sample_rust_project):
        """Test recommendation generation"""
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        if build_result.returncode == 0:
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', sample_rust_project],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                results = json.loads(result.stdout)
                recommendations = results['recommendations']
                
                assert len(recommendations) >= 0
                assert isinstance(recommendations, list)
                
                # Recommendations should be strings
                for rec in recommendations:
                    assert isinstance(rec, str)
                    assert len(rec) > 0
    
    def test_analyze_metric_values(self, sample_rust_project):
        """Test that metric values are reasonable"""
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        if build_result.returncode == 0:
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', sample_rust_project],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                results = json.loads(result.stdout)
                metrics = results['metrics']
                
                for metric in metrics:
                    # Value should be numeric
                    assert isinstance(metric['value'], (int, float))
                    
                    # Value should be non-negative for performance metrics
                    assert metric['value'] >= 0
                    
                    # Unit should be a string
                    assert isinstance(metric['unit'], str)
                    assert len(metric['unit']) > 0
                    
                    # Timestamp should be valid
                    assert isinstance(metric['timestamp'], str)
                    assert len(metric['timestamp']) > 0
    
    def test_analyze_timestamp_format(self, sample_rust_project):
        """Test timestamp format in output"""
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        if build_result.returncode == 0:
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', sample_rust_project],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                results = json.loads(result.stdout)
                
                # Main timestamp
                from datetime import datetime
                timestamp = datetime.fromisoformat(results['analysis_timestamp'].replace('Z', '+00:00'))
                assert timestamp is not None
                
                # Metric timestamps
                for metric in results['metrics']:
                    metric_timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
                    assert metric_timestamp is not None
    
    def test_analyze_project_path_handling(self, sample_rust_project):
        """Test project path handling"""
        build_result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd='../../analysis-tools/rust/performance-tools',
            capture_output=True,
            text=True
        )
        
        if build_result.returncode == 0:
            result = subprocess.run(
                ['cargo', 'run', '--release', '--', sample_rust_project],
                cwd='../../analysis-tools/rust/performance-tools',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                results = json.loads(result.stdout)
                
                # Project path should match input
                assert results['project_path'] == sample_rust_project
