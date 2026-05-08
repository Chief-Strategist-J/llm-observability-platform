import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
from domain.models.project import Project, ProjectStatus, QualityGateStatus
from infrastructure.persistence.postgresql_analysis_repository import PostgreSQLAnalysisRepository
from infrastructure.persistence.postgresql_project_repository import PostgreSQLProjectRepository
from infrastructure.sonarqube.sonarqube_service_adapter import SonarQubeServiceAdapter


@pytest.fixture
def sample_project():
    return Project(
        key="test-project",
        name="Test Project",
        description="A test project",
        status=ProjectStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        last_analysis_at=None,
        quality_gate_status=QualityGateStatus.NONE,
        languages=["python", "javascript"]
    )


@pytest.fixture
def sample_analysis():
    return Analysis(
        id="test-analysis-123",
        project_key="test-project",
        branch="main",
        commit_hash="abc123def456789012345678901234567890abcd",
        status=AnalysisStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        issues=[
            Issue(
                key="ISSUE-1",
                type=IssueType.BUG,
                severity=Severity.MAJOR,
                message="Test issue",
                file_path="test.py",
                line_number=10,
                rule="TEST_RULE",
                status="OPEN"
            )
        ],
        metrics=[
            Metric(
                name="coverage",
                value=85.5,
                formatted_value="85.5%"
            )
        ]
    )


@pytest.fixture
def mock_sonarqube_service():
    service = Mock(spec=SonarQubeServiceAdapter)
    service.create_project.return_value = True
    service.trigger_analysis.return_value = "task-123"
    service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
    service.get_analysis_results.return_value = None
    service.get_project_analyses.return_value = []
    service.get_project_quality_gate.return_value = "PASSED"
    return service


@pytest.fixture
def temp_database():
    """Mock database connection for testing"""
    # Use a mock connection instead of real PostgreSQL
    # This avoids database connection issues during testing
    import sqlite3
    import tempfile
    
    # Create temporary SQLite database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    conn = sqlite3.connect(temp_db.name)
    
    # Create basic schema for testing
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE projects (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_analysis_at TEXT,
            quality_gate_status TEXT NOT NULL,
            languages TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE analyses (
            id TEXT PRIMARY KEY,
            project_key TEXT NOT NULL,
            branch TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            summary TEXT,
            quality_score REAL,
            ready_for_merge BOOLEAN
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE issues (
            key TEXT PRIMARY KEY,
            analysis_id TEXT NOT NULL,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            file_path TEXT NOT NULL,
            line_number INTEGER NOT NULL,
            rule TEXT NOT NULL,
            status TEXT NOT NULL,
            is_blocking BOOLEAN NOT NULL,
            is_security_related BOOLEAN NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id TEXT NOT NULL,
            name TEXT NOT NULL,
            value REAL NOT NULL,
            formatted_value TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    
    yield conn
    
    # Cleanup
    conn.close()
    os.unlink(temp_db.name)


@pytest.fixture
def analysis_repository(temp_database):
    # Mock repository for testing with SQLite
    from unittest.mock import Mock
    from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
    
    repository = Mock()
    
    # Create different sample analyses for different scenarios
    running_analysis = Analysis(
        id="test-analysis",
        project_key="test-project",
        branch="main",
        commit_hash="abc123def456789012345678901234567890abcd",
        status=AnalysisStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
        issues=[],
        metrics=[]
    )
    
    completed_analysis = Analysis(
        id="test-analysis",
        project_key="test-project",
        branch="main",
        commit_hash="abc123def456789012345678901234567890abcd",
        status=AnalysisStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        issues=[],
        metrics=[
            Metric(
                name="coverage",
                value=85.0,
                formatted_value="85.0%"
            )
        ]
    )
    
    failed_analysis = Analysis(
        id="test-analysis",
        project_key="test-project",
        branch="main",
        commit_hash="abc123def456789012345678901234567890abcd",
        status=AnalysisStatus.FAILED,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        issues=[],
        metrics=[]
    )
    
    # Mock basic methods with dynamic return values
    repository.save = Mock()
    repository.find_by_id = Mock(return_value=running_analysis)
    repository.find_by_status = Mock(return_value=[running_analysis])
    repository.find_by_project = Mock(return_value=[running_analysis])
    repository.find_by_commit = Mock(return_value=None)  # No existing analysis
    
    # Store the different analyses for tests to use
    repository.running_analysis = running_analysis
    repository.completed_analysis = completed_analysis
    repository.failed_analysis = failed_analysis
    
    # Mock the save method to return the analysis ID
    def mock_save(analysis):
        return analysis.id
    repository.save.side_effect = mock_save
    
    return repository


@pytest.fixture
def project_repository(temp_database):
    # Mock repository for testing with SQLite
    from unittest.mock import Mock
    from domain.models.project import Project, ProjectStatus, QualityGateStatus
    
    repository = Mock()
    
    # Create sample project for testing
    sample_project = Project(
        key="test-project",
        name="Test Project",
        description="A test project",
        status=ProjectStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        last_analysis_at=datetime.now(timezone.utc),
        quality_gate_status=QualityGateStatus.NONE,
        languages=["python", "javascript"]
    )
    
    # Mock basic methods
    repository.save = Mock()
    repository.find_by_key = Mock(return_value=sample_project)
    repository.find_all = Mock(return_value=[sample_project])
    
    return repository


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample Python files for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample Python files
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0

def dangerous_function():
    eval("print('hello')")
    return True

class TestClass:
    def __init__(self):
        self.value = 42
    
    def method_with_issues(self):
        import os
        return os.system("ls")
""")
        
        # Create another file
        another_file = os.path.join(temp_dir, "another.py")
        with open(another_file, 'w') as f:
            f.write("""
def simple_function():
    return "hello world"

class AnotherClass:
    def method(self):
        return self.value if hasattr(self, 'value') else 0
""")
        
        yield temp_dir


@pytest.fixture
def sample_terraform_files():
    """Create temporary directory with Terraform files for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create main.tf with security issues
        main_tf = os.path.join(temp_dir, "main.tf")
        with open(main_tf, 'w') as f:
            f.write("""
resource "aws_security_group" "example" {
    name        = "example-sg"
    description = "Example security group"
    
    ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]  # Open to world
    }
    
    ingress {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]  # Open to world
    }
}

resource "aws_instance" "example" {
    ami           = "ami-12345678"
    instance_type = "t2.micro"
    
    root_block_device {
        encrypted = false  # Unencrypted storage
    }
}

resource "aws_db_instance" "example" {
    identifier     = "example-db"
    engine         = "mysql"
    instance_class = "db.t2.micro"
    
    username = "admin"
    password = "supersecretpassword123"  # Hardcoded password
    
    storage_encrypted = false
}
""")
        
        # Create variables.tf
        variables_tf = os.path.join(temp_dir, "variables.tf")
        with open(variables_tf, 'w') as f:
            f.write("""
variable "region" {
    description = "AWS region"
    type        = string
    default     = "us-west-2"
}

variable "instance_type" {
    description = "EC2 instance type"
    type        = string
    default     = "t2.micro"
}
""")
        
        yield temp_dir


@pytest.fixture
def sample_kubernetes_files():
    """Create temporary directory with Kubernetes files for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create deployment.yaml with security issues
        deployment_yaml = os.path.join(temp_dir, "deployment.yaml")
        with open(deployment_yaml, 'w') as f:
            f.write("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: test-container
        image: nginx:latest
        securityContext:
          privileged: true  # Privileged container
          runAsUser: 0       # Running as root
        ports:
        - containerPort: 80
        env:
        - name: DATABASE_PASSWORD
          value: "secretpassword"  # Hardcoded secret
---
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  type: NodePort  # Exposes service externally
  selector:
    app: test-app
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
""")
        
        # Create configmap.yaml
        configmap_yaml = os.path.join(temp_dir, "configmap.yaml")
        with open(configmap_yaml, 'w') as f:
            f.write("""
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
data:
  database_host: "localhost"
  database_user: "admin"
  database_password: "admin123"  # Secret in ConfigMap
  api_key: "sk-1234567890abcdef"  # API key in ConfigMap
""")
        
        yield temp_dir


@pytest.fixture
def sample_rust_project():
    """Create temporary directory with Rust project for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create Cargo.toml
        cargo_toml = os.path.join(temp_dir, "Cargo.toml")
        with open(cargo_toml, 'w') as f:
            f.write("""
[package]
name = "test-project"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }
""")
        
        # Create src/main.rs
        src_dir = os.path.join(temp_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        main_rs = os.path.join(src_dir, "main.rs")
        with open(main_rs, 'w') as f:
            f.write("""
use std::collections::HashMap;
use std::time::Instant;

fn complex_calculation(data: &Vec<i32>) -> i32 {
    let mut result = 0;
    for i in 0..data.len() {
        for j in 0..data.len() {
            result += data[i] * data[j];
            if result > 1000000 {
                break;
            }
        }
    }
    result
}

fn memory_intensive_operation() -> Vec<String> {
    let mut data = Vec::new();
    for i in 0..100000 {
        data.push(format!("Item {}", i));
    }
    data
}

fn main() {
    let start = Instant::now();
    let data = vec![1, 2, 3, 4, 5];
    let result = complex_calculation(&data);
    let memory_data = memory_intensive_operation();
    let duration = start.elapsed();
    
    println!("Result: {}, Duration: {:?}, Memory items: {}", 
             result, duration, memory_data.len());
}
""")
        
        yield temp_dir
