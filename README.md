# LLM Observability Platform

A comprehensive Python-based observability platform for Large Language Models (LLMs) with chat interface, container orchestration, monitoring, and advanced analytics capabilities.

## Features

- **Interactive Chat Interface**: Streamlit-based web UI for chatting with LLM models
- **Model Selection**: Support for multiple LLM categories and models from Cloudflare
- **Conversation History**: Persistent chat history with user sessions
- **Deep Analysis**: Advanced emotional and meta-analysis of conversations and LLM responses
- **Container Orchestration**: Docker-based deployment with automatic scaling
- **Observability Suite**: Comprehensive monitoring for LLM performance, usage metrics, and behavioral analytics
- **Health Monitoring**: Real-time health checks and alerting for LLM services
- **Performance Tracking**: Detailed metrics on response times, token usage, and model performance
- **Multi-Cloud Support**: Deployment options for Fly.io and Render

## Project Structure

```
llm-chatbot-python/
├── service/llm_chat_app/          # Main application
│   ├── app/                       # Streamlit web interface
│   ├── core/                      # Core business logic
│   ├── worker/                    # Background workers and workflows
│   └── requirements.txt           # Python dependencies
├── infrastructure/                # Infrastructure components
│   ├── orchestrator/              # Container management
│   └── observability_platform/    # Monitoring and logging
├── deployment/                    # Deployment configurations
├── docs/                          # Documentation
└── shared/                        # Shared utilities
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd llm-chatbot-python
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
cd service/llm_chat_app
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.llm_chat_app.example .env.llm_chat_app
# Edit .env.llm_chat_app with your API keys and configuration
```

### Running the Application

1. Start the Streamlit app:
```bash
cd service/llm_chat_app
streamlit run app/streamlit_app.py
```

2. Open your browser and navigate to `http://localhost:8501`

## Configuration

### Environment Variables

Key environment variables in `.env.llm_chat_app`:

- `CLOUDFLARE_API_TOKEN`: Your Cloudflare API token
- `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare account ID
- `NEO4J_URI`: Neo4j database connection string
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password

### Docker Deployment

1. Build the container:
```bash
docker build -t llm-chatbot .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

## Development

### Code Style

This project follows strict linting rules:
- Python: Pylint with snake_case naming
- YAML: 2-space indentation, single quotes
- Line length: 120 characters max

### Git Workflow

All changes are automatically committed with timestamps:
```bash
git add .
git commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
git push
```

## Architecture

- **Streamlit Frontend**: Web interface for user interactions
- **AI Client**: Handles communication with LLM APIs
- **Neo4j Database**: Stores conversation history and user data
- **Container Manager**: Orchestrates Docker containers
- **Workers**: Background processing for deployment and maintenance

## Deployment Options

### Fly.io
```bash
# Deploy to Fly.io
cd service/llm_chat_app
fly launch
```

### Render
```bash
# Deploy to Render (automated via workflow)
# See: worker/workflows/render_deploy_workflow.py
```

### Kubernetes
```bash
# Deploy to Kubernetes
cd deployment/kubernetes
kubectl apply -f .
```

## Monitoring

The application includes comprehensive observability:
- **Loki**: Log aggregation
- **Health Checks**: Container and service health monitoring
- **Metrics**: Performance and usage tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all linting rules pass
5. Submit a pull request

## Important Links

**Connect with Scaibu:**
- **Email**: chief.stategist.j@gmail.com
- **Medium**: https://medium.com/@scaibu
- **LinkedIn**: https://www.linkedin.com/in/chiefj/
- **Twitter**: https://x.com/ChiefErj
- **Instagram**: https://www.instagram.com/chief._.jaydeep/
- **Discord Server**: https://discord.com/invite/FzZPnjZa
- **Website**: https://scaibu.lovable.app/
- **Service Booking**: https://topmate.io/jaydeep_wagh/1194002
- **Contact**: 9664920749

## License

[Add your license information here]

## Support

For issues and questions:
- Check the documentation in `docs/`
- Review the architecture overview in `docs/architecture/overview.md`
- Check deployment guides in `docs/deployment/`
