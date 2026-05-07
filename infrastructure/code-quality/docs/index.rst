SonarQube Code Quality Infrastructure Documentation
=================================================

Welcome to the SonarQube Code Quality Infrastructure documentation. This comprehensive system provides automated code quality analysis, reporting, and monitoring capabilities.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   architecture
   installation
   quickstart
   api
   testing
   deployment
   cicd
   troubleshooting
   contributing

Overview
--------

The SonarQube Code Quality Infrastructure is a production-ready system that provides:

* **Automated Code Analysis**: Multi-language support (Python, Go, Rust)
* **Quality Gate Enforcement**: Configurable quality thresholds
* **Comprehensive Reporting**: Detailed metrics and insights
* **CI/CD Integration**: Seamless pipeline integration
* **Security Scanning**: Built-in vulnerability detection
* **Performance Monitoring**: Resource usage tracking

Key Features
------------

* **Domain-Driven Design**: Clean, maintainable architecture
* **Microservices Architecture**: Scalable and resilient
* **Docker Support**: Containerized deployment
* **Production-Ready**: Comprehensive testing and monitoring

Architecture
-----------

The system follows a hexagonal architecture pattern with clear separation of concerns:

* **Domain Layer**: Core business logic and entities
* **Application Layer**: Use cases and orchestration
* **Infrastructure Layer**: External integrations and persistence
* **Adapters Layer**: External interfaces and APIs

Getting Started
---------------

1. **Installation**: See :doc:`installation` for setup instructions
2. **Quick Start**: Follow the :doc:`quickstart` guide
3. **API Reference**: Check the :doc:`api` documentation
4. **Testing**: Review the :doc:`testing` guidelines
5. **Deployment**: See :doc:`deployment` instructions

CI/CD Pipeline
--------------

The system includes a comprehensive CI/CD pipeline that:

* Runs automated tests on every push/PR
* Generates coverage reports with Codecov
* Creates Allure test reports
* Builds and deploys Docker images
* Performs security scanning
* Generates documentation
* Enforces quality gates

For detailed CI/CD information, see :doc:`cicd`.

Testing Strategy
---------------

We maintain comprehensive test coverage across multiple categories:

* **Unit Tests**: Domain and application logic
* **Integration Tests**: Database and external services
* **Critical Tests**: Production-breaking scenarios
* **Security Tests**: Vulnerability scanning
* **Performance Tests**: Load and memory testing

See :doc:`testing` for detailed testing guidelines.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
