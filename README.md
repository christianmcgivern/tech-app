# AI-Powered Technician Workflow System

A real-time AI system for managing technician workflows using OpenAI's Realtime API.

## Features

- Real-time AI interactions using WebSocket connections
- Work order management with priority queuing
- Location tracking and validation
- Audio input/output handling
- Comprehensive error handling
- Performance monitoring and metrics collection

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tech-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure:
```bash
cp config/.env.example .env
# Edit .env with your settings
```

## Configuration

The system uses both environment variables and JSON configuration:

1. Environment Variables (`.env`):
- `OPENAI_API_KEY`: Your OpenAI API key
- `LOG_LEVEL`: Logging level (default: INFO)

2. JSON Configuration (`config/config.json`):
- WebSocket settings
- Audio configuration
- Logging format
- Technician parameters

## Usage

1. Start the application:
```bash
python -m src.main
```

2. Monitor the application:
```bash
python -m src.utils.monitoring --summary
```

## Testing

Run the test suite:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/core/  # Core functionality tests
pytest tests/utils/  # Utility tests
pytest -k "work_order"  # Work order specific tests
```

### Test Coverage

Generate coverage report:
```bash
pytest --cov=src tests/
```

## Monitoring

The system includes comprehensive monitoring capabilities:

1. API Metrics:
- Call duration tracking
- Error rate monitoring
- Rate limit tracking

2. Performance Monitoring:
```python
from src.utils.monitoring import MetricsCollector

metrics = MetricsCollector()
summary = metrics.get_api_metrics_summary(window_minutes=60)
print(f"API Performance: {summary}")
```

3. Rate Limits:
```python
limits = metrics.get_rate_limit_status()
print(f"Current Rate Limits: {limits}")
```

## Project Structure

```
src/
├── core/           # Core functionality
│   ├── websocket.py
│   ├── audio.py
│   └── work_order.py
├── utils/          # Utility modules
│   ├── config.py
│   ├── logging.py
│   └── monitoring.py
└── main.py         # Application entry point

tests/              # Test suite
├── core/           # Core tests
└── utils/          # Utility tests

config/             # Configuration files
└── config.json
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[License information]
