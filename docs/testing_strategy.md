# Testing Strategy

## Overview
This document outlines the comprehensive testing strategy for the technician dispatch application, focusing on test organization, coverage requirements, and best practices for testing async operations and WebSocket communication.

## Test Organization

### Directory Structure
```
tests/
├── conftest.py           # Shared fixtures and configuration
├── core/                 # Core module tests
│   ├── test_audio.py    # Audio processing tests
│   ├── test_event_handlers.py  # Event system tests
│   ├── test_technician.py     # Technician session tests
│   ├── test_websocket.py     # WebSocket client tests
│   └── test_work_order.py    # Work order tests
└── utils/                # Utility module tests
    └── test_config.py    # Configuration tests
```

### Test Categories

1. Unit Tests
   - Individual component functionality
   - Isolated behavior verification
   - Mock external dependencies
   - Fast execution
   - High coverage requirements (95%+)

2. Integration Tests
   - Component interaction testing
   - Real dependency usage where practical
   - End-to-end workflows
   - WebSocket communication
   - Event handling chains

3. Async Tests
   - WebSocket operations
   - Event handling
   - Concurrent operations
   - Timeout handling
   - Connection management

4. Performance Tests
   - Response time verification
   - Resource usage monitoring
   - Concurrent connection handling
   - Message throughput
   - Queue performance

## Test Configuration

### Base Configuration
```python
# tests/conftest.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

@pytest_asyncio.fixture
async def config():
    """Provide test configuration."""
    return Config(
        api_key="test-key",
        model_version="gpt-4o-realtime-preview-2024-12-17",
        websocket_url="wss://test.openai.com/v1/audio/speech",
        ping_interval=30,
        ping_timeout=10
    )

@pytest_asyncio.fixture
async def websocket_client(config):
    """Provide WebSocket client fixture."""
    client = WebSocketClient(config)
    yield client
    if client.is_connected:
        await client.disconnect()

@pytest_asyncio.fixture
async def mock_websocket():
    """Provide mock WebSocket connection."""
    mock = AsyncMock()
    mock.send = AsyncMock()
    mock.recv = AsyncMock()
    mock.close = AsyncMock()
    return mock
```

### Test Environment
```python
# tests/test_env.py
import os
import pytest
from dotenv import load_dotenv

def pytest_configure(config):
    """Configure test environment."""
    load_dotenv(".env.test")
    os.environ["TESTING"] = "1"
    os.environ["API_KEY"] = "sk-test-key"
```

## Testing Guidelines

### Unit Testing
1. Test individual components in isolation
2. Mock external dependencies
3. Verify edge cases
4. Test error handling
5. Validate input/output

Example:
```python
@pytest.mark.asyncio
async def test_websocket_connection(websocket_client, mock_websocket, mocker):
    """Test WebSocket connection establishment."""
    mocker.patch("websockets.connect", return_value=mock_websocket)
    
    connected = await websocket_client.connect()
    assert connected
    assert websocket_client.is_connected
    
    # Verify connection headers
    connect_call = mocker.patch.call_args
    assert "Authorization" in connect_call.kwargs["extra_headers"]
    assert "OpenAI-Beta" in connect_call.kwargs["extra_headers"]
```

### Integration Testing
1. Test component interactions
2. Verify workflow completion
3. Test state transitions
4. Validate event chains
5. Check data consistency

Example:
```python
@pytest.mark.asyncio
async def test_work_order_workflow(work_order_manager, technician_session):
    """Test complete work order workflow."""
    # Create and assign order
    order = await work_order_manager.create_order(
        "WO001", "Test Order", WorkOrderPriority.HIGH
    )
    await work_order_manager.assign_order(order.id, technician_session.id)
    
    # Update status and verify
    await technician_session.start_work(order.id)
    updated_order = await work_order_manager.get_order(order.id)
    assert updated_order.status == WorkOrderStatus.IN_PROGRESS
    assert updated_order.technician_id == technician_session.id
```

### Async Testing
1. Use proper async fixtures
2. Handle timeouts appropriately
3. Test concurrent operations
4. Verify cleanup
5. Mock async dependencies

Example:
```python
@pytest.mark.asyncio
async def test_concurrent_messages(websocket_client, mock_websocket):
    """Test concurrent message handling."""
    messages = [{"type": "test", "id": i} for i in range(5)]
    
    async def send_messages():
        for msg in messages:
            await websocket_client.send_message(msg)
    
    async def receive_messages():
        received = []
        for _ in range(5):
            msg = await websocket_client.receive()
            received.append(msg)
        return received
    
    send_task = asyncio.create_task(send_messages())
    receive_task = asyncio.create_task(receive_messages())
    
    received_messages = await asyncio.gather(send_task, receive_task)
    assert len(received_messages[1]) == 5
```

### Performance Testing
1. Measure response times
2. Test under load
3. Monitor resource usage
4. Verify scalability
5. Test recovery

Example:
```python
@pytest.mark.performance
async def test_message_throughput(websocket_client):
    """Test message handling throughput."""
    start_time = time.time()
    message_count = 1000
    
    for i in range(message_count):
        await websocket_client.send_message({"type": "test", "id": i})
    
    end_time = time.time()
    duration = end_time - start_time
    
    assert duration < 5.0  # Should handle 1000 messages in under 5 seconds
```

## Coverage Requirements

### Minimum Coverage Levels
- Core Modules: 95%
- Utility Modules: 90%
- Integration Tests: 85%
- Overall Project: 90%

### Coverage Configuration
```ini
# .coveragerc
[run]
source = src
omit = 
    src/utils/logging.py
    tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: |
          python -m pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices
1. Write tests before code (TDD)
2. Keep tests focused and atomic
3. Use descriptive test names
4. Maintain test independence
5. Clean up test resources
6. Mock external dependencies
7. Test error conditions
8. Verify edge cases
9. Document test requirements
10. Regular test maintenance

## Test Execution

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run async tests
python -m pytest -v -m asyncio

# Run performance tests
python -m pytest -v -m performance

# Run with timeout protection
python -m pytest --timeout=30
```

### Test Markers
```python
# pytest.ini
[pytest]
markers =
    asyncio: mark test as async
    integration: mark as integration test
    performance: mark as performance test
    slow: mark test as slow running
```

## Status
- [x] Unit test framework
- [x] Integration test framework
- [x] Async test support
- [x] Coverage configuration
- [x] CI/CD integration
- [x] WebSocket testing
- [x] Performance testing
- [ ] Load testing (optional)
- [ ] Security testing (optional)
- [ ] UI testing (pending)

## Next Steps
1. Implement load testing
2. Add security test suite
3. Set up UI testing
4. Enhance performance tests
5. Add stress testing
6. Implement chaos testing
7. Add mutation testing
8. Enhance coverage reporting 